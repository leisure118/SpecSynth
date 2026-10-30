"""spectool slice — generate a minimal compilable slice for one C function."""

import os

from ..registry import command
from ..io import emit_json, fail, log
from engine.spectool_core import slice_engine


@command(name="slice",
         help="Generate a minimal self-contained C slice for a function (inline or stub mode).")
def configure(parser):
    parser.add_argument("--project-dir", required=True,
                        help="Path to the project source directory.")
    parser.add_argument("--func", required=True,
                        help="Target function name.")
    parser.add_argument("--mode", choices=["inline", "stub"], default="inline",
                        help="inline = full callee bodies; stub = callee declarations only.")
    parser.add_argument("--out", default=None,
                        help="Write slice to this file (default: return in JSON).")


def run(args):
    if not os.path.isdir(args.project_dir):
        fail("project directory not found: %s" % args.project_dir)

    result = slice_engine.generate_slice(args.func, args.project_dir, args.mode)
    if result is None:
        fail("function '%s' not found in project" % args.func)

    lines = result.count('\n') + 1
    out_path = args.out
    if out_path:
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(result)
        log("[slice] written %s (%d lines)" % (out_path, lines))

    emit_json({
        "ok": True,
        "func": args.func,
        "mode": args.mode,
        "lines": lines,
        "out": out_path,
        "source": result if not out_path else None,
    })
