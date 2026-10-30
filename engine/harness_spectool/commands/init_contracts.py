"""spectool init-contracts — build the full contracts.json skeleton for a project."""

import os
import json

from ..registry import command
from ..io import emit_json, fail, log
from engine.spectool_core import slice_engine


@command(name="init-contracts",
         help="Scan project and create contracts.json with all functions, layers, callees, and signatures.")
def configure(parser):
    parser.add_argument("--project-dir", required=True,
                        help="Path to the project source directory.")
    parser.add_argument("--db", required=True,
                        help="Output path for contracts.json.")


def run(args):
    if not os.path.isdir(args.project_dir):
        fail("project directory not found: %s" % args.project_dir)

    _, all_functions, _, _ = slice_engine.build_project_index(args.project_dir)
    layers, call_graph = slice_engine.compute_layers(all_functions)

    old_db = {}
    if os.path.exists(args.db):
        with open(args.db, 'r', encoding='utf-8') as f:
            old_db = json.load(f)

    db = {}
    preserved = 0
    for fname, finfo in all_functions.items():
        sig = slice_engine.extract_function_declaration(finfo)
        callees = sorted(call_graph.get(fname, []))
        layer = layers.get(fname, -1)

        db[fname] = {
            "layer": layer,
            "signature": sig,
            "callees": callees,
            "contract": None,
            "status": "pending",
            "proved": None,
        }

        old = old_db.get(fname)
        if old and old.get("contract"):
            db[fname]["contract"] = old["contract"]
            db[fname]["status"] = old.get("status", "pass")
            db[fname]["proved"] = old.get("proved")
            db[fname]["source"] = old.get("source")
            preserved += 1

    os.makedirs(os.path.dirname(args.db) or '.', exist_ok=True)
    with open(args.db, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        f.write('\n')

    total = len(db)
    max_layer = max(layers.values()) if layers else 0
    log("[init-contracts] wrote %d functions (%d layers) to %s, preserved %d contracts"
        % (total, max_layer + 1, args.db, preserved))

    emit_json({
        "ok": True,
        "db": args.db,
        "total_functions": total,
        "total_layers": max_layer + 1,
        "preserved_contracts": preserved,
    })
