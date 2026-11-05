"""Keep full verifier logs on disk; send bounded, relevant repair evidence."""
import json,re

def compact_feedback(check,limit=5000):
    if check.get("tool")=="verifast":
        return json.dumps({k:check.get(k) for k in ("tool","status","verified","message","diagnostics")},ensure_ascii=False)[:limit]
    summary={k:check[k] for k in ('status','message','verified_count','error_count') if k in check}
    diagnostics=[{k:d[k] for k in ('path','line','kind','message') if k in d} for d in check.get('diagnostics',[])[:6]]
    for d in diagnostics:
        if 'message' in d:d['message']=d['message'][:220]
    text=json.dumps(summary,ensure_ascii=False)+'\n'+json.dumps(diagnostics,ensure_ascii=False)
    logs=str(check.get('stdout',''))+'\n'+str(check.get('stderr',''))
    if re.search(r'invalid operands to binary [|&^]',logs):
        text+='\nSyntax repair: comparison binds before bitwise operators in ACSL. Parenthesize the ENTIRE bitwise side, e.g. ensures \\result == (a | b | c);. Parenthesizing only each operand is insufficient. This fixes parsing only, not the proof.'
    if re.search(r'syntax error',logs,re.I):
        text+='\nSyntax repair: loop annotations must be directly attached to for/while/do. Put any separate assert BEFORE the full loop contract, not between that contract and its loop. Preserve the assertions and original source.'
    logs=str(check.get('stdout',''))+'\n'+str(check.get('stderr',''))
    # Keep unproved goal formulas and parser diagnostics; discard proved goals and repeated warnings.
    blocks=re.split(r'(?=Goal )',logs)
    relevant=[b for b in blocks if re.search(r'annot-error|unbound logic|undefined in this context|syntax error|parse error',b,re.I) or ('Goal ' in b and 'returns Valid' not in b and re.search(r'Timeout|Unknown|Failed|Invalid',b))]
    seen=set()
    for block in relevant:
        if 'Prove:' in block:
            proof=block[block.rfind('Prove:'):]
            block=block[:450]+'\n...\n'+proof[-1000:]
        else:block=block[:1500]
        if block not in seen:seen.add(block);text+='\n'+block
    if not relevant and not diagnostics:text+='\n'+logs[-1800:]
    if re.search(r'and_fold|land\(|bitwise',logs,re.I):
        text+='\nRepair hint: separate bitwise range/width preservation from fold induction and permutation invariance; preserve signedness and establish each required intermediate fact with checked ACSL assertions. Do not add axioms, admit or unproved lemmas.'
    if re.search(r'acopy|separated',logs) or ('shift_sint32' in logs and 'Preservation of Invariant' in logs):
        text+='\nRepair hint: cover both copied index ranges and precise loop frame conditions; establish memory separation from actual source declarations, never by admit.'
    return text[:limit]
