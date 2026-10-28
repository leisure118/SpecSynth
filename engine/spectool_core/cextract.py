"""Extract individual C functions from a source file.

Distilled from FM-Agent/src/extract.py — kept only the C/C++ path (this project
is C + Frama-C only, docs/design.md "范围边界") and dropped the multi-language
LANG_CONFIG table, the phases.json batch driver, and test-file heuristics. The
robust brace matcher (string/char/comment aware) is preserved.

Returns functions as (name, source_text, start_line, end_line) so callers can
map back to 1-based line numbers in the original file.

No LLM calls.
"""

import re

_C_KEYWORDS = {
    "if", "else", "while", "for", "do", "switch", "case", "return",
    "break", "continue", "goto", "sizeof", "struct", "union", "enum",
    "typedef", "extern", "inline", "static", "const", "volatile",
}
_SKIP_PREFIXES = ("//", "#", "using", "typedef")
_SKIP_KW_LINE = ("struct", "union", "enum")


def _strip_angle_brackets(text):
    result = []
    depth = 0
    for ch in text:
        if ch == "<":
            depth += 1
        elif ch == ">":
            if depth > 0:
                depth -= 1
        elif depth == 0:
            result.append(ch)
    return "".join(result)


def _func_name(signature_text):
    cleaned = _strip_angle_brackets(signature_text)
    for m in re.finditer(r"\b(\w+)\s*\(", cleaned):
        name = m.group(1)
        if name not in _C_KEYWORDS:
            return name
    return None


def _find_brace_end(lines, start_idx):
    depth = 0
    found_open = False
    for i in range(start_idx, len(lines)):
        line = lines[i]
        j = 0
        n = len(line)
        while j < n:
            ch = line[j]
            if ch == '"':
                j += 1
                while j < n:
                    if line[j] == "\\":
                        j += 2
                        continue
                    if line[j] == '"':
                        j += 1
                        break
                    j += 1
                continue
            if ch == "'":
                j += 1
                while j < n:
                    if line[j] == "\\":
                        j += 2
                        continue
                    if line[j] == "'":
                        j += 1
                        break
                    j += 1
                continue
            if ch == "/" and j + 1 < n and line[j + 1] == "/":
                break
            if ch == "/" and j + 1 < n and line[j + 1] == "*":
                j += 2
                while j < n:
                    if line[j] == "*" and j + 1 < n and line[j + 1] == "/":
                        j += 2
                        break
                    j += 1
                continue
            if ch == "{":
                depth += 1
                found_open = True
            elif ch == "}":
                depth -= 1
                if found_open and depth == 0:
                    return i
            j += 1
    return len(lines) - 1


def extract_functions(source_text):
    """Return [(name, source, start_line, end_line)] (1-based line numbers)."""
    lines = [l.rstrip("\n").rstrip("\r") for l in source_text.splitlines()]
    functions = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped:
            i += 1
            continue
        if any(stripped.startswith(p) for p in _SKIP_PREFIXES):
            i += 1
            continue
        # Descend into namespaces (rare in C, present in C++ headers).
        if re.match(r"^namespace\b", stripped):
            i += 1
            continue
        if any(stripped.startswith(kw) for kw in _SKIP_KW_LINE):
            i += 1
            continue
        # C top-level functions start at column 0.
        if line[0:1].isspace():
            i += 1
            continue
        if "(" not in stripped or stripped.rstrip().endswith(";"):
            i += 1
            continue

        sig_start = i
        sig_end = i
        sig_text = stripped
        found_semi = False
        for look in range(i, min(i + 6, len(lines))):
            joined = " ".join(lines[sig_start:look + 1])
            semi_idx = joined.find(";")
            brace_idx = joined.find("{")
            if semi_idx >= 0 and (brace_idx < 0 or semi_idx < brace_idx):
                # Semicolon before any opening brace => this is a prototype declaration.
                found_semi = True
                break
            if "{" in lines[look]:
                sig_end = look
                sig_text = joined
                break
        if found_semi:
            i += 1
            continue
        if "{" not in lines[sig_end]:
            i += 1
            continue
        name = _func_name(sig_text)
        if not name:
            i += 1
            continue
        end = _find_brace_end(lines, sig_end)
        source = "\n".join(lines[sig_start:end + 1]) + "\n"
        functions.append((name, source, sig_start + 1, end + 1))
        i = end + 1

    # Deduplicate repeated names (foo, foo_1, ...).
    counts = {}
    out = []
    for name, source, s, e in functions:
        c = counts.get(name, 0)
        counts[name] = c + 1
        out.append((name if c == 0 else "%s_%d" % (name, c), source, s, e))
    return out


def extract_one(source_text, func_name):
    """Return (source, start_line, end_line) for one function, or None."""
    for name, source, s, e in extract_functions(source_text):
        if name == func_name:
            return source, s, e
    return None
