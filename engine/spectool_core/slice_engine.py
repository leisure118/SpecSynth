#!/usr/bin/env python3
"""
slice.py — 从多文件 C 项目中切出单函数的最小可验证文件。

用法:
    python3 scripts/slice.py --project-dir x509-parser-bench \
                             --func parse_null \
                             --out slices/parse_null.c \
                             --mode inline

策略:
  1. 扫描所有 .c/.h 文件，建立函数索引（名称 → 文件:起止行）
  2. 对目标函数，递归追踪其调用的其他项目内函数
  3. 精确收集所有涉及的类型定义（typedef/enum/struct）、宏和全局变量
  4. 按依赖序拼装为一个自包含的 .c 文件

两种模式:
  --mode inline : 被调函数连实现体一起放入（适合叶子调用链）
  --mode stub   : 被调函数只放声明（后续可手动/自动加契约）
"""

import argparse
import os
import re
import sys
from collections import defaultdict, OrderedDict


# ─── C 源码解析工具 ───────────────────────────────────────────────

def find_function_boundaries(content, filename):
    """
    找出文件中所有顶层函数定义的 {name, start, end, signature_start} 行号。
    使用花括号匹配来确定函数体范围。
    """
    lines = content.split('\n')
    functions = []

    i = 0
    while i < len(lines):
        line = lines[i]

        stripped = line.strip()
        if (stripped.startswith('#') or stripped.startswith('//') or
            stripped.startswith('/*') or stripped == '' or
            stripped.startswith('*')):
            i += 1
            continue

        func_match = re.match(
            r'^(?:static\s+)?(?:const\s+)?(?:(?:int|void|u8|u16|u32|u64|const\s+\w+\s*\*?)\s+\*?\s*)'
            r'(\w+)\s*\(',
            stripped
        )
        if not func_match:
            func_match = re.match(
                r'^(?:static\s+)?(?:inline\s+)?(?:const\s+)?'
                r'(?:(?:unsigned\s+|signed\s+)?(?:int|void|char|short|long|float|double|'
                r'u8|u16|u32|u64|_Bool|size_t|off_t|ssize_t|'
                r'(?:const\s+)?(?:struct\s+)?\w+)(?:\s+const)?[\s*]+)'
                r'(\w+)\s*\(',
                stripped
            )

        if func_match:
            func_name = func_match.group(1)
            sig_start = i

            j = i
            paren_depth = 0
            found_open_brace = False
            is_forward_decl = False
            while j < len(lines):
                for ch in lines[j]:
                    if ch == '(':
                        paren_depth += 1
                    elif ch == ')':
                        paren_depth -= 1
                    elif paren_depth == 0 and ch == ';':
                        is_forward_decl = True
                        break
                    elif ch == '{' and paren_depth == 0:
                        found_open_brace = True
                        break
                if found_open_brace or is_forward_decl:
                    break
                j += 1
                if j - i > 10:
                    break

            if is_forward_decl:
                i += 1
                continue

            if found_open_brace:
                brace_depth = 0
                k = j
                body_started = False
                in_block_comment = False
                found_end = False
                while k < len(lines):
                    line_k = lines[k]
                    ci = 0
                    while ci < len(line_k):
                        if in_block_comment:
                            if line_k[ci:ci+2] == '*/':
                                in_block_comment = False
                                ci += 2
                            else:
                                ci += 1
                            continue
                        if line_k[ci:ci+2] == '/*':
                            in_block_comment = True
                            ci += 2
                            continue
                        if line_k[ci:ci+2] == '//':
                            break
                        if line_k[ci] == '"':
                            ci += 1
                            while ci < len(line_k) and line_k[ci] != '"':
                                if line_k[ci] == '\\':
                                    ci += 1
                                ci += 1
                            ci += 1
                            continue
                        if line_k[ci] == "'":
                            ci += 1
                            while ci < len(line_k) and line_k[ci] != "'":
                                if line_k[ci] == '\\':
                                    ci += 1
                                ci += 1
                            ci += 1
                            continue
                        if line_k[ci] == '{':
                            brace_depth += 1
                            body_started = True
                        elif line_k[ci] == '}':
                            brace_depth -= 1
                            if body_started and brace_depth == 0:
                                functions.append({
                                    'name': func_name,
                                    'file': filename,
                                    'sig_start': sig_start,
                                    'body_start': j,
                                    'end': k,
                                })
                                i = k + 1
                                found_end = True
                                break
                        ci += 1
                    if found_end:
                        break
                    k += 1
                if not found_end:
                    i += 1
            else:
                i += 1
        else:
            i += 1

    return functions


