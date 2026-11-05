"""Verifier adapter for the shared task, artifact and result lifecycle."""
from acsl.infrastructure.settings import resolve_project_path
from engine.verification import verifast_runtime
from acsl.infrastructure.proof_limits import proof_slot


def execute_verifast(manager, task, payload):
    if task.mode != 'single' or payload.demo_case_id:
        raise ValueError('VeriFast 仅支持 C 文件直接验证。')
    upload = manager.store.read_upload(payload.file_id)
    if not upload:
        raise ValueError('缺少源码快照。')
    files = ([{'path': f['relative_path'], 'content': resolve_project_path(f['stored_path']).read_text()}
              for f in upload['manifest']] if upload.get('kind') == 'bundle' else
             [{'path': payload.entry_path, 'content': resolve_project_path(upload['stored_path']).read_text()}])
    source = next(f['content'] for f in files if f['path'] == payload.entry_path)
    manager._advance_phase(task, 'formal_verifying', 'running', 'VeriFast 正在验证当前文件规约')
    with proof_slot(payload.timeout_sec or 200) as remaining:
        check = verifast_runtime.verify(files, payload.entry_path, min(600, max(1, int(remaining))))
    status = ('Pass' if check['verified'] else 'Unavailable' if check['status'] == 'unavailable' else
              'Timeout' if check['status'] == 'timeout' else 'Invalid' if check['status'] in ('blocked','compile_error') else 'Fail')
    for phase in task.phases:
        phase.status = 'completed' if check['verified'] else 'failed'
        phase.detail = check['message']
    task.model_name = None
    manager.store.write_text_artifact(task.task_id, 'input', 'sources.json', __import__('json').dumps(files,ensure_ascii=False))
    manager.store.write_text_artifact(task.task_id, 'logs', 'verification.log', check.get('display_log',''))
    result = manager._build_result(task,status=status,summary=check['message'],source_code=source,result_code=source,
        command=check.get('command_text'),logs={'raw':check.get('display_log',''),'summary':[check['message']]},specifications={},
        engine_detail={'verification':check,'verifier':'VeriFast','verification_tool':'verifast','provider_calls':0},
        proof_stats={'scope':'compilation-unit','unit':'units','proved_goals':int(check['verified']),
                     'total_goals':1,'open_goals':int(not check['verified']),'pass_rate':float(check['verified'])})
    result['engine'] = 'VeriFast'
    return result
