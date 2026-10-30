"""spectool locate-fail — parse WP output to find failing goals (read-only)."""

import os

from ..registry import command
from ..io import emit_json, fail
from engine.spectool_core import locate


@command(name="locate-fail",
         help="Parse frama-c -wp output and list failing goals with line numbers (does not modify source).")
def configure(parser):
    parser.add_argument("--wp", required=True, help="Path to saved WP stdout (from `verify --save-stdout`).")
    parser.add_argument("--src", default=None, help="Annotated C file the goals refer to (for filtering).")


def run(args):
    if not os.path.exists(args.wp):
        fail("WP output file not found: %s" % args.wp)
    with open(args.wp, "r", encoding="utf-8", errors="replace") as f:
        wp_text = f.read()

    src_base = os.path.basename(args.src) if args.src else None
    failures = locate.locate_failures(wp_text, src_basename=src_base)

    emit_json({
        "failures": failures,
        "count": len(failures),
    })