def extract_function_calls(content, start_line, end_line):
    """提取函数体内调用的其他函数名。"""
    lines = content.split('\n')[start_line:end_line + 1]
    body = '\n'.join(lines)

    body = re.sub(r'"[^"\n]*"', '""', body)
    body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)
    body = re.sub(r'//[^\n]*', '', body)

    keywords = {'if', 'else', 'for', 'while', 'do', 'switch', 'case',
                'return', 'sizeof', 'goto', 'break', 'continue', 'typedef'}
    calls = set(re.findall(r'\b([a-zA-Z_]\w*)\s*\(', body))
    calls -= keywords
    return calls


def extract_type_references(content, start_line, end_line, all_type_names):
    """提取函数中引用的自定义类型名。"""
    lines = content.split('\n')[start_line:end_line + 1]
    body = '\n'.join(lines)

    types = set()
    for tname in all_type_names:
        if re.search(r'\b' + re.escape(tname) + r'\b', body):
            types.add(tname)
    return types


def find_macro_references(text, all_macros):
    """提取文本中引用的宏名。"""
    used = set()
    for macro in all_macros:
        if re.search(r'\b' + re.escape(macro) + r'\b', text):
            used.add(macro)
    return used


def collect_inter_function_content(all_contents, all_functions_by_file):
    """收集 .c 文件中函数之间的全局变量和宏定义。

    扫描每个 .c 文件的"间隙区域"：
      - 第一个函数之前的 preamble
      - 每两个相邻函数之间的区域
      - 最后一个函数之后的区域

    返回:
        globals_map: dict  name -> {'text': definition_text, 'file': filename}
        inter_macros: dict  name -> {'text': macro_text, 'file': filename}
    """
    globals_map = {}
    inter_macros = {}

    for filename, content in all_contents.items():
        if not filename.endswith('.c'):
            continue
        lines = content.split('\n')

        funcs_in_file = sorted(
            all_functions_by_file.get(filename, []),
            key=lambda f: f['sig_start']
        )

        # Build list of gap regions: (start_line, end_line) exclusive of functions
        gaps = []
        if funcs_in_file:
            # Before first function
            if funcs_in_file[0]['sig_start'] > 0:
                gaps.append((0, funcs_in_file[0]['sig_start'] - 1))
            # Between functions
            for idx in range(len(funcs_in_file) - 1):
                gap_start = funcs_in_file[idx]['end'] + 1
                gap_end = funcs_in_file[idx + 1]['sig_start'] - 1
                if gap_start <= gap_end:
                    gaps.append((gap_start, gap_end))
            # After last function
            last_end = funcs_in_file[-1]['end'] + 1
            if last_end < len(lines):
                gaps.append((last_end, len(lines) - 1))
        else:
            gaps.append((0, len(lines) - 1))

        for gap_start, gap_end in gaps:
            gap_lines = lines[gap_start:gap_end + 1]
            _parse_gap_region(gap_lines, filename, globals_map, inter_macros)

    # Also scan .h files for globals (rare but possible)
    for filename, content in all_contents.items():
        if not filename.endswith('.h'):
            continue
        lines = content.split('\n')
        _parse_gap_region(lines, filename, globals_map, inter_macros)

    return globals_map, inter_macros


