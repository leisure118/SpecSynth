"""Merge annotation-only patches against an immutable original source snapshot."""
import json,re
from engine.verification.spec_edit import source_tokens


def parse_patch_json(text):
    text=text.strip()
    if text.startswith('```'):text=re.sub(r'^```(?:json)?\s*\n?|\n?```\s*$','',text)
    data=json.loads(text)
    if not isinstance(data,dict) or set(data)!={'patches'} or not isinstance(data['patches'],list):raise ValueError('只接受 patches 规约补丁，不能返回完整源码。')
    return data



def normalize_patch_delimiters(data,verification_tool='framac'):
    """Normalize only an explicit @@ annotation fence, never generate or alter clauses."""
    if not isinstance(data,dict) or not isinstance(data.get('patches'),list):return data,[]
    normalized=[];notes=[]
    for index,patch in enumerate(data['patches']):
        if not isinstance(patch,dict):normalized.append(patch);continue
        item=dict(patch);annotation=item.get('annotation')
        if isinstance(annotation,str):
            match=re.fullmatch(r'\s*@@\s+([\s\S]*?)\s*@@\s*',annotation)
            if match:
                body=match[1].strip()
                if ('@@' not in body and not any(marker in body for marker in ('/*','*/','//'))
                    and re.match(r'(?:loop\s+)?(?:requires|ensures|invariant|assigns|variant|assert|decreases|terminates)\b',body)
                    and body.endswith(';') and not re.search(r'\b(?:return|while|for|switch|goto|break|continue|typedef|struct|union|enum)\b',body)):
                    item['annotation']='\n'.join('//@ '+line for line in body.splitlines()) if verification_tool=='verifast' else '/*@\n'+body+'\n*/'
                    notes.append({'patch_index':index,'format':'@@ -> complete '+verification_tool+' comment','clauses_changed':False})
        normalized.append(item)
    return {**data,'patches':normalized},notes

def loop_inventory(files):
    """Conservative loop locations, excluding comments, strings and preprocessor lines."""
    rows=[]
    for f in files:
        clean=re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*|^[ \t]*\#[^\n]*',lambda m:re.sub(r'[^\n]',' ',m[0]),f['content'],flags=re.S|re.M)
        for m in re.finditer(r'\b(?:for|while)\s*\(|\bdo\b',clean):
            rows.append({'path':f['path'],'line':clean.count('\n',0,m.start())+1,'offset':m.start(),'kind':re.match(r'\w+',m[0])[0]})
    return rows


def candidate_quality(files,data,verification_tool="framac"):
    if verification_tool=="verifast":
        merged=merge_spec_patches(files,data,verification_tool=verification_tool)
        return {"verification_tool":"verifast","patch_count":len(data["patches"]),"annotation_nonempty":bool(data["patches"]),"coverage_is_proof":False,"static_syntax_checks_passed":True,"line_numbering":"original"}
    merged=merge_spec_patches(files,data)
    inventory=loop_inventory(merged);covered=[]
    for loop in inventory:
        code=next(f['content'] for f in merged if f['path']==loop['path'])
        before=code[:loop['offset']]
        # Adjacent ACSL blocks only; ordinary declarations must not count as coverage.
        end=len(before);adjacent=[]
        for comment in reversed(list(re.finditer(r'/\*.*?\*/|//[^\n]*',before,re.S))):
            if before[comment.end():end].strip():break
            adjacent.append(comment[0]);end=comment.start()
        if any(re.search(r'\bloop\s+invariant\b',c) for c in adjacent):covered.append(loop)
    original_inventory=loop_inventory(files)
    uncovered=[{k:original_inventory[i][k] for k in ('path','line','kind')} for i,r in enumerate(inventory) if r not in covered]
    return {'patch_count':len(data['patches']),'annotation_nonempty':bool(data['patches']),
            'loop_count_estimate':len(inventory),'covered_loop_count_estimate':len(covered),
            'uncovered_loops_estimate':uncovered,'line_numbering':'original',
            'coverage_is_proof':False,'static_syntax_checks_passed':True}


