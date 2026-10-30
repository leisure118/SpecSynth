"""spectool list-layers — output bottom-up DAG verification ordering."""

import os

from ..registry import command
from ..io import emit_json, fail
from engine.spectool_core import slice_engine


@command(name="list-layers",
         help="Compute bottom-up DAG layers for verification ordering.")
def configure(parser):
    parser.add_argument("--project-dir", required=True,
                        help="Path to the project source directory.")


def run(args):
    if not os.path.isdir(args.project_dir):
        fail("project directory not found: %s" % args.project_dir)

    _, all_functions, _, _ = slice_engine.build_project_index(args.project_dir)
    layers, call_graph = slice_engine.compute_layers(all_functions)

    max_layer = max(layers.values()) if layers else 0
    layer_data = []
    for layer_num in range(max_layer + 1):
        funcs_in_layer = sorted([f for f, l in layers.items() if l == layer_num])
        entries = []
        for fname in funcs_in_layer:
            callees = sorted(call_graph.get(fname, []))
            entries.append({"name": fname, "callees": callees})
        layer_data.append({
            "layer": layer_num,
            "count": len(funcs_in_layer),
            "functions": entries,
        })

    emit_json({
        "ok": True,
        "total_functions": len(all_functions),
        "total_layers": max_layer + 1,
        "layers": layer_data,
    })