def _parse_gap_region(gap_lines, filename, globals_map, inter_macros):
    """Parse a gap region (lines between functions) for globals and macros."""
    i = 0
    while i < len(gap_lines):
        line = gap_lines[i]
        stripped = line.strip()

        # Skip empty lines, comments, includes, guards
        if (stripped == '' or stripped.startswith('//') or
            stripped.startswith('#include') or
            stripped.startswith('#ifndef') or stripped.startswith('#endif') or
            stripped.startswith('/*') or stripped.startswith('*') or
            stripped.startswith('#if') or stripped.startswith('#else') or
            stripped.startswith('#undef')):
            # Handle block comments
            if stripped.startswith('/*') and '*/' not in stripped:
                while i < len(gap_lines) - 1 and '*/' not in gap_lines[i]:
                    i += 1
            i += 1
            continue

        # Match #define macros (single or multi-line)
        m = re.match(r'^\s*#\s*define\s+(\w+)', line)
        if m:
            macro_name = m.group(1)
            macro_lines = [line]
            while line.rstrip().endswith('\\') and i + 1 < len(gap_lines):
                i += 1
                line = gap_lines[i]
                macro_lines.append(line)
            inter_macros[macro_name] = {
                'text': '\n'.join(macro_lines),
                'file': filename,
            }
            i += 1
            continue

        # Match static const / const variable/array definitions (top-level only)
        # Skip indented lines — those are likely local variables from missed function bodies
        if line[0:1] in ('\t', ' ') and not line.startswith('static') and not line.startswith('const'):
            i += 1
            continue
        m = re.match(
            r'^(?:static\s+)?(?:const\s+)?(?:\w[\w\s*]*)\s+(?:ATTRIBUTE_UNUSED\s+)?(?:\*\s*)?(\w+)\s*\[?\]?\s*=',
            stripped
        )
        if m:
            var_name = m.group(1)
            # Collect complete definition (may span multiple lines to ';')
            def_lines = [line]
            j = i
            brace_depth = line.count('{') - line.count('}')
            while (';' not in gap_lines[j] or brace_depth > 0) and j + 1 < len(gap_lines):
                j += 1
                def_lines.append(gap_lines[j])
                brace_depth += gap_lines[j].count('{') - gap_lines[j].count('}')
            globals_map[var_name] = {
                'text': '\n'.join(def_lines),
                'file': filename,
            }
            i = j + 1
            continue

        # Match top-level macro invocations that generate globals via ## token pasting
        # e.g. DECL_HASH_ALG(md2, ...) generates _md2_hash_name[], _md2_hash_alg, etc.
        m = re.match(r'^(\w+)\s*\(', stripped)
        if m and m.group(1) in inter_macros:
            macro_name = m.group(1)
            macro_def = inter_macros[macro_name]['text']
            if '##' in macro_def:
                inv_lines = [line]
                j = i
                brace_depth = line.count('{') - line.count('}')
                while (';' not in gap_lines[j] or brace_depth > 0) and j + 1 < len(gap_lines):
                    j += 1
                    inv_lines.append(gap_lines[j])
                    brace_depth += gap_lines[j].count('{') - gap_lines[j].count('}')
                inv_text = '\n'.join(inv_lines)
                args_match = re.search(r'\(\s*(\w+)', inv_text)
                if args_match:
                    first_arg = args_match.group(1).strip()
                    param_match = re.match(r'#\s*define\s+\w+\s*\(\s*(\w+)', macro_def)
                    if param_match:
                        param_name = param_match.group(1)
                        expanded = macro_def.replace('##' + param_name + '##', first_arg)
                        expanded = re.sub(r'##' + re.escape(param_name) + r'\b', first_arg, expanded)
                        expanded = re.sub(r'\b' + re.escape(param_name) + r'##', first_arg, expanded)
                        for ident_m in re.finditer(r'(?:static\s+const\s+\w[\w\s*]*\s+)(\w+)\s*[\[=({]', expanded):
                            gen_name = ident_m.group(1)
                            if gen_name not in globals_map:
                                globals_map[gen_name] = {
                                    'text': inv_text,
                                    'file': filename,
                                    'macro_def': macro_name,
                                }
                i = j + 1
                continue

        i += 1


def collect_macros_from_headers(all_contents):
    """收集 .h 文件中的 #define 宏名。"""
    macros = {}
    for filename, content in all_contents.items():
        if not filename.endswith('.h'):
            continue
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            m = re.match(r'^\s*#\s*define\s+(\w+)', lines[i])
            if m:
                macro_name = m.group(1)
                macro_lines = [lines[i]]
                while lines[i].rstrip().endswith('\\') and i + 1 < len(lines):
                    i += 1
                    macro_lines.append(lines[i])
                macros[macro_name] = {
                    'text': '\n'.join(macro_lines),
                    'file': filename,
                }
            i += 1
    return macros


def collect_type_definitions(all_contents):
    """从所有文件内容中收集 typedef/enum/struct 定义。

    Returns:
        type_defs: OrderedDict  name -> definition text
        enum_members: dict  member_name -> typedef_name
    """
    type_defs = OrderedDict()
    enum_members = {}

    for filename, content in all_contents.items():
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]

            # typedef ... name; (single line, no braces)
            m = re.match(r'^\s*typedef\s+.+\s+(\w+)\s*;', line)
            if m and '{' not in line:
                type_defs[m.group(1)] = line
                i += 1
                continue

            # typedef enum/struct/union { ... } name; (multi-line)
            if re.match(r'^\s*typedef\s+(?:enum|struct|union)\s*\w*\s*\{', line):
                block_lines = [line]
                brace = line.count('{') - line.count('}')
                j = i + 1
                while j < len(lines) and brace > 0:
                    block_lines.append(lines[j])
                    brace += lines[j].count('{') - lines[j].count('}')
                    j += 1
                block = '\n'.join(block_lines)
                tm = re.search(r'\}\s*(\w+)\s*;', block)
                if tm:
                    td_name = tm.group(1)
                    type_defs[td_name] = block
                    if 'enum' in block_lines[0]:
                        for member_match in re.finditer(r'^\s*(\w+)\s*=', block, re.MULTILINE):
                            enum_members[member_match.group(1)] = td_name
                        for member_match in re.finditer(r'^\s*(\w+)\s*[,}]', block, re.MULTILINE):
                            mname = member_match.group(1)
                            if mname not in ('typedef', 'enum', 'struct', 'union'):
                                enum_members[mname] = td_name
                i = j
                continue

            i += 1

    return type_defs, enum_members


def _text_references(text, name):
    """Check if text references a given identifier name."""
    return bool(re.search(r'\b' + re.escape(name) + r'\b', text))


