#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, io, sys, time, signal
import openai
import logging
import subprocess
import datetime
from typing import List

Check_STDOUT = 1                    # Set 1 if you want to record std result
Check_STDERR = 1                    # Set 1 if you want to record err result
SubprocessTimeout = 500             # Set the timeout of subprocess
DEFAULT_FRAMAC_CPP_COMMAND = os.getenv(
    "FRAMAC_CPP_COMMAND",
    "clang -E -C -I. -I/root/.opam/default/share/frama-c/share/libc "
    "-D__FRAMAC__ -D__FC_MACHDEP_X86_64 -dD -nostdinc -m64 %1 -o %2",
)


# create subprocess according to the value of Check_STDOUT and Check_STDERR
def create_FRAMAC_subprocess(FRAMAC_Command, Check_STDOUT, Check_STDERR):
    # Create the FRAMAC command
    # Check_STDOUT and Check_STDERR are used to check the standard output and error of the FRAMAC subprocess
    if (Check_STDOUT == 1 and Check_STDERR == 1):
        process = subprocess.Popen(FRAMAC_Command, close_fds=True, preexec_fn=os.setpgrp, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif (Check_STDOUT == 1 and Check_STDERR == 0):
        process = subprocess.Popen(FRAMAC_Command, close_fds=True, preexec_fn=os.setpgrp, stdout=subprocess.PIPE)
    elif (Check_STDOUT == 0 and Check_STDERR == 1):
        process = subprocess.Popen(FRAMAC_Command, close_fds=True, preexec_fn=os.setpgrp, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(FRAMAC_Command, close_fds=True, preexec_fn=os.setpgrp)
    return process


def get_result_type(context_bytes):
    # Convert from bytes to a list of strings (split by newline characters).
    result_type = "UK"
    try:
        context_strings = context_bytes.decode("utf-8")
        context_io = io.StringIO(context_strings)
        context = context_io.readlines()
    except:
        return result_type
    
    # Iterate through each line in the context.
    timeout_in_requires = 0
    for line in context:
        # If the line contains the string "[kernel] Frama-C aborted:", then the
        # build is invalid.
        if "[kernel] Frama-C aborted:" in line or "[kernel] Plug-in wp aborted" in line or "[wp] Warning: No goal generated" in line or "error: invalid preprocessing directive" in line:
            result_type = "Invalid"
            break
        elif "[wp] [Timeout] typed_" in line and ("_requires (" in line or "_requires_" in line):
            timeout_in_requires += 1
            continue
        # If the line contains the string "[wp] Proved goals:", then the build
        # is valid. The number of proved goals is given in the form "x/y",
        # where x is the number of proved goals and y is the number of total
        # goals. If x == y, then the build is a pass. Otherwise, the build is
        # a fail.
        elif "[wp] Proved goals:" in line:
            proportion = line.split(":")[-1]
            left, right = proportion.split("/")
            left = left.strip()
            right = right.strip()
            if int(left) + int(timeout_in_requires) == int(right):
                result_type = "Pass_" + left + "_" + right
            else:
                result_type = "Fail_" + left + "_" + right
            break

    return result_type


def run_framac_syntax_check(Output_folder, gfile):
    """Parse C and ACSL before launching the more expensive WP proof phase."""
    target_path = os.path.join(Output_folder, gfile)
    command = [
        "frama-c",
        "-cpp-command",
        DEFAULT_FRAMAC_CPP_COMMAND,
        "-kernel-warn-key",
        "annot-error=abort",
        target_path,
    ]
    logging.info("[CMD] Syntax check `" + " ".join(command) + "`")
    completed = subprocess.run(command, capture_output=True, timeout=SubprocessTimeout)
    output = (completed.stdout or b"") + (completed.stderr or b"")
    failed = completed.returncode != 0 or b"[kernel:annot-error]" in output or b"Frama-C aborted" in output
    if not failed:
        return None

    stem, _ = os.path.splitext(gfile)
    marker_path = os.path.join(Output_folder, stem + "_Invalid.txt")
    with open(marker_path, "wb") as marker:
        marker.write(output or b"Frama-C syntax check failed before WP.\n")
    return marker_path

def run_framac_with_wp(Output_folder, gfile, time_out = None, target_function = None):
    starttime = datetime.datetime.now()
    if time_out is None:
        time_out = int(os.getenv("AUTOSPEC_WP_GOAL_TIMEOUT", "8"))
    wp_provers = os.getenv("AUTOSPEC_WP_PROVERS", "Alt-Ergo,Z3")
    syntax_error_path = run_framac_syntax_check(Output_folder, gfile)
    if syntax_error_path is not None:
        solve_time = datetime.datetime.now() - starttime
        return "Invalid", syntax_error_path, "", solve_time

    FRAMAC_Command = [
        "frama-c",
        "-cpp-command",
        DEFAULT_FRAMAC_CPP_COMMAND,
        "-wp",
        "-wp-rte",
        "-wp-precond-weakening",
        "-wp-prover",
        wp_provers,
        "-wp-print",
        "-wp-timeout",
        str(time_out),
    ]
    if target_function:
        FRAMAC_Command.extend(["-wp-fct", target_function])
    FRAMAC_Command.append(os.path.join(Output_folder, gfile))
    
    # create subprocess according to the value of check_STDOUT and check_STDERR
    process = create_FRAMAC_subprocess(FRAMAC_Command, Check_STDOUT, Check_STDERR)
    logging.info("[CMD] Running `" + ' '.join(FRAMAC_Command) + "`")

    output_std_file_name = ""
    output_err_file_name = ""
    output_result_type = ""
    try:
        # join subprocess
        if Check_STDOUT == 1 or Check_STDERR == 1:
            stdoutdata, stderrdata = process.communicate(timeout=SubprocessTimeout)
            fleft, fright = gfile.split(".")
            fright = "." + fright
            if stdoutdata != b'':
                result_type = get_result_type(stdoutdata)
                output_result_type = result_type
                fleft = fleft.replace("_gen_", "_fstd_")
                fstd_file_name = fleft + "_" + result_type
                output_std_file_name = os.path.join(Output_folder, fstd_file_name + ".txt")
                with open (output_std_file_name, "wb") as stdfile:
                    #stdfile.write(bytes(str(pattern)+"\n", encoding = "utf8"))
                    stdfile.write(stdoutdata)
            if stderrdata != b'':
                fleft = fleft.replace("_gen_", "_ferr_")
                output_err_file_name = os.path.join(Output_folder, fleft + ".txt")
                with open (output_err_file_name, "wb") as errfile:
                    errfile.write(stderrdata)
        else:
            process.communicate(timeout=SubprocessTimeout)
    
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        output_result_type = "Timeout"
        logging.error("Timeout for subprocess when running frama-c on " + os.path.join(Output_folder, gfile))
    
    except Exception as e:
        print("\033[34m\tUnknown Exception" + "\033[0m")
        print(e)
        raise e
    endtime = datetime.datetime.now()
    solve_time = endtime - starttime
    return output_result_type, output_std_file_name, output_err_file_name, solve_time
