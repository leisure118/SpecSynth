"""Conservative source routing before launching any generation runtime."""
import re
from pathlib import PurePosixPath


def classify_sources(files,entry,mode):
    source=next((f['content'] for f in files if f['path']==entry),None)
    if source is None:raise ValueError('入口文件不存在。')
    suffix=PurePosixPath(entry).suffix.lower()
    if suffix not in ('.c','.rs'):raise ValueError('请选择 C 或 Rust 源文件作为验证入口。')
    language='Rust' if suffix=='.rs' else 'C'
    if (language=='Rust')!=mode.startswith('rust-'):raise ValueError('入口文件语言与验证工作流不一致，请重新选择验证模式。')
    allowed=('.rs',) if language=='Rust' else ('.c','.h')
    if any(PurePosixPath(f['path']).suffix.lower() not in allowed for f in files):raise ValueError('源码快照包含不兼容语言文件，请拆分 C 与 Rust 项目。')
    annotations=re.findall(r'/\*@([\s\S]*?)\*/|//@([^\n]*)',source) if language=='C' else []
    annotation_text='\n'.join(a or b for a,b in annotations)
    has_contract=bool(re.search(r'\b(requires|ensures|assigns|loop\s+(?:invariant|assigns|variant))\b',annotation_text)) if language=='C' else bool(re.search(r'\b(?:requires|ensures|invariant)\b',source))
    # Strip comments and literals before counting definitions; a routing hint, not a C parser.
    code=re.sub(r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',' ',source)
    functions=len(re.findall(r'\b(?!if\b|for\b|while\b|switch\b)([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{',code)) if language=='C' else len(re.findall(r'\bfn\s+\w+',code))
    multifile=sum(f['path'].endswith('.c' if language=='C' else '.rs') for f in files)>1
    if language=='Rust':workflow='verus-repair' if has_contract else 'verus-generate'
    elif mode=='termination':workflow='acsl-termination'
    elif has_contract:workflow='acsl-repair'
    elif multifile or functions>1 or mode=='inter-modular':workflow='acsl-bottom-up'
    else:workflow='acsl-single'
    labels={'acsl-single':'C 单函数规约生成','acsl-bottom-up':'C 多函数分层验证','acsl-repair':'已有 ACSL 规约检查与修复','acsl-termination':'C 终止性验证','verus-repair':'已有 Verus 规约检查与修复','verus-generate':'Rust / Verus 生成与验证'}
    return {'language':language,'entry_path':entry,'source_kind':'annotated' if has_contract else 'source-with-assertions' if annotations else 'original','workflow':workflow,'label':labels[workflow],'function_count_hint':functions,'multi_file':multifile}


def routing_instructions(route):
    common='\nPlatform source classification: '+route['workflow']+'. '
    if route['workflow'] in ('acsl-repair','verus-repair'):
        return common+'This source already contains proof annotations. Inspect and verify the existing annotations first; preserve them and repair only missing or failing clauses. Do not regenerate specifications from scratch. Preserve every original assertion and requirement. Use dependency slicing only if necessary for multiple functions.'
    if route['workflow']=='acsl-single':
        return common+'Use the single-function workflow: read this source, add only required ACSL annotations, and verify. Do not perform dependency splitting or contract database initialization for this single function.'
    if route['workflow']=='acsl-bottom-up':return common+'Use spec-split to inspect dependencies, then orchestrate bottom-up per-function specification generation and independent proof checking.'
    if route['workflow']=='acsl-termination':return common+'Analyze loop termination; preserve original requirements, add or repair invariants and decreasing variants, and check termination obligations.'
    return common+'Use the Rust/Verus workflow and Verus verifier; do not call C/Frama-C tools.'