# ─── 主切片逻辑 ────────────────────────────────────────────────────

def build_project_index(project_dir):
    """扫描项目目录，建立完整的函数索引。"""
    all_contents = OrderedDict()
    all_functions = {}
    all_functions_by_file = defaultdict(list)

    for fname in sorted(os.listdir(project_dir)):
        if not fname.endswith(('.c', '.h')):
            continue
        path = os.path.join(project_dir, fname)
        with open(path, 'r') as f:
            content = f.read()
        all_contents[fname] = content

        funcs = find_function_boundaries(content, fname)
        for func in funcs:
            all_functions[func['name']] = func
            all_functions[func['name']]['content'] = content
            all_functions_by_file[fname].append(func)

    # Collect header macros
    header_macros = collect_macros_from_headers(all_contents)

    # Collect inter-function globals and macros from .c files
    inter_globals, inter_macros = collect_inter_function_content(
        all_contents, all_functions_by_file
    )

    # Merge all macros (header macros + inter-function macros)
    all_macros = {}
    all_macros.update(header_macros)
    all_macros.update(inter_macros)

    return all_contents, all_functions, all_macros, inter_globals


def resolve_dependencies(target_func, all_functions, all_macros, all_globals,
                         mode='inline', max_depth=50):
    """递归解析目标函数的依赖（被调函数、宏、全局变量）。

    Performs transitive resolution:
    - Function → called functions
    - Function → referenced globals → globals referenced by those globals
    - Function → referenced macros → macros/globals referenced by those macros
    """
    needed_funcs = OrderedDict()
    needed_macros = set()
    needed_globals = set()
    visited = set()

    def resolve_func(func_name, depth=0):
        if func_name in visited or depth > max_depth:
            return
        visited.add(func_name)

        if func_name not in all_functions:
            return

        func_info = all_functions[func_name]
        content = func_info['content']
        body_lines = content.split('\n')[func_info['sig_start']:func_info['end'] + 1]
        body_text = '\n'.join(body_lines)

        # Direct macro references
        for mname in all_macros:
            if _text_references(body_text, mname):
                needed_macros.add(mname)

        # Direct global references from THIS function only
        func_globals = set()
        for gname in all_globals:
            if _text_references(body_text, gname):
                needed_globals.add(gname)
                func_globals.add(gname)

        # Called functions
        calls = extract_function_calls(content, func_info['body_start'], func_info['end'])
        project_calls = [c for c in calls if c in all_functions and c != func_name]

        # Check globals directly referenced by THIS function for function pointers
        for gname in func_globals:
            if gname in all_globals:
                gtext = all_globals[gname]['text']
                for candidate in all_functions:
                    if candidate != func_name and _text_references(gtext, candidate):
                        if candidate not in project_calls:
                            project_calls.append(candidate)

        for callee in project_calls:
            if callee not in visited:
                resolve_func(callee, depth + 1)

        needed_funcs[func_name] = func_info

    resolve_func(target_func)

    # Transitive resolution: globals → globals, globals → macros, macros → globals
    changed = True
    while changed:
        changed = False
        # Check globals for references to other globals
        for gname in list(needed_globals):
            if gname not in all_globals:
                continue
            gtext = all_globals[gname]['text']
            for other_g in all_globals:
                if other_g not in needed_globals and _text_references(gtext, other_g):
                    needed_globals.add(other_g)
                    changed = True
            # Check globals for macro references
            for mname in all_macros:
                if mname not in needed_macros and _text_references(gtext, mname):
                    needed_macros.add(mname)
                    changed = True
            # Check globals for function references (function pointers in arrays)
            for fname in all_functions:
                if fname not in needed_funcs and _text_references(gtext, fname):
                    resolve_func(fname)
                    changed = True

        # Check macros for references to globals
        for mname in list(needed_macros):
            if mname not in all_macros:
                continue
            mtext = all_macros[mname]['text']
            for gname in all_globals:
                if gname not in needed_globals and _text_references(mtext, gname):
                    needed_globals.add(gname)
                    changed = True
            # Check macros for references to other macros
            for other_m in all_macros:
                if other_m not in needed_macros and other_m != mname:
                    if _text_references(mtext, other_m):
                        needed_macros.add(other_m)
                        changed = True

    return needed_funcs, needed_macros, needed_globals


