"""spectool inject — place ACSL annotations into C source at correct positions.

The function contract and/or loop annotations are supplied by Claude (skill
layer); this command only does the deterministic placement (docs/design.md §6.3).

ACSL inputs accept either a literal string or `@path` to read from a file.
Loop specs are supplied as JSON (literal or `@path`):
    [{"line": 34, "acsl": "loop invariant 0<=i<=n; loop assigns i;"}, ...]
"""

import os
import json

from ..registry import command
from ..io import emit_json, fail
from engine.spectool_core import inject as inject_mod


def _read_arg(value):
    """Resolve a `@file` reference to its contents; otherwise return as-is."""
    if value is None:
        return None
    if value.startswith("@"):
        path = value[1:]
        if not os.path.exists(path):
            fail("referenced file not found: %s" % path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return value


@command(name="inject",
         help="Inject ACSL function contract and/or loop annotations into a C file.")
def configure(parser):
    parser.add_argument("--src", required=True, help="Input C file.")
    parser.add_argument("--out", required=True, help="Output (annotated) C file.")
    parser.add_argument("--func", default=None, help="Function the contract applies to.")
    parser.add_argument("--acsl", default=None,
                        help="Function contract ACSL (literal or @file).")
    parser.add_argument("--loops", default=None,
                        help='Loop specs as JSON list (literal or @file): '
                             '[{"line":N,"acsl":"..."}].')


def run(args):
    if not os.path.exists(args.src):
        fail("source file not found: %s" % args.src)
    with open(args.src, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()

    contract = _read_arg(args.acsl)
    loops_raw = _read_arg(args.loops)
    loop_specs = None
    if loops_raw:
        try:
            loop_specs = json.loads(loops_raw)
        except json.JSONDecodeError as e:
            fail("--loops is not valid JSON: %s" % e)

    if not contract and not loop_specs:
        fail("nothing to inject: provide --acsl and/or --loops")

    try:
        annotated = inject_mod.inject(
            source,
            func_contract=contract,
            func_name=args.func,
            loop_specs=loop_specs,
        )
    except ValueError as e:
        fail(str(e))

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(annotated)

    emit_json({
        "ok": True,
        "out": args.out,
        "injected_contract": bool(contract),
        "injected_loops": len(loop_specs) if loop_specs else 0,
    })
