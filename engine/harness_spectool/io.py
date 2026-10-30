"""Unified output protocol for spectool (docs/design.md §5.1).

Contract that every command obeys so Claude can treat spectool as a predictable
tool rather than a black box:

  * stdout  : JSON only (one object), via emit_json()
  * stderr  : human-readable logs, via log()
  * exit code semantics:
        0  success
        2  external tool missing / unusable (frama-c, veri-clang, prover, ...)
        3  bad input (file not found, unparseable, malformed args)
        1  unexpected internal error (reserved; raised as traceback)

emit_json() and fail() both terminate the process via SystemExit so a command's
run() can simply `return emit_json(...)` / `return fail(...)`.
"""

import sys
import json

EXIT_OK = 0
EXIT_TOOL_MISSING = 2
EXIT_BAD_INPUT = 3


def log(msg):
    """Human-readable progress/diagnostic line -> stderr (never pollutes stdout)."""
    sys.stderr.write(str(msg).rstrip("\n") + "\n")
    sys.stderr.flush()


def emit_json(obj, code=EXIT_OK):
    """Write exactly one JSON object to stdout and exit with `code`."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.flush()
    raise SystemExit(code)


def fail(msg, code=EXIT_BAD_INPUT, **extra):
    """Emit a JSON error envelope and exit non-zero.

    The JSON still goes to stdout (so Claude can parse the reason); the exit code
    carries the category. `extra` keys are merged into the envelope.
    """
    payload = {"ok": False, "error": msg}
    payload.update(extra)
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.flush()
    log("[spectool] error (%d): %s" % (code, msg))
    raise SystemExit(code)