def resolve_dependencies_stub(target_func, all_functions, all_macros, all_globals):
    """Stub 模式专用：只解析目标函数的直接依赖。

    收集范围：
    - 目标函数体直接调用的函数（只取签名，不递归）
    - 目标函数体直接引用的宏
    - 目标函数体直接引用的全局变量（含全局→全局/宏的传递依赖）
    不收集：
    - callee 的 callee
    - 全局变量中的函数指针引用
    - callee 体内引用的全局变量
    """
    if target_func not in all_functions:
        return OrderedDict(), set(), set()

    func_info = all_functions[target_func]
    content = func_info['content']
    body_lines = content.split('\n')[func_info['sig_start']:func_info['end'] + 1]
    body_text = '\n'.join(body_lines)

    needed_funcs = OrderedDict()
    needed_macros = set()
    needed_globals = set()

    # Direct macro references from target body
    for mname in all_macros:
        if _text_references(body_text, mname):
            needed_macros.add(mname)

    # Direct global references from target body
    for gname in all_globals:
        if _text_references(body_text, gname):
            needed_globals.add(gname)

    # Direct callee functions (no recursion)
    calls = extract_function_calls(content, func_info['body_start'], func_info['end'])
    for callee in calls:
        if callee in all_functions and callee != target_func:
            needed_funcs[callee] = all_functions[callee]

    # Target function itself
    needed_funcs[target_func] = func_info

    # Scan callee signatures for macros (e.g., ATTRIBUTE_UNUSED in parameter lists)
    for callee_name, callee_info in needed_funcs.items():
        if callee_name == target_func:
            continue
        sig_lines = callee_info['content'].split('\n')[callee_info['sig_start']:callee_info['body_start'] + 1]
        sig_text = '\n'.join(sig_lines)
        for mname in all_macros:
            if mname not in needed_macros and _text_references(sig_text, mname):
                needed_macros.add(mname)

    # Transitive resolution for globals only (globals→globals, globals→macros, macros→globals)
    # No function-pointer expansion from globals
    changed = True
    while changed:
        changed = False
        for gname in list(needed_globals):
            if gname not in all_globals:
                continue
            gtext = all_globals[gname]['text']
            for other_g in all_globals:
                if other_g not in needed_globals and _text_references(gtext, other_g):
                    needed_globals.add(other_g)
                    changed = True
            for mname in all_macros:
                if mname not in needed_macros and _text_references(gtext, mname):
                    needed_macros.add(mname)
                    changed = True
        for mname in list(needed_macros):
            if mname not in all_macros:
                continue
            mtext = all_macros[mname]['text']
            for gname in all_globals:
                if gname not in needed_globals and _text_references(mtext, gname):
                    needed_globals.add(gname)
                    changed = True
            for other_m in all_macros:
                if other_m not in needed_macros and other_m != mname:
                    if _text_references(mtext, other_m):
                        needed_macros.add(other_m)
                        changed = True

    # Ensure DECL_* macro definitions for macro-generated globals
    for gname in list(needed_globals):
        if gname in all_globals and 'macro_def' in all_globals[gname]:
            macro_name = all_globals[gname]['macro_def']
            if macro_name in all_macros:
                needed_macros.add(macro_name)

    return needed_funcs, needed_macros, needed_globals


def extract_function_text(func_info):
    """从文件内容中提取函数完整文本（含签名）。"""
    lines = func_info['content'].split('\n')
    return '\n'.join(lines[func_info['sig_start']:func_info['end'] + 1])


def extract_function_declaration(func_info):
    """提取函数的声明（签名 + 分号，用于 stub 模式）。"""
    lines = func_info['content'].split('\n')
    sig_lines = []
    for i in range(func_info['sig_start'], func_info['body_start'] + 1):
        line = lines[i]
        if '{' in line:
            line = line[:line.index('{')].rstrip()
            sig_lines.append(line)
            break
        sig_lines.append(line)
    sig = '\n'.join(sig_lines).rstrip()
    if not sig.endswith(';'):
        sig += ';'
    return sig


def _topo_sort_globals(needed_globals, all_globals, all_macros, needed_macros):
    """Topologically sort globals and macros so dependencies come first.

    Returns two lists: (sorted_globals, sorted_macros) where each item
    appears after all items it depends on.
    """
    # Build dependency graph for globals
    global_deps = {}
    for gname in needed_globals:
        if gname not in all_globals:
            continue
        gtext = all_globals[gname]['text']
        deps = set()
        for other_g in needed_globals:
            if other_g != gname and other_g in all_globals:
                if _text_references(gtext, other_g):
                    deps.add(other_g)
        global_deps[gname] = deps

    # Simple topological sort (DFS-based)
    sorted_globals = []
    g_visited = set()
    g_in_stack = set()

    def visit_global(g):
        if g in g_visited:
            return
        if g in g_in_stack:
            # Cycle — just add it
            sorted_globals.append(g)
            g_visited.add(g)
            return
        g_in_stack.add(g)
        for dep in global_deps.get(g, set()):
            visit_global(dep)
        g_in_stack.discard(g)
        g_visited.add(g)
        sorted_globals.append(g)

    for g in sorted(needed_globals):
        visit_global(g)

    # Build dependency graph for macros
    macro_deps = {}
    for mname in needed_macros:
        if mname not in all_macros:
            continue
        mtext = all_macros[mname]['text']
        deps = set()
        for other_m in needed_macros:
            if other_m != mname and other_m in all_macros:
                if _text_references(mtext, other_m):
                    deps.add(other_m)
        # Macros that reference globals should come after those globals
        for gname in needed_globals:
            if gname in all_globals and _text_references(mtext, gname):
                deps.add(f'__global__{gname}')
        macro_deps[mname] = deps

    sorted_macros = []
    m_visited = set()
    m_in_stack = set()

    def visit_macro(m):
        if m in m_visited:
            return
        if m in m_in_stack:
            sorted_macros.append(m)
            m_visited.add(m)
            return
        m_in_stack.add(m)
        for dep in macro_deps.get(m, set()):
            if not dep.startswith('__global__'):
                visit_macro(dep)
        m_in_stack.discard(m)
        m_visited.add(m)
        sorted_macros.append(m)

    for m in sorted(needed_macros):
        visit_macro(m)

    return sorted_globals, sorted_macros


