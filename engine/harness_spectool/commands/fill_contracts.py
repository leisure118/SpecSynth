"""spectool fill-contracts — replace TODO markers in stub files with verified contracts."""

import os
import re
import json

from ..registry import command
from ..io import emit_json, fail, log


@command(name="fill-contracts",
         help="Fill callee contracts from contracts.json into a stub C file.")
def configure(parser):
    parser.add_argument("--file", required=True,
                        help="Stub C file with /* TODO */ markers.")
    parser.add_argument("--db", required=True,
                        help="Path to contracts.json.")
    parser.add_argument("--out", default=None,
                        help="Output path (default: overwrite --file in place).")


def run(args):
    if not os.path.exists(args.file):
        fail("file not found: %s" % args.file)
    if not os.path.exists(args.db):
        fail("contracts database not found: %s" % args.db)

    with open(args.file, 'r', encoding='utf-8') as f:
        source = f.read()

    with open(args.db, 'r', encoding='utf-8') as f:
        db = json.load(f)

    lines = source.split('\n')
    result_lines = []
    filled = []
    skipped = []
    i = 0
    while i < len(lines):
        dep_match = re.match(
            r'\s*/\*\s*---\s*Dependency:\s*(\S+)\s*\(stub\)\s*---\s*\*/',
            lines[i]
        )
        if dep_match:
            callee_name = dep_match.group(1)
            result_lines.append(lines[i])
            i += 1

            has_todo = (i < len(lines)
                        and re.match(r'\s*/\*\s*TODO.*\*/', lines[i]))
            if has_todo:
                i += 1

            entry = db.get(callee_name, {})
            contract = entry.get("contract")

            if contract:
                result_lines.append(contract)
                # Skip old declaration lines — replace with signature from db
                sig = entry.get("signature")
                if sig:
                    while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('/*'):
                        i += 1
                    result_lines.append(sig)
                    filled.append(callee_name)
                else:
                    filled.append(callee_name)
            else:
                if has_todo:
                    result_lines.append("/* TODO: add ACSL contract here */")
                skipped.append(callee_name)
        else:
            result_lines.append(lines[i])
            i += 1

    output = '\n'.join(result_lines)
    out_path = args.out or args.file
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)

    log("[fill-contracts] %s: filled %d, skipped %d" % (
        os.path.basename(out_path), len(filled), len(skipped)))

    emit_json({
        "ok": True,
        "file": out_path,
        "filled": filled,
        "skipped": skipped,
    })
