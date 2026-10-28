"""NL2Verus integration using the platform's durable tasks and source snapshots."""
from __future__ import annotations

import json
import time
from collections import Counter
from math import ceil
from pathlib import PurePosixPath

from fastapi import APIRouter, HTTPException, Query
from engine.nl2verus import verifier
from engine.nl2verus.b3_runner import candidate_problem, verify_b3_candidate
from engine.nl2verus.dataset import load_tasks, summarize_task
from engine.nl2verus.platform_provider import provider_status
from engine.nl2verus.workflow import WorkflowRequest, prepare_workflow
from engine.nl2verus.workflow_runs import WorkflowRuns, WorkflowRunRequest, TERMINAL
from .config import resolve_project_path
from .storage import utcnow

router = APIRouter(prefix='/api/v1/rust', tags=['rust'])


@router.get('/status')
def rust_status():
    return {'verifier': verifier.verifier_info(), 'provider': provider_status()}


@router.get('/examples')
def examples(q: str = '', page: int = Query(1, ge=1)):
    rows = [r for r in load_tasks() if q.casefold() in (str(r.get('description', '')) + str(r.get('sample_id', ''))).casefold()]
    return {'items': [summarize_task(r) | {'code': r.get('verified_verus', '')} for r in rows[(page-1)*12:page*12]], 'total': len(rows)}


@router.get('/dataset/stats')
def dataset_stats():
    tasks = load_tasks()
    categories = Counter(str(task.get('category') or 'Uncategorized') for task in tasks)
    return {'total': len(tasks), 'categories': dict(sorted(categories.items())), 'source': 'NL2VBench'}


@router.get('/dataset/tasks')
def dataset_tasks(query: str = Query('', max_length=200), category: str = Query('all', max_length=40),
                  page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=50)):
    query, category = query.strip().casefold(), category.strip().casefold()
    items = []
    for task in load_tasks():
        summary = summarize_task(task)
        if category != 'all' and str(summary['category']).casefold() != category:
            continue
        haystack = '\n'.join(str(summary[key]) for key in ('sample_id', 'description', 'function_signature')).casefold()
        if query and query not in haystack:
            continue
        items.append(summary)
    start = (page - 1) * page_size
    return {'items': items[start:start + page_size], 'page': page, 'page_size': page_size,
            'total': len(items), 'pages': ceil(len(items) / page_size)}


@router.get('/dataset/tasks/{sample_id}')
def dataset_task(sample_id: str):
    for task in load_tasks():
        if task.get('sample_id') == sample_id:
            return summarize_task(task) | {'verified_verus': task.get('verified_verus') or ''}
    raise HTTPException(404, '数据集任务不存在。')


@router.post('/prepare')
def prepare(request: WorkflowRequest):
    try:
        return prepare_workflow(request)
    except (ValueError, OSError):
        raise HTTPException(422, '无法准备提示词，请检查任务与本地知识库。') from None


def validate_generation(payload):
    capabilities = provider_status()
    if not capabilities.get('generation_configured'):
        raise ValueError('Rust 生成模型尚未配置，请设置 NL2VERUS_CONFIG；仍可直接验证 Rust 文件。')
    if payload['model_id'] not in {m['id'] for m in capabilities.get('models', []) if m.get('configured')}:
        raise ValueError('请选择已配置的 Rust 生成模型。')
    if payload['rag_enabled'] and not capabilities.get('embedding_configured'):
        raise ValueError('向量检索尚未配置，请关闭 RAG 或配置 embedding。')


