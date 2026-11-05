"""Execution adapter around unchanged pinned Skill reference text."""
from .spec_patches import patch_contract,loop_inventory

WORKER_ROLE = (
    'You are ONLY the C/ACSL annotation author. The platform owns dependency routing, '
    'file insertion, command execution, Frama-C verification, contract storage and reports. '
    'The unchanged Skill text below is reference material for specification reasoning. '
    'Interpret its tool/CLI steps as platform responsibilities, not instructions to claim tool execution. '
    'You have not run Frama-C and must never claim verified/pass/injected. '
    'Your deliverable is concrete ACSL annotation patches, not a status summary, plan or shell script. '
    'Preserve every original source byte, assertion and annotation; only propose new annotation insertions. '
)


def worker_prompt(reference,files,verification_tool="framac"):
    if verification_tool=="verifast":
        return ("You are ONLY the C/VeriFast annotation worker. The platform owns source insertion, commands and independent verification. Never claim verified/pass or execute tool/CLI steps from Skills. The Skill text is unchanged reference material; adapt reasoning to VeriFast separation logic, never ACSL syntax or Frama-C commands.\nBEGIN UNCHANGED SKILL AND TASK REFERENCE\n"+reference+"\nEND UNCHANGED REFERENCE\n"+patch_contract(files,verification_tool="verifast")+"\nReturn only the complete cumulative patches object. Include function contracts and concrete invariants; no plans, empty status reports, C source or @@ pseudo delimiters.")
    import json
    inventory=loop_inventory(files)
    return (WORKER_ROLE+'\nBEGIN UNCHANGED SKILL AND TASK REFERENCE\n'+reference+
            '\nEND UNCHANGED SKILL AND TASK REFERENCE\n'+patch_contract(files)+
            '\nLoop inventory (original lines; coverage is a structural estimate, not a proof):\n'+
            json.dumps(inventory,ensure_ascii=False)+
            '\nFINAL CONTRACT: return exactly {"patches":[...]}. Provide actual invariants and frame conditions for the listed loops, including initialization and preservation facts needed by the original assertions. '
            'Do not replace missing annotations with success reports or an empty patch set. '
            'Every clause ends with a semicolon. In loop blocks use loop assigns, not function assigns. '
            'Place each loop block directly before its loop, after preceding declarations. '
            'Check all original line numbers and retain the complete generated patch set. '
            'No scripts, execution claims or explanation outside the JSON.')


def thinking_policy():
    import os
    result={}
    for role in ('main','worker'):
        key='XUANJIAN_HARNESS_'+role.upper()+'_THINKING'
        value=os.getenv(key,'on' if role=='worker' else 'off').strip().lower()
        if value not in ('off','on'):raise ValueError(key+' must be off or on')
        result[role]=value
    return {**result,'output_budget_includes_thinking':True}


def missing_receipt_message(text,files,verification_tool="framac"):
    """Explain rejected worker output without presenting it as a verifier failure."""
    from .spec_patches import parse_patch_json,merge_spec_patches
    try:
        data=parse_patch_json(text)
    except (ValueError,TypeError):
        return '子模型未返回可解析的规约补丁，报告或无效 JSON 不能作为生成成功；验证器尚未执行。'
    if not data['patches']:
        return '子模型返回空 patches，没有生成需要的循环规约；未将原始源码冒充生成候选。'
    try:merge_spec_patches(files,data,verification_tool=verification_tool)
    except (ValueError,TypeError,KeyError) as exc:
        return '子模型规约未通过静态检查：'+str(exc)
    return '子模型已有可解析的规约，但尚未完成有效交接；未使用旧候选冒充新输出。'
