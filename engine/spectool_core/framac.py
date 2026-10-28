"""Frama-C/WP runner + result parser.

Extracted & cleaned from autospec+/LLM4Veri/src/framac.py
(run_framac_with_wp / get_result_type). Changes vs. the quarry original:
  * removed the unused `openai` import and module-level logging side effects;
  * replaced the `sudo kill` timeout handler with a portable process-group kill;
  * returns a plain dict instead of writing bespoke `_fstd_`/`_ferr_` files
    (the caller decides where to persist stdout/stderr).

No LLM calls. Only invokes the external `frama-c` binary.
"""

import os
import io as _io
import signal
import subprocess
import datetime

# Hard ceiling on a single frama-c invocation (wall clock). The per-goal prover
# timeout is a separate, smaller knob passed as `timeout` below.
SUBPROCESS_TIMEOUT = 500

FRAMAC_BIN = os.environ.get("SPECTOOL_FRAMAC", "frama-c")


def get_result_type(stdout_text):
    """Parse frama-c -wp stdout into a result-type string.

    Returns one of:
        "Invalid"          frama-c aborted / no goals / preprocessing error
        "Pass_<n>_<m>"     n proved out of m, and n(+requires-timeouts) == m
        "Fail_<n>_<m>"     n proved out of m, n < m
        "UK"               could not determine
    Mirrors the original's tolerance: WP timeouts on `_requires` goals are
    counted as effectively discharged (callee preconditions weakened).
    """
    result_type = "UK"
    try:
        lines = _io.StringIO(stdout_text).readlines()
    except Exception:
        return result_type

    timeout_in_requires = 0
    for line in lines:
        if ("[kernel] Frama-C aborted:" in line
                or "[kernel] Plug-in wp aborted" in line
                or "[wp] Warning: No goal generated" in line
                or "error: invalid preprocessing directive" in line):
            return "Invalid"
        if "[wp] [Timeout] typed_" in line and ("_requires (" in line or "_requires_" in line):
            timeout_in_requires += 1
            continue
        if "[wp] Proved goals:" in line:
            proportion = line.split(":")[-1]
            left, right = proportion.split("/")
            left = left.strip()
            right = right.strip()
            if int(left) + int(timeout_in_requires) == int(right):
                return "Pass_" + left + "_" + right
            return "Fail_" + left + "_" + right
    return result_type


def parse_proved(result_type):
    """('Pass_3_5' | 'Fail_3_5') -> (3, 5); anything else -> (None, None)."""
    if not result_type or "_" not in result_type:
        return None, None
    parts = result_type.split("_")
    if len(parts) >= 3 and parts[-2].isdigit() and parts[-1].isdigit():
        return int(parts[-2]), int(parts[-1])
    return None, None


def verdict_of(result_type):
    """Map a result_type to a coarse verdict, trusting the Pass_/Fail_ prefix.

    The prefix already encodes get_result_type's tolerance (e.g. requires-timeout
    goals counted as discharged), so callers must NOT re-derive pass/fail from
    proved==total — that would wrongly flip a tolerated Pass_5_6 to Fail.
    Returns "Pass" | "Fail" | "Invalid" | "Unknown".
    """
    if result_type == "Invalid":
        return "Invalid"
    if result_type.startswith("Pass_"):
        return "Pass"
    if result_type.startswith("Fail_"):
        return "Fail"
    return "Unknown"


def run_framac_with_wp(cfile, timeout=8):
    """Run `frama-c -wp ...` on a single annotated C file.

    Returns a dict:
        {result_type, stdout, stderr, elapsed_sec, returncode, timed_out}
    Raises FileNotFoundError if the frama-c binary is missing (caller maps this
    to exit code 2).
    """
    if not os.path.exists(cfile):
        raise FileNotFoundError("input C file not found: %s" % cfile)

    cmd = [
        FRAMAC_BIN, "-wp",
        "-wp-rte",
        "-wp-precond-weakening",
        "-wp-prover", "Alt-Ergo,Z3",
        "-wp-print",
        "-wp-timeout", str(timeout),
        cfile,
    ]

    start = datetime.datetime.now()
    timed_out = False
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            preexec_fn=os.setpgrp,
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            "frama-c binary '%s' not found on PATH (run inside the acslagent image)" % FRAMAC_BIN
        )

    try:
        out, err = proc.communicate(timeout=SUBPROCESS_TIMEOUT)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            proc.kill()
        out, err = proc.communicate()

    elapsed = (datetime.datetime.now() - start).total_seconds()
    out_text = (out or b"").decode("utf-8", errors="replace")
    err_text = (err or b"").decode("utf-8", errors="replace")
    result_type = "Invalid" if timed_out else get_result_type(out_text)

    return {
        "result_type": result_type,
        "stdout": out_text,
        "stderr": err_text,
        "elapsed_sec": round(elapsed, 3),
        "returncode": proc.returncode,
        "timed_out": timed_out,
    }