def execute_rust(manager, task, payload):
    store = manager.store
    upload = store.read_upload(payload.file_id)
    if not upload or upload.get('kind') != 'bundle':
        raise ValueError('Rust 验证需要项目源码快照。')
    files = [{'path': row['relative_path'], 'content': resolve_project_path(row['stored_path']).read_text(encoding='utf-8')}
             for row in upload['manifest']]
    entry = next(f for f in files if f['path'] == payload.entry_path)
    source = entry['content']
    task.title = f"Rust · {payload.entry_path}"
    task.input_file = upload['stored_path']
    task.metadata.update(language='Rust', entry_path=payload.entry_path,
                         input_manifest=upload['manifest'], timeout_sec=payload.timeout_sec)
    store.write_task(task)
    # Keep the exact input as browsable artifacts; original upload remains immutable.
    store.write_text_artifact(task.task_id, 'input', 'sources.json', json.dumps(files, ensure_ascii=False, indent=2))
    result_code, attempts, workflow = source, [], None
    try:
        if task.mode == 'rust-generate':
            manager._advance_phase(task, 'generation', 'running', '生成候选并根据验证诊断修复')
            runner = WorkflowRuns()
            try:
                workflow = runner.submit(WorkflowRunRequest(**payload.rust_workflow))
                while True:
                    workflow = runner.get(workflow['id'])
                    # Persist each revision so a restart retains all completed rounds.
                    store.write_text_artifact(task.task_id, 'workflow', 'rounds.json', json.dumps(workflow, ensure_ascii=False, indent=2))
                    task.metadata['rust_workflow'] = workflow
                    task.message = workflow['message']
                    task.updated_at = utcnow()
                    store.write_task(task)
                    if workflow['status'] in TERMINAL:
                        break
                    time.sleep(0.3)
            finally:
                runner.close()
            attempts = workflow['attempts']
            result_code = next((a['code'] for a in reversed(attempts) if a.get('code')), '')
            check = (attempts[-1].get('verification') if attempts else None) or {
                'status': workflow.get('outcome') or 'tool_error', 'message': workflow['message'], 'verified': False}
            manager._advance_phase(task, 'generation', 'completed' if attempts else 'failed', workflow['message'])
        else:
            manager._advance_phase(task, 'verus', 'running', '使用项目源码快照执行 Verus')
            # Check every dependency too, before passing the selected crate root to Verus.
            problem = next((candidate_problem(f['content']) for f in files if (f['content'].strip() or f['path'] == entry['path']) and candidate_problem(f['content'])), None)
            if problem:
                check = {'status': 'blocked', 'verified': False, 'message': '源码含证明绕过标记、空文件或超出大小限制：' + problem}
            else:
                check = verify_b3_candidate(source, verify=lambda code: verifier.verify_code(
                    code, payload.timeout_sec or 120, files=files, entry_path=entry['path']))
    except (verifier.VerifierUnavailableError, FileNotFoundError, OSError) as error:
        check = {'status': 'unavailable', 'verified': False, 'message': str(error)}
    except ValueError as error:
        check = {'status': 'blocked', 'verified': False, 'message': str(error)}
    except Exception:
        check = {'status': 'tool_error', 'verified': False, 'message': 'Rust 工作流无法完成，请检查验证器与模型配置。'}
    status = {'verified': 'Pass', 'failed': 'Fail', 'verification_failed': 'Fail',
              'compile_error': 'Invalid', 'blocked': 'Invalid', 'no_checks': 'Invalid',
              'timeout': 'Timeout', 'output_limit': 'Invalid', 'provider_error': 'Unavailable', 'unavailable': 'Unavailable', 'tool_error': 'Unavailable'}.get(check['status'], 'Fail')
    raw = '\n'.join(str(check.get(k) or '') for k in ('stdout', 'stderr', 'message'))
    proved, errors = int(check.get('verified_count') or 0), int(check.get('error_count') or 0)
    total = proved + errors
    manager._advance_phase(task, 'verus', 'completed' if status == 'Pass' else 'failed', check['message'])
    for phase in task.phases:
        if phase.status in ('pending', 'running'):
            phase.status = 'failed'
    store.write_text_artifact(task.task_id, 'output', PurePosixPath(entry['path']).name, result_code)
    store.write_text_artifact(task.task_id, 'logs', 'verus.log', raw)
    for attempt in attempts:
        store.write_text_artifact(task.task_id, 'rounds', f"round-{attempt['round']}.rs", attempt.get('code', ''))
    result = manager._build_result(task, status=status, summary=check['message'], source_code=source,
        result_code=result_code, command=None, logs={'raw': raw, 'summary': [check['message']]}, specifications={},
        engine_detail={'language': 'Rust', 'verifier': 'Verus', 'version': verifier.VERUS_VERSION,
                       'verification': check, 'workflow': workflow, 'attempts': attempts},
        proof_stats={'scope': 'proof-goals', 'unit': 'goals', 'proved_goals': proved,
                     'total_goals': total, 'open_goals': errors, 'pass_rate': proved/total if total else 0},
        failure_analysis={'category': 'none' if status == 'Pass' else check['status'],
                          'label': check['message'], 'summary': check['message'], 'evidence': [raw] if status != 'Pass' else []},
        highlights=['Rust / Verus', '真实验证结果', '完整输入快照'])

    result["result_code"] = result_code  # Rust output must never pass through ACSL cleanup.
    return result
