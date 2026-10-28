"""Parse frama-c -wp output to locate failing goals (non-destructive).

Extracted from autospec+/LLM4Veri/src/simplify_acsl.py. IMPORTANT difference:
the original `simplify_acsl` both parsed failures *and deleted* the offending
spec lines from the source file. In this pipeline the deletion is wrong —
Claude (not the CLI) decides how to repair, per docs/design.md §6.5. So we keep
only the parsing half and return a structured failure list; the source file is
never modified here.

No LLM calls.
"""

import re


def locate_failures(wp_stdout, src_basename=None):
    """Scan WP stdout text and return a list of failed-goal descriptors.

    Each item: {"goal": <kind str>, "line": <int>, "function": <str>, "kind": <category>}
    where `kind` is a coarse category Claude can branch on:
        "ensures" | "requires" | "assigns" | "loop_inv" | "assert" | "other".

    `src_basename` (e.g. "foo.acsl.c"), when given, restricts the file-scoped
    goal headers we treat as belonging to our file.
    """
    content = wp_stdout.splitlines(keepends=True)
    failures = []

    for idx in range(len(content)):
        header = content[idx]
        is_file_goal = ("Goal " in header and ("(file " in header or "file " in header))
        is_assign_goal = "Goal Assigns " in header
        if src_basename and is_file_goal and src_basename not in header:
            # A goal header that names a *different* file — skip.
            if "Goal Assigns " not in header:
                continue
        if not (is_file_goal or is_assign_goal):
            continue

        # Walk forward to find this goal's verdict.
        prove_false = False
        prove_true = False
        j = idx
        while j + 1 < len(content):
            nxt = content[j + 1]
            if "Prove: true." in nxt or ("Prover " in nxt and "returns Valid (" in nxt):
                prove_true = True
                break
            if "Prove: false." in nxt or ("Prover " in nxt and "returns Timeout (" in nxt) \
                    or ("Prover " in nxt and "returns Unknown" in nxt):
                prove_false = True
            elif "----------" in nxt:
                break
            j += 1

        if prove_true or not prove_false:
            continue

        parsed = _parse_goal_header(content, idx)
        if parsed:
            failures.append(parsed)

    return failures


def _parse_goal_header(content, idx):
    line = content[idx]
    goal = None
    fnstr = ""
    lineint = None

    try:
        if "Goal Assigns " in line:
            merged = line.strip() + " " + (content[idx + 1].strip() if idx + 1 < len(content) else "")
            goal = "Assigns"
            m = re.findall(r"Goal Assigns (.*), line (.*) in '(.*)' .*: Effect at line (.*)", merged)
            if m:
                _, linestr, fnstr, linestr2 = m[0]
            else:
                m = re.findall(r"Goal (.*) in '(.*)' .*: Effect at line (.*)", merged)
                if m:
                    goal, fnstr, linestr = m[0]
                else:
                    m = re.findall(r"Goal (.*) in (.*): Effect at line (.*)", merged)
                    if not m:
                        return None
                    goal, fnstr, linestr = m[0]
        else:
            m = re.findall(r"Goal (.*)\(file .*\.c, (.*)\)(.*):", line)
            if not m:
                return None
            goal, linestr, fnstr = m[0]

        goal = goal.strip()
        if ")" in linestr:
            linestr = linestr.split(")")[0]
        lineint = int(linestr.replace("line ", "").strip())
        if fnstr and "in '" in fnstr:
            fnstr = fnstr.replace("in '", "").replace("'", "")
        fnstr = fnstr.strip().strip("'").strip()
    except Exception:
        return None

    return {
        "goal": goal,
        "line": lineint,
        "function": fnstr,
        "kind": _categorize(goal),
    }


def _categorize(goal):
    g = goal.lower()
    if "post-condition" in g or "ensures" in g:
        return "ensures"
    if "pre-condition" in g or "requires" in g:
        return "requires"
    if "assigns" in g:
        return "assigns"
    if "loop invariant" in g or "invariant" in g:
        return "loop_inv"
    if "loop variant" in g or "decrease" in g or "variant" in g:
        return "loop_variant"
    if "assert" in g:
        return "assert"
    return "other"