def generate_slice(target_func, project_dir, mode='inline'):
    """生成目标函数的最小可验证切片。

    Always uses precise minimal collection — no full-header dump.
    """
    all_contents, all_functions, all_macros, all_globals = build_project_index(project_dir)

    if target_func not in all_functions:
        print(f"Error: function '{target_func}' not found in project", file=sys.stderr)
        print(f"Available functions: {sorted(all_functions.keys())[:20]}...", file=sys.stderr)
        return None

    # Resolve dependencies
    if mode == 'stub':
        needed_funcs, needed_macros, needed_globals = resolve_dependencies_stub(
            target_func, all_functions, all_macros, all_globals
        )
    else:
        needed_funcs, needed_macros, needed_globals = resolve_dependencies(
            target_func, all_functions, all_macros, all_globals, mode
        )
        # Ensure DECL_* macro definitions are included for macro-generated globals
        for gname in list(needed_globals):
            if gname in all_globals and 'macro_def' in all_globals[gname]:
                macro_name = all_globals[gname]['macro_def']
                if macro_name in all_macros:
                    needed_macros.add(macro_name)

    # Collect type definitions
    type_defs, enum_members = collect_type_definitions(all_contents)

    # Find types referenced by needed functions
    all_type_names = set(type_defs.keys())
    all_needed_types = set()
    for fname, finfo in needed_funcs.items():
        if mode == 'stub' and fname != target_func:
            # Stub mode: only scan callee signatures, not bodies
            scan_end = finfo['body_start']
        else:
            scan_end = finfo['end']
        types = extract_type_references(finfo['content'], finfo['sig_start'], scan_end, all_type_names)
        all_needed_types.update(types)
        body_lines = finfo['content'].split('\n')[finfo['sig_start']:scan_end + 1]
        body_text = '\n'.join(body_lines)
        for member_name, td_name in enum_members.items():
            if re.search(r'\b' + re.escape(member_name) + r'\b', body_text):
                all_needed_types.add(td_name)

    # Find types referenced by needed globals
    for gname in needed_globals:
        if gname not in all_globals:
            continue
        gtext = all_globals[gname]['text']
        for tname in all_type_names:
            if _text_references(gtext, tname):
                all_needed_types.add(tname)
        for member_name, td_name in enum_members.items():
            if _text_references(gtext, member_name):
                all_needed_types.add(td_name)

    # Find types referenced by needed macros
    for mname in needed_macros:
        if mname not in all_macros:
            continue
        mtext = all_macros[mname]['text']
        for tname in all_type_names:
            if _text_references(mtext, tname):
                all_needed_types.add(tname)

    # Find macros referenced by needed types (e.g., ATTRIBUTE_UNUSED in struct fields)
    for tname in list(all_needed_types):
        if tname not in type_defs:
            continue
        tdef = type_defs[tname]
        for mname in all_macros:
            if mname not in needed_macros and _text_references(tdef, mname):
                needed_macros.add(mname)

    # Pre-compute functions referenced in globals (needed for type scanning)
    _funcs_in_globals_pre = set()
    for gname in needed_globals:
        if gname not in all_globals:
            continue
        gtext = all_globals[gname]['text']
        for fname in all_functions:
            if _text_references(gtext, fname):
                _funcs_in_globals_pre.add(fname)
    # Scan their signatures for types
    for fname in _funcs_in_globals_pre:
        finfo = all_functions[fname]
        sig_types = extract_type_references(finfo['content'], finfo['sig_start'], finfo['body_start'], all_type_names)
        all_needed_types.update(sig_types)

    # Recursively resolve type dependencies (struct fields may reference other typedefs)
    resolved_types = set()
    def resolve_type_deps(tname):
        if tname in resolved_types:
            return
        resolved_types.add(tname)
        if tname in type_defs:
            tdef = type_defs[tname]
            for other_type in all_type_names:
                if other_type != tname and re.search(r'\b' + re.escape(other_type) + r'\b', tdef):
                    all_needed_types.add(other_type)
                    resolve_type_deps(other_type)

    for t in list(all_needed_types):
        resolve_type_deps(t)

    # Topologically sort globals and macros
    sorted_globals, sorted_macros = _topo_sort_globals(
        needed_globals, all_globals, all_macros, needed_macros
    )

    # ─── Assemble output ─────────────────────────────
    output_parts = []

    output_parts.append("/* Auto-generated minimal verifiable slice */")
    output_parts.append(f"/* Target function: {target_func} */")
    output_parts.append(f"/* Mode: {mode} */")
    output_parts.append("")

    # Standard includes
    output_parts.append("#include <stdint.h>")
    output_parts.append("#include <unistd.h>")
    output_parts.append("#include <string.h>")

    # Check if target function uses printf/fprintf (stub mode: only target body matters)
    target_info = all_functions[target_func]
    target_body_lines = target_info['content'].split('\n')[target_info['sig_start']:target_info['end'] + 1]
    all_func_text = '\n'.join(target_body_lines)
    if re.search(r'\b(?:printf|fprintf|sprintf|snprintf)\b', all_func_text):
        output_parts.append("#include <stdio.h>")
    if re.search(r'\b(?:malloc|calloc|realloc|free|atoi|atol|strtol|strtoul|exit|abort)\b', all_func_text):
        output_parts.append("#include <stdlib.h>")
    output_parts.append("")

    # Base type aliases — always emit first, skip duplicates in type_defs later
    base_type_names = {'u8', 'u16', 'u32', 'u64'}
    output_parts.append("typedef uint8_t  u8;")
    output_parts.append("typedef uint16_t u16;")
    output_parts.append("typedef uint32_t u32;")
    output_parts.append("typedef uint64_t u64;")
    output_parts.append("")

    # X509_FILE_NUM — needed by many macros, define a default
    if 'X509_FILE_NUM' in needed_macros or any(
        'X509_FILE_NUM' in all_macros.get(m, {}).get('text', '')
        for m in needed_macros
    ):
        output_parts.append("#define X509_FILE_NUM 0")
        needed_macros.discard('X509_FILE_NUM')
        sorted_macros = [m for m in sorted_macros if m != 'X509_FILE_NUM']

    # Essential macros that many functions depend on (emit first in dependency order)
    essential_macros_ordered = ['MAX_UINT32', 'X509_FILE_LINE_NUM_ERR',
                                'ERROR_TRACE_APPEND', 'ATTRIBUTE_UNUSED',
                                'ASN1_MAX_BUFFER_SIZE']
    emitted_macros = set()
    for mname in essential_macros_ordered:
        if mname in needed_macros and mname in all_macros:
            output_parts.append(all_macros[mname]['text'])
            emitted_macros.add(mname)

    # Remaining macros that don't depend on globals (non-sizeof macros)
    for mname in sorted_macros:
        if mname in emitted_macros:
            continue
        if mname not in all_macros:
            continue
        mtext = all_macros[mname]['text']
        # Defer macros that reference globals (e.g., sizeof-based NUM_KNOWN_*)
        refs_global = False
        for gname in needed_globals:
            if gname in all_globals and _text_references(mtext, gname):
                refs_global = True
                break
        if not refs_global:
            output_parts.append(mtext)
            emitted_macros.add(mname)

    output_parts.append("")

    # Type definitions (enum/struct/typedef) — topologically sorted, skip base types
    if all_needed_types:
        # Build dependency graph and topo-sort types
        type_dep_graph = {}
        for tname in all_needed_types:
            if tname in base_type_names or tname not in type_defs:
                continue
            deps = set()
            tdef = type_defs[tname]
            for other_t in all_needed_types:
                if other_t != tname and other_t not in base_type_names and other_t in type_defs:
                    if _text_references(tdef, other_t):
                        deps.add(other_t)
            type_dep_graph[tname] = deps

        sorted_types = []
        t_visited = set()
        t_in_stack = set()
        def visit_type(t):
            if t in t_visited:
                return
            if t in t_in_stack:
                sorted_types.append(t)
                t_visited.add(t)
                return
            t_in_stack.add(t)
            for dep in type_dep_graph.get(t, set()):
                visit_type(dep)
            t_in_stack.discard(t)
            t_visited.add(t)
            sorted_types.append(t)

        for tname in type_dep_graph:
            visit_type(tname)

        for tname in sorted_types:
            output_parts.append(type_defs[tname])
            output_parts.append("")

    # Forward declarations for functions referenced in globals
    funcs_in_globals = set()
    for gname in sorted_globals:
        if gname not in all_globals:
            continue
        gtext = all_globals[gname]['text']
        for fname in all_functions:
            if _text_references(gtext, fname):
                funcs_in_globals.add(fname)
    if funcs_in_globals:
        # Emit any macros used in these function signatures that weren't already emitted
        for fname in funcs_in_globals:
            finfo = all_functions[fname]
            sig_lines = finfo['content'].split('\n')[finfo['sig_start']:finfo['body_start'] + 1]
            sig_text = '\n'.join(sig_lines)
            for mname in all_macros:
                if mname not in emitted_macros and _text_references(sig_text, mname):
                    output_parts.append(all_macros[mname]['text'])
                    emitted_macros.add(mname)
        for fname in sorted(funcs_in_globals):
            output_parts.append(extract_function_declaration(all_functions[fname]))
        output_parts.append("")

    # Global/static constants (topologically sorted)
    if sorted_globals:
        for gname in sorted_globals:
            if gname in all_globals:
                output_parts.append(all_globals[gname]['text'])
        output_parts.append("")

    # Macros that reference globals (sizeof-based NUM_KNOWN_* etc.)
    deferred_macros = [m for m in sorted_macros if m not in emitted_macros and m in all_macros]
    if deferred_macros:
        for mname in deferred_macros:
            output_parts.append(all_macros[mname]['text'])
            emitted_macros.add(mname)
        output_parts.append("")

    # Collect external function calls not in the project (e.g., analysis tool builtins)
    std_funcs = {'printf', 'fprintf', 'sprintf', 'snprintf', 'malloc', 'calloc',
                 'realloc', 'free', 'memcpy', 'memset', 'memcmp', 'memmove',
                 'strlen', 'strcmp', 'strncmp', 'strcpy', 'strncpy', 'strcat',
                 'strncat', 'atoi', 'atol', 'strtol', 'strtoul', 'exit', 'abort',
                 'qsort', 'bsearch', 'abs', 'labs', 'fopen', 'fclose', 'fread',
                 'fwrite', 'fgets', 'fputs', 'fseek', 'ftell', 'rewind',
                 'perror', 'putchar', 'getchar', 'puts', 'gets', 'sscanf',
                 'bzero', 'bcopy', 'index', 'rindex', 'ffs', 'srand', 'rand'}
    keywords = {'if', 'else', 'for', 'while', 'do', 'switch', 'case',
                'return', 'sizeof', 'goto', 'break', 'continue', 'typedef'}
    extern_calls = set()
    scan_funcs = [needed_funcs[target_func]] if mode == 'stub' else needed_funcs.values()
    for finfo_n in scan_funcs:
        calls = extract_function_calls(finfo_n['content'], finfo_n['body_start'], finfo_n['end'])
        for c in calls:
            if c not in all_functions and c not in std_funcs and c not in keywords and c not in all_macros:
                extern_calls.add(c)
    if extern_calls:
        for ec in sorted(extern_calls):
            output_parts.append(f"extern int {ec}();")
        output_parts.append("")

    # Forward declarations for ALL functions (avoids C99 ordering issues)
    func_names = list(needed_funcs.keys())
    for fname in func_names:
        finfo = needed_funcs[fname]
        if mode == 'inline' or fname == target_func:
            output_parts.append(extract_function_declaration(finfo))
    output_parts.append("")

    # Function definitions
    for fname in func_names:
        finfo = needed_funcs[fname]
        if fname == target_func:
            output_parts.append(f"/* === Target: {fname} === */")
            output_parts.append(extract_function_text(finfo))
        else:
            if mode == 'inline':
                output_parts.append(extract_function_text(finfo))
            else:
                output_parts.append(f"/* --- Dependency: {fname} (stub) --- */")
                output_parts.append("/* TODO: add ACSL contract here */")
                output_parts.append(extract_function_declaration(finfo))
        output_parts.append("")

    return '\n'.join(output_parts)


def compute_layers(all_functions):
    """计算函数的 DAG 层次（bottom-up 验证顺序）。

    Layer 0 = 叶子函数（无项目内调用）
    Layer N = 所有 callee 都在 Layer < N 的函数

    Returns:
        layers: dict  func_name -> layer_number
        call_graph: dict  func_name -> [callee_names]
    """
    call_graph = {}
    for fname, finfo in all_functions.items():
        calls = extract_function_calls(finfo['content'], finfo['body_start'], finfo['end'])
        proj_calls = [c for c in calls if c in all_functions and c != fname]
        call_graph[fname] = proj_calls

    layers = {}
    assigned = set()
    layer_num = 0
    while len(assigned) < len(all_functions):
        current_layer = []
        for fname in all_functions:
            if fname in assigned:
                continue
            unresolved = [c for c in call_graph[fname] if c not in assigned]
            if not unresolved:
                current_layer.append(fname)
        if not current_layer:
            current_layer = [f for f in all_functions if f not in assigned]
        for f in current_layer:
            layers[f] = layer_num
            assigned.add(f)
        layer_num += 1

    return layers, call_graph