def check_annotation_syntax(annotation,following=''):
    """Reject two known transportable ACSL mistakes, without changing expressions."""
    for clause in re.finditer(r'\b(?:ensures|invariant|assert)\s+([^;]+);',annotation):
        groups=[];serial=0;operators={}
        for token in re.finditer(r'==|!=|<=|>=|&&|\|\||[()\[\]<>&|^]',clause[1]):
            value=token[0]
            if value in ('(', '['):serial+=1;groups.append(serial)
            elif value in (')',']'):
                if groups:groups.pop()
            elif value in ('==','!=','<=','>=','<','>','&','|','^'):
                operators.setdefault(tuple(groups),set()).add(value)
        if any(ops.intersection({'==','!=','<=','>=','<','>'}) and ops.intersection({'&','|','^'}) for ops in operators.values()):
            raise ValueError('ACSL 比较与位运算混用了优先级：请给完整位运算表达式加外层括号，例如 ensures \\result == (a | b | c);，不要只给各操作数加括号。')
    comments=list(re.finditer(r'/\*@.*?\*/|//@[^\n]*',annotation,re.S))
    for comment in comments:
        body=comment[0][3:-2] if comment[0].startswith('/*@') else comment[0][3:]
        body=body.strip().rstrip('@').strip()
        if body and not body.endswith(';'):
            raise ValueError('ACSL 规约子句缺少结尾分号；请补齐分号，不能提交不完整断言。')
        if re.search(r'\bloop\s+(?:invariant|variant|assigns)\b',body) and re.search(r'\bassigns\b',re.sub(r'\bloop\s+assigns\b','',body)):
            raise ValueError('循环规约块必须使用 loop assigns，不能混入函数级 assigns。')
        if not re.search(r'\bloop\s+(?:invariant|assigns|variant|allocates|frees)\b',comment[0]):continue
        tail=annotation[comment.end():]+following
        tail=re.sub(r'^(?:\s+|/\*(?!@).*?\*/|//(?!@)[^\n]*(?:\n|$))*','',tail,flags=re.S)
        if re.match(r'(?:/\*@|//@)\s*assert\b',tail):
            raise ValueError('循环规约与循环之间不能插入 assert。请将 assert 放在完整 loop 规约块之前，让 loop 规约紧邻 for/while/do；保留断言和原始源码。')
        # A following loop-contract block can legally continue this loop annotation.
        if not re.match(r'(?:for|while|do)\b|(?:/\*@|//@)\s*(?:@\s*)?loop\b',tail):
            raise ValueError('loop 规约必须直接位于 for/while/do 之前，不能插入到 int 等声明之前；请使用实际循环的原始行号。')


