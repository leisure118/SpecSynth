"""spectool extract — pull one function (or list all) from a C file."""

import os

from ..registry import command
from ..io import emit_json, fail
from engine.spectool_core import cextract


@command(name="extract",
         help="Extract a single C function as a standalone snippet (or list all functions).")
def configure(parser):
    parser.add_argument("--src", required=True, help="C source file.")
    parser.add_argument("--func", default=None,
                        help="Function name to extract. Omit to list all functions.")
    parser.add_argument("--out", default=None, help="Write the extracted function to this file.")


def run(args):
    if not os.path.exists(args.src):
        fail("source file not found: %s" % args.src)
    with open(args.src, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()

    funcs = cextract.extract_functions(source)

    if not args.func:
        emit_json({
            "functions": [
                {"name": n, "start_line": s, "end_line": e} for (n, _, s, e) in funcs
            ],
            "count": len(funcs),
        })

    match = next(((n, src, s, e) for (n, src, s, e) in funcs if n == args.func), None)
    if match is None:
        fail("function '%s' not found in %s" % (args.func, args.src),
             available=[n for (n, _, _, _) in funcs])

    name, src, start, end = match
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(src)

    emit_json({
        "name": name,
        "start_line": start,
        "end_line": end,
        "source": src,
        "out": args.out,
    })
