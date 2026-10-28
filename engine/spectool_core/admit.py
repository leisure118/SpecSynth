"""Detect illegal //@ admit usage in annotated C source.

Legal admits: \valid(...) and \separated(...) — WP cannot derive these from
malloc, so they must be axiomatically assumed.

Illegal admits: everything else (logical predicates, return values, math
relations, preconditions that should be `requires`).
"""

import re

_ADMIT_LINE_RE = re.compile(
    r"//\s*@\s*admit\s+(.*?)\s*;\s*$",
    re.IGNORECASE,
)

_ADMIT_BLOCK_RE = re.compile(
    r"/\*\s*@\s*admit\s+(.*?)\s*;\s*\*/",
    re.IGNORECASE | re.DOTALL,
)

_ADMIT_BARE_RE = re.compile(
    r"^\s*admit\s+(.*?)\s*;\s*$",
    re.IGNORECASE,
)

_LEGAL_PREFIX_RE = re.compile(r"^\\(valid|separated)\b")


def _is_legal(predicate):
    return bool(_LEGAL_PREFIX_RE.match(predicate.strip()))


def check_admits(source):
    """Scan source for admit declarations; classify each as legal or illegal.

    Returns a dict ready for JSON output:
      {
        "ok": bool,
        "total_admits": int,
        "valid_admits": int,
        "illegal_admits": int,
        "violations": [{"line": int, "content": str, "suggestion": str}, ...]
      }
    """
    violations = []
    legal_count = 0
    total = 0

    for lineno, line in enumerate(source.splitlines(), start=1):
        for m in _ADMIT_LINE_RE.finditer(line):
            total += 1
            predicate = m.group(1)
            if _is_legal(predicate):
                legal_count += 1
            else:
                violations.append({
                    "line": lineno,
                    "content": "admit %s;" % predicate,
                    "suggestion": "requires_or_invariant",
                })

        for m in _ADMIT_BLOCK_RE.finditer(line):
            total += 1
            predicate = m.group(1)
            if _is_legal(predicate):
                legal_count += 1
            else:
                violations.append({
                    "line": lineno,
                    "content": "admit %s;" % predicate,
                    "suggestion": "requires_or_invariant",
                })

        if _ADMIT_LINE_RE.search(line) or _ADMIT_BLOCK_RE.search(line):
            continue
        m = _ADMIT_BARE_RE.match(line)
        if m:
            total += 1
            predicate = m.group(1)
            if _is_legal(predicate):
                legal_count += 1
            else:
                violations.append({
                    "line": lineno,
                    "content": "admit %s;" % predicate,
                    "suggestion": "requires_or_invariant",
                })

    return {
        "ok": len(violations) == 0,
        "total_admits": total,
        "valid_admits": legal_count,
        "illegal_admits": len(violations),
        "violations": violations,
    }