def merge_spec_patches(files,data,verification_tool="framac"):
    if verification_tool not in ("framac","verifast"):raise ValueError("Unknown verification tool")
    dialect="VeriFast" if verification_tool=="verifast" else "ACSL"
    if not isinstance(data,dict) or set(data)!={'patches'} or not isinstance(data['patches'],list) or len(data['patches'])>128:raise ValueError('规约补丁格式不正确，最多128个插入位置。')
    data,_=normalize_patch_delimiters(data,verification_tool)
    originals={f['path']:f['content'] for f in files};edits={p:[] for p in originals};seen=set();size=0
    for patch in data['patches']:
        if not isinstance(patch,dict) or set(patch)-({'path','before_line','before_column','annotation','anchor'} if verification_tool=='verifast' else {'path','before_line','annotation','anchor'}):raise ValueError('规约补丁字段不正确。')
        path=patch.get('path');line=patch.get('before_line');annotation=patch.get('annotation')
        if not isinstance(path,str) or path not in originals:raise ValueError('补丁文件不属于原始源码快照。')
        lines=originals[path].splitlines(keepends=True)
        if type(line)!=int or not 1<=line<=len(lines)+1:raise ValueError('规约插入行号超出原始文件范围。')
        if line>1 and lines[line-2].rstrip('\r\n').endswith('\\'):raise ValueError('不能在预处理续行或转义换行中插入规约。')
        column=patch.get('before_column',1)
        text=lines[line-1].rstrip('\r\n') if line<=len(lines) else ''
        if column!=1 and text.lstrip().startswith('#'):raise ValueError('不能在预处理指令内部插入规约。')
        if type(column)!=int or not 1<=column<=len(text)+1:raise ValueError('规约插入列号超出原始行范围。')
        if (path,line,column) in seen:raise ValueError('同一行只允许一个规约块，请合并相邻 loop 子句。')
        seen.add((path,line,column))
        if 'anchor' in patch and (line>len(lines) or patch['anchor']!=lines[line-1].rstrip('\r\n')):raise ValueError('插入位置的源码锚点不匹配，请使用原始行号。')
        if not isinstance(annotation,str) or not annotation.strip() or source_tokens(annotation):raise ValueError(f'补丁只能包含完整 {dialect} 注释（//@ 或 /*@ ... */），不能包含 C 代码、普通注释、@@ 伪分隔符或不完整规约。')
        if re.search(r'\b(?:admit|assume|axiom|axiomatic|lemma)\b',annotation):raise ValueError('补丁不得引入 admit、假设或未验证逻辑声明。')
        if re.search(r'\\u00(?:0[aA]|5[cC])',annotation):raise ValueError('规约包含未解码的 Unicode 转义，请使用正常 JSON 换行和反斜杠转义。')
        # Never insert into a multiline comment/string: it could change executable code.
        boundary=sum(len(s) for s in lines[:line-1])+column-1
        token=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*')
        if any(m.start()<boundary<m.end() for m in token.finditer(originals[path])):raise ValueError('不能在已有注释或字符串内部插入规约。')
        try:
            if verification_tool=='framac':check_annotation_syntax(annotation,originals[path][boundary:])
            elif re.search(r'\bloop\s+(?:invariant|assigns|variant)\b|\b(?:assigns|variant)\b|\\result\b',annotation):raise ValueError('VeriFast 不能使用 ACSL loop invariant/assigns/variant 或 \\result；请使用 invariant 和 result。')
        except ValueError as exc:raise ValueError(f'{path}: original line {line}, column {column}: {exc}') from None
        size+=len(annotation.encode())
        if size>131072:raise ValueError('规约补丁输出超过128KiB。')
        edits[path].append((boundary,('\n' if column>1 or (boundary>0 and boundary==len(originals[path]) and not originals[path].endswith(('\n','\r'))) else '')+annotation.rstrip()+'\n'))
    result=[]
    for f in files:
        code=f['content']
        for offset,annotation in sorted(edits[f['path']],reverse=True):code=code[:offset]+annotation+code[offset:]
        if source_tokens(code)!=source_tokens(f['content']):raise ValueError('规约插入改变了原始源码，已拒绝。')
        result.append({'path':f['path'],'content':code})
    return result


