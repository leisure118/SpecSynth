"""Inject ACSL annotations into C source at the right syntactic positions.

A clean reimplementation of the idea behind autospec+'s infill marking
(LLM4Veri/mark.py + baselib), without the pickle task-list machinery. Two kinds
of injection, both as Frama-C `/*@ ... */` blocks:

  * function contract  -> placed immediately above the function signature line
  * loop annotation    -> placed immediately above a given loop statement line

Positions are resolved against the *original* file's 1-based line numbers; all
insertions are applied bottom-up so earlier line numbers stay valid.

ACSL text may be passed with or without the surrounding `/*@ */`; we normalize.
No LLM calls.
"""

import re

from . import cextract


def _as_acsl_block(text, indent=""):
    """Wrap raw ACSL clause text in a /*@ ... */ block (idempotent)."""
    body = text.strip()
    if body.startswith("/*@") or body.startswith("/*"):
        # Already a block; re-indent its lines lightly.
        return body
    # Normalize to one clause per line: prefer existing line breaks, but if the
    # text is a single line with several `;`-terminated clauses, split on `;`.
    raw_lines = [l.strip() for l in body.splitlines() if l.strip()]
    if len(raw_lines) == 1 and raw_lines[0].count(";") > 1:
        clauses = [c.strip() for c in raw_lines[0].split(";") if c.strip()]
        raw_lines = [c + ";" for c in clauses]
    if not raw_lines:
        return ""
    out = [indent + "/*@"]
    for l in raw_lines:
        out.append(indent + "  " + l)
    out.append(indent + "*/")
    return "\n".join(out)


def _indent_of(line):
    return re.match(r"\s*", line).group()


def inject(source_text, func_contract=None, func_name=None, loop_specs=None):
    """Return annotated source.

    func_contract : raw ACSL (requires/ensures/assigns ...) for the function, or None
    func_name     : which function the contract applies to (required if func_contract)
    loop_specs    : list of {"line": <int>, "acsl": <raw loop invariant text>}
                    where `line` is the 1-based line of the loop statement in the
                    ORIGINAL source.

    Raises ValueError if the function can't be located.
    """
    lines = source_text.splitlines()
    # (line_index_0based, block_text) insertions; applied from highest index down.
    insertions = []

    if func_contract:
        if not func_name:
            raise ValueError("func_name is required when func_contract is given")
        loc = cextract.extract_one(source_text, func_name)
        if loc is None:
            raise ValueError("function '%s' not found in source" % func_name)
        _, start_line, _ = loc
        idx0 = start_line - 1
        indent = _indent_of(lines[idx0]) if idx0 < len(lines) else ""
        block = _as_acsl_block(func_contract, indent)
        if block:
            insertions.append((idx0, block))

    for spec in (loop_specs or []):
        ln = spec.get("line")
        acsl = spec.get("acsl", "")
        if not ln or not acsl.strip():
            continue
        idx0 = ln - 1
        if idx0 < 0 or idx0 >= len(lines):
            continue
        indent = _indent_of(lines[idx0])
        block = _as_acsl_block(acsl, indent)
        if block:
            insertions.append((idx0, block))

    # Apply bottom-up so indices remain valid.
    for idx0, block in sorted(insertions, key=lambda x: x[0], reverse=True):
        lines.insert(idx0, block)

    return "\n".join(lines) + ("\n" if source_text.endswith("\n") else "")
