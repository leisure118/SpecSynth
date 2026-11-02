"""spectool save-contract — extract verified contract from .acsl.c into contracts.json."""

import os
import re
import json

from ..registry import command
from ..io import emit_json, fail, log


def _extract_contract(source, func_name=None):
    """Extract the ACSL contract block for the target function.

    Finds the `/* === Target: <func> === */` marker and looks for the
    `/*@ ... */` block either immediately above or immediately below it.
    """
    lines = source.split('\n')

    target_line = None
    detected_name = None
    for i, line in enumerate(lines):
        m = re.search(r'/\*\s*===\s*Target:\s*(\S+)\s*===\s*\*/', line)
        if m:
            target_line = i
            detected_name = m.group(1)
            break

    if target_line is None:
        return None, None, "no /* === Target: ... === */ marker found"

    if func_name and detected_name != func_name:
        return None, None, ("target mismatch: expected '%s', found '%s'"
                            % (func_name, detected_name))

    contract_start = None
    contract_end = None

    # Search ABOVE the target marker
    for j in range(target_line - 1, -1, -1):
        stripped = lines[j].strip()
        if not stripped:
            continue
        if stripped.endswith('*/') and contract_end is None:
            contract_end = j
        if contract_end is not None and stripped.startswith('/*@'):
            contract_start = j
            break
        if contract_end is None:
            break

    # Search BELOW the target marker if not found above
    if contract_start is None:
        contract_start = None
        contract_end = None
        for j in range(target_line + 1, len(lines)):
            stripped = lines[j].strip()
            if not stripped:
                continue
            if stripped.startswith('/*@') and contract_start is None:
                contract_start = j
            if contract_start is not None and stripped.endswith('*/'):
                contract_end = j
                break
            if contract_start is None:
                break

    if contract_start is None or contract_end is None:
        return detected_name, None, "no /*@ ... */ block found near target marker"

    contract = '\n'.join(lines[contract_start:contract_end + 1])
    return detected_name, contract, None


@command(name="save-contract",
         help="Extract verified contract from .acsl.c and save to contracts.json.")
def configure(parser):
    parser.add_argument("--acsl", required=True,
                        help="Path to the verified .acsl.c file.")
    parser.add_argument("--db", required=True,
                        help="Path to contracts.json (created if missing, merged if exists).")
    parser.add_argument("--func", default=None,
                        help="Expected function name (optional cross-check).")
    parser.add_argument("--proved", default=None,
                        help="Proved goals string, e.g. '24/24' (optional metadata).")


def run(args):
    if not os.path.exists(args.acsl):
        fail("file not found: %s" % args.acsl)

    with open(args.acsl, 'r', encoding='utf-8') as f:
        source = f.read()

    func_name, contract, err = _extract_contract(source, args.func)
    if err:
        fail(err)

    if not os.path.exists(args.db):
        fail("contracts.json not found: %s (run init-contracts first)" % args.db)

    with open(args.db, 'r', encoding='utf-8') as f:
        db = json.load(f)

    if func_name not in db:
        fail("function '%s' not found in %s" % (func_name, args.db))

    # Never promote an agent's --proved claim into a reusable contract.
    from engine.verification.framac_runtime import run_candidate
    from pathlib import Path
    import tempfile
    if re.search(r'\b(?:admit|assume|axiom|axiomatic)\b',source):
        fail('Unproved assumptions cannot enter the contract library')
    proof_root=Path.cwd()/'.platform-proofs';proof_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=proof_root) as folder:
        proof=run_candidate([{'path':'candidate.c','content':source}], 'candidate.c','single',Path(folder),40)
    if not proof.get('verified'):
        fail('Contract rejected: actual Frama-C verification did not pass')
    args.proved=str(proof['verified_count'])+'/'+str(proof['verified_count'])
    db[func_name]["contract"] = contract
    db[func_name]["status"] = "pass"
    db[func_name]["source"] = args.acsl
    if args.proved:
        db[func_name]["proved"] = args.proved

    with open(args.db, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        f.write('\n')

    log("[save-contract] saved '%s' to %s" % (func_name, args.db))

    emit_json({
        "ok": True,
        "func": func_name,
        "db": args.db,
        "contract_lines": contract.count('\n') + 1,
    })