def patch_contract(files,verification_tool='framac'):
    numbered=[{'path':f['path'],'lines':['%d: %s'%(i,line) for i,line in enumerate(f['content'].splitlines(),1)]} for f in files]
    if verification_tool=='verifast':
        return ('\nVERIFAST ANNOTATION PATCH PROTOCOL: Return ONLY JSON {"patches":[{"path":"original file path","before_line":2,"before_column":1,"annotation":"//@ requires 0 <= limit &*& limit <= 100000;\\n//@ ensures result == limit;"}]}. '
            'All lines and columns are 1-based positions in immutable ORIGINAL source. before_column defaults to 1. Insert contracts after the function signature BEFORE its opening brace. '
            'VeriFast loop invariant belongs AFTER the while/for header and BEFORE its opening brace; if header and brace share a line, set before_column to the exact column of that brace. '
            'Use a separate //@ line or separate /*@ ... @*/ block for EACH requires, ensures or invariant clause; never combine requires and ensures in a single block. Use complete //@ comments or /*@ ... @*/ blocks only. Never use @@ pseudo-delimiters, ordinary comments, C code or complete source. '
            'Use &*& and result; never ACSL loop invariant, assigns, variant or \\result. Retain original assertions and all useful previous patches. '
            'Placement example: for original lines 1: int f(int n), 2: {, insert requires/ensures at line 2 column 1, NOT before line 1. '
            'For original line 4: while (i < n) {, insert invariant at line 4 column 15 (the opening brace), NOT before while. '
            'An ordinary /* ... */ is not an annotation. A rejected patch must be repaired, never acknowledged as successful. '
            'No assume/admit, false preconditions or unproved lemmas. A patch receipt is NOT proof; only independent VeriFast decides pass. '
            '\nOriginal numbered source:\n'+json.dumps(numbered,ensure_ascii=False))
    return ('\nANNOTATION PATCH PROTOCOL (overrides all full-source output examples): Return ONLY JSON {"patches":[{"path":"original file path","before_line":8,"annotation":"/*@ loop invariant ...; loop assigns ...; loop variant ...; */"}]}. '
            'Line numbers always refer to the immutable ORIGINAL source below, never the annotated candidate. Each response replaces the previous generated patch set: retain useful earlier annotations in the returned patches. '
            'Return only complete ACSL blocks and insertion locations, never any C statements, complete source, escaped pseudo-source, admit, assume, axiom or unproved lemmas. One block per location; preserve every original assertion and contract. '
            'Do not modify original annotations. A statement assert must precede the loop contract, never occur between a loop contract and its loop. Parenthesize the ENTIRE bitwise expression in comparison predicates: ensures \\result == (a | b | c);. Use a loop annotation block immediately before its loop. For a bitwise fold, prove range/induction and the required permutation-invariance properties rather than assuming them. For array copies, cover both written index ranges and their frame conditions. '
            '\nOriginal numbered source:\n'+json.dumps(numbered,ensure_ascii=False))


def patch_line_map(files,data,verification_tool="framac"):
    data,_=normalize_patch_delimiters(data,verification_tool)
    if verification_tool=="verifast":
        rows=[]
        for f in files:
            ordered=sorted([p for p in data["patches"] if p["path"]==f["path"]],key=lambda p:(p["before_line"],p.get("before_column",1)))
            added=0
            for patch in ordered:
                count=patch["annotation"].rstrip().count("\n")+1
                column=patch.get("before_column",1);prefix=int(column>1)
                for i in range(count):rows.append({"path":f["path"],"generated_line":patch["before_line"]+added+prefix+i,"original_line":patch["before_line"],"original_column":column,"patch_index":data["patches"].index(patch)})
                added+=count+prefix
        return rows
    """Relate verifier lines in merged output to immutable lines or generated patches."""
    rows=[]
    for file in files:
        inserts={p['before_line']:(i,p['annotation'].rstrip()+'\n') for i,p in enumerate(data['patches']) if p['path']==file['path']}
        generated=1;lines=file['content'].splitlines(keepends=True)
        for original in range(1,len(lines)+2):
            if original in inserts:
                index,text=inserts[original]
                for _ in text.splitlines():
                    rows.append({'path':file['path'],'generated_line':generated,'original_line':original,'patch_index':index});generated+=1
            if original<=len(lines):
                rows.append({'path':file['path'],'generated_line':generated,'original_line':original});generated+=1
    return rows


def recover_patch_candidate(workspace):
    """Recover rejected annotations as repair context, never as an accepted receipt."""
    from pathlib import Path
    for name in ('candidate-patches.json','.platform-rejected-patches.json','.platform-worker-final.txt'):
        receipt=Path(workspace)/name
        try:
            if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>262144:continue
            data=parse_patch_json(receipt.read_text())
            patches=data['patches']
            if 0<len(patches)<=128 and all(isinstance(p,dict) and isinstance(p.get('path'),str)
                and type(p.get('before_line')) is int and isinstance(p.get('annotation'),str)
                and re.search(r'\b(?:requires|ensures|invariant|assert|assigns|variant|admit|assume)\b',p['annotation']) for p in patches):return data
        except (OSError,ValueError):continue
    return {'patches':[]}


def repairable_patch_receipt(directory):
    """A concrete rejected annotation set may enter bounded same-session repair."""
    from pathlib import Path
    return bool(recover_patch_candidate(Path(directory)/'workspace')['patches'])
