"""spectool check-admit — scan an annotated C file for illegal //@ admit usage."""

import os

from ..registry import command
from ..io import emit_json, fail
from engine.spectool_core import admit


@command(name="check-admit",
         help="Scan .acsl.c for illegal admit usage (only \\valid/\\separated allowed).")
def configure(parser):
    parser.add_argument("-f", "--file", required=True,
                        help="Annotated C file to check.")


def run(args):
    if not os.path.exists(args.file):
        fail("input file not found: %s" % args.file)
    with open(args.file, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()

    result = admit.check_admits(source)
    emit_json(result)
