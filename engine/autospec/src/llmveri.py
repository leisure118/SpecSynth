#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys, re
import logging
import pickle
import copy
import subprocess
from itertools import combinations
from typing import List
from .framac import *
from .baselib import *
from .simplify_acsl import *
from .prompt.prompt import *

current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(current_path)))
from engine.llm_clients.qwencore import *

SHOT_NUM = 3
N_CHOICES = 8

ACSL_RESERVED_IDENTIFIERS = {
    "requires",
    "ensures",
    "assigns",
    "behavior",
    "behaviors",
    "assumes",
    "complete",
    "disjoint",
    "loop",
    "invariant",
    "variant",
    "integer",
    "nothing",
    "true",
    "false",
    "result",
    "old",
    "at",
    "forall",
    "exists",
    "valid",
    "valid_read",
    "separated",
    "null",
    "initialized",
    "subset",
    "union",
    "inter",
    "offset",
    "base_addr",
}

ACSL_CLAUSE_PREFIXES = (
    "requires ", "ensures ", "assigns ",
    "loop invariant ", "loop assigns ", "loop variant ",
)


def normalize_candidate_spec_line(raw_line):
    line = raw_line.strip()
    if line == "":
        return None

    for token in ("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/", ">>> INFILL <<<"):
        if token in line:
            return None

    line = line.replace("/* @", "").replace("/*@", "").replace("*/", "")
    if line in {"/*", "@", "};", ";"}:
        return None
    if line.startswith("//"):
        return None
    if line.startswith("@ "):
        line = line.replace("@ ", "", 1)
    if line.startswith("@"):
        line = line[1:].strip()
    if line == "":
        return None
    # Never turn prose or a repeated C declaration into an ACSL clause.
    # This is especially important for merged projects, where an LLM can copy
    # the signature of a distant function into the current infill location.
    if not line.startswith(ACSL_CLAUSE_PREFIXES):
        return None
    if not line.endswith(";"):
        line = line + ";"

    invalid_tokens = {"*/;", "/*;", "/* @;", "/*@;", "/**;", "{;", "};"}
    if line in invalid_tokens:
        return None

    return line


def format_acsl_operator_spacing(spec_line):
    """Normalize comparison spacing without corrupting ACSL/C pointer access."""
    protected_tokens = {
        "<==>": "__ACSL_EQUIVALENCE__",
        "==>": "__ACSL_IMPLIES__",
        "->": "__ACSL_POINTER_ARROW__",
    }
    formatted = spec_line
    for token, placeholder in protected_tokens.items():
        formatted = formatted.replace(token, placeholder)
    for operator in ("==", "<=", ">=", "<", ">"):
        if operator in formatted:
            formatted = re.sub(rf"\s*{re.escape(operator)}\s*", f" {operator} ", formatted)
            break
    for token, placeholder in protected_tokens.items():
        formatted = formatted.replace(placeholder, token)
    return re.sub(r" {2,}", " ", formatted)


def strip_generated_acsl_wrapper(reply):
    """Return clauses only; the infill marker already supplies the ACSL wrapper."""
    cleaned = reply.replace("```c;", "").replace("```c", "").replace("```;", "").replace("```", "")
    cleaned = re.sub(r"^\s*/\*\s*@?\s*", "", cleaned, count=1)
    cleaned = re.sub(r"\s*@?\s*\*/\s*$", "", cleaned, count=1)
    return cleaned.strip()


def remove_nullable_behavior_conflicts(reply):
    """Drop global dereference clauses that contradict an explicit null behavior."""
    lines = reply.splitlines()
    first_behavior = next((i for i, line in enumerate(lines) if line.strip().startswith("behavior ")), None)
    if first_behavior is None:
        return reply
    behavior_text = "\n".join(lines[first_behavior:])
    null_match = re.search(r"assumes\s+([A-Za-z_]\w*)\s*==\s*\\null\s*;", behavior_text)
    if null_match is None:
        return reply
    pointer_name = null_match.group(1)
    valid_pattern = re.compile(rf"^requires\s+\\valid\s*\(\s*{re.escape(pointer_name)}\s*\)\s*;$")
    dereference_pattern = re.compile(rf"^ensures\s+.*\b{re.escape(pointer_name)}\s*->")
    prefix = [
        line for line in lines[:first_behavior]
        if not valid_pattern.match(line.strip()) and not dereference_pattern.match(line.strip())
    ]
    return "\n".join(prefix + lines[first_behavior:]).strip()


def add_nullable_global_validity_guard(reply):
    """Make a nullable behavior contract sufficient for WP-RTE memory proofs.

    A validity requirement nested only inside the non-null behavior is enough
    to describe that behavior, but WP-RTE proves the function body from global
    preconditions.  Promote the conditional validity fact to a global guard so
    a checked dereference after ``if (!ptr) return`` does not time out.
    """
    lines = reply.splitlines()
    behavior_text = "\n".join(lines)
    null_match = re.search(r"assumes\s+([A-Za-z_]\w*)\s*==\s*\\null\s*;", behavior_text)
    if null_match is None:
        return reply
    pointer_name = null_match.group(1)
    valid_pattern = re.compile(
        rf"requires\s+\\valid\s*\(\s*{re.escape(pointer_name)}\s*\)\s*;"
    )
    if valid_pattern.search(behavior_text) is None:
        return reply
    guard = f"requires {pointer_name} == \\null || \\valid({pointer_name});"
    if any(line.strip() == guard for line in lines):
        return reply
    return "\n".join([guard] + lines).strip()


def target_function_returns_void(question):
    """Whether the function associated with the infill marker returns void."""
    marker_index = next(
        (question.find(token) for token in ("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/", ">>> INFILL <<<") if question.find(token) >= 0),
        -1,
    )
    if marker_index < 0:
        return False
    tail = question[marker_index:]
    signature = re.search(
        r"(?:^|\n)\s*(?P<return_type>(?:static\s+|inline\s+|const\s+)*void)\s+"
        r"[A-Za-z_]\w*\s*\([^;{}]*\)\s*\{",
        tail,
        re.MULTILINE,
    )
    return signature is not None


def sanitize_contract_reply(reply, question):
    """Remove clauses that are structurally invalid for the target contract."""
    cleaned = strip_generated_acsl_wrapper(reply)
    cleaned = remove_nullable_behavior_conflicts(cleaned)
    cleaned = add_nullable_global_validity_guard(cleaned)
    if target_function_returns_void(question):
        cleaned = "\n".join(line for line in cleaned.splitlines() if "\\result" not in line)
    return cleaned.strip()


def spec_has_user_function_call(spec_line):
    lowered = spec_line.replace("\\valid", "").replace("\\forall", "").replace("\\exists", "").replace("\\old", "")
    return re.search(r"\b[a-zA-Z_]\w*\s*\(", lowered) is not None


def extract_target_function_signature(question):
    marker_candidates = ("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/", ">>> INFILL <<<")
    marker_index = -1
    marker_token = ""
    for candidate in marker_candidates:
        marker_index = question.find(candidate)
        if marker_index != -1:
            marker_token = candidate
            break

    if marker_index == -1:
        return None, []

    tail = question[marker_index + len(marker_token):]
    signature_match = re.search(
        r"(?:^|\n)\s*(?:[A-Za-z_]\w*[\s\*]+)+(?P<func>[A-Za-z_]\w*)\s*\((?P<params>[^)]*)\)\s*\{",
        tail,
        re.MULTILINE,
    )
    if signature_match is None:
        return None, []

    func_name = signature_match.group("func")
    params_str = signature_match.group("params").strip()
    if params_str in {"", "void"}:
        return func_name, []

    allowed_names = []
    for raw_param in params_str.split(","):
        param = raw_param.strip()
        if param == "" or param == "void":
            continue
        param = re.sub(r"\[[^\]]*\]", "", param)
        name_match = re.search(r"([A-Za-z_]\w*)\s*$", param)
        if name_match is not None:
            allowed_names.append(name_match.group(1))
    return func_name, allowed_names


def extract_target_function_identifiers(question):
    """Return lexical identifiers from the function containing the infill marker."""
    marker_index = next(
        (question.find(token) for token in ("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/", ">>> INFILL <<<") if question.find(token) >= 0),
        -1,
    )
    if marker_index < 0:
        return set()
    pattern = re.compile(
        r"(?:^|\n)\s*(?:[A-Za-z_]\w*[\s\*]+)+[A-Za-z_]\w*\s*\([^;{}]*\)\s*\{",
        re.MULTILINE,
    )
    ranges = []
    for match in pattern.finditer(question):
        brace = question.find("{", match.start(), match.end())
        depth = 0
        end = len(question)
        for index in range(brace, len(question)):
            if question[index] == "{":
                depth += 1
            elif question[index] == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        ranges.append((match.start(), end))
    target = next(((start, end) for start, end in ranges if start <= marker_index < end), None)
    if target is None:
        target = next(((start, end) for start, end in ranges if start > marker_index), None)
    if target is None:
        return set()
    return set(re.findall(r"\b[A-Za-z_]\w*\b", question[target[0]:target[1]]))


def extract_loop_body_local_identifiers(question):
    """Return locals declared after a loop infill marker.

    Such variables are not in scope at the loop annotation, even though they
    occur inside the containing function (for example ``int ret`` declared in
    the loop body).
    """
    marker_index = next(
        (question.find(token) for token in ("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/", ">>> INFILL <<<") if question.find(token) >= 0),
        -1,
    )
    if marker_index < 0:
        return set()
    tail = question[marker_index:]
    declaration_pattern = re.compile(
        r"(?m)(?:^|[;{}])\s*(?:const\s+)?(?:unsigned\s+|signed\s+)?"
        r"(?:char|short|int|long|float|double|u8|u16|u32|u64|s8|s16|s32|s64|size_t)"
        r"(?:\s+|\s*\*\s*)([A-Za-z_]\w*)\s*(?:[=;,])"
    )
    return set(declaration_pattern.findall(tail))


def loop_spec_matches_target_scope(spec_line, target_identifiers):
    if not spec_line.startswith("loop ") or not target_identifiers:
        return True
    scrubbed = re.sub(r"(?:->|\.)\s*[A-Za-z_]\w*", "", spec_line)
    for identifier in extract_candidate_identifiers(scrubbed):
        if identifier in ACSL_RESERVED_IDENTIFIERS or identifier in target_identifiers:
            continue
        if identifier.isupper():
            continue
        if identifier in {"i", "j", "k", "m", "n", "p", "q"} and ("\\forall" in spec_line or "\\exists" in spec_line):
            continue
        return False
    return True


def candidate_matches_task_type(spec_line, gpt_task):
    if gpt_task in (1, 3):
        return spec_line.startswith(("loop invariant ", "loop assigns ", "loop variant "))
    if gpt_task in (2, 4):
        return spec_line.startswith(("requires ", "assigns ", "ensures "))
    return True


def response_uses_named_behaviors(reply):
    """Detect structured behaviors before standalone-clause normalization."""
    return bool(re.search(
        r"(?m)^\s*(?:behavior\s+[A-Za-z_]\w*\s*:|assumes\s+)", reply
    ))


def extract_target_function_name(question):
    marker_index = next(
        (question.find(token) for token in ("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/", ">>> INFILL <<<") if question.find(token) >= 0),
        -1,
    )
    if marker_index < 0:
        return None
    pattern = re.compile(
        r"(?:^|\n)\s*(?:[A-Za-z_]\w*[\s\*]+)+(?P<func>[A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(question))
    for match in reversed([item for item in matches if item.start() <= marker_index]):
        brace = question.find("{", match.start(), match.end())
        depth = 0
        for index in range(brace, len(question)):
            depth += question[index] == "{"
            depth -= question[index] == "}"
            if depth == 0:
                if marker_index < index:
                    return match.group("func")
                break
    following = next((item for item in matches if item.start() > marker_index), None)
    return following.group("func") if following else None


def extract_candidate_identifiers(spec_line):
    scrubbed = spec_line
    for token in ("\\forall", "\\exists", "\\valid_read", "\\valid", "\\old", "\\result", "\\nothing", "\\null"):
        scrubbed = scrubbed.replace(token, " ")
    return re.findall(r"\b[A-Za-z_]\w*\b", scrubbed)


def contract_matches_target_scope(spec_line, allowed_param_names):
    if not (spec_line.startswith("requires ") or spec_line.startswith("ensures ") or spec_line.startswith("assigns ")):
        return True

    allowed = set(allowed_param_names)
    for identifier in extract_candidate_identifiers(spec_line):
        if identifier in ACSL_RESERVED_IDENTIFIERS:
            continue
        if identifier.isupper():
            continue
        if identifier in {"i", "j", "k", "m", "n", "p", "q"} and ("\\forall" in spec_line or "\\exists" in spec_line):
            continue
        if identifier in allowed:
            continue
        return False
    return True


def should_keep_candidate_spec(spec_line):
    if spec_line.count(";") != 1:
        return False
    if "loop assigns \\nothing;" in spec_line:
        return False
    if spec_line.startswith("loop invariant ") and spec_has_user_function_call(spec_line):
        return False
    if spec_line.startswith("loop invariant ") and spec_line.count("\\exists") > 1:
        return False
    if " ==> " in spec_line and " <==> " in spec_line:
        return False
    return True


def score_candidate_spec(spec_line):
    score = 0
    if spec_line.startswith("requires "):
        score += 100
    elif spec_line.startswith("ensures "):
        score += 90
    elif spec_line.startswith("loop variant "):
        score += 85
    elif spec_line.startswith("loop invariant 0 <=") or spec_line.startswith("loop invariant 0<="):
        score += 80
    elif spec_line.startswith("loop invariant ") and "==" in spec_line:
        score += 70
    elif spec_line.startswith("loop invariant ") and "\\forall" in spec_line:
        score += 60
    elif spec_line.startswith("loop invariant "):
        score += 50
    elif spec_line.startswith("loop assigns "):
        score += 20
    elif spec_line.startswith("assigns "):
        score += 10
    if spec_has_user_function_call(spec_line):
        score -= 40
    if "\\exists" in spec_line:
        score -= 10
    if " || " in spec_line:
        score -= 5
    score -= len(spec_line) / 1000
    return score


def sort_candidate_specs(spec_list):
    return sorted(spec_list, key=lambda item: (-score_candidate_spec(item), item))


def prune_candidate_specs(spec_list):
    requirements = []
    postconditions = []
    invariants = []
    variants = []
    loop_assigns_specs = []
    assigns_specs = []
    other_specs = []

    for each_spec in sort_candidate_specs(list(dict.fromkeys(spec_list))):
        if not should_keep_candidate_spec(each_spec):
            continue
        if each_spec.startswith("requires "):
            requirements.append(each_spec)
        elif each_spec.startswith("ensures "):
            postconditions.append(each_spec)
        elif each_spec.startswith("loop variant "):
            variants.append(each_spec)
        elif each_spec.startswith("loop invariant "):
            invariants.append(each_spec)
        elif each_spec.startswith("loop assigns "):
            loop_assigns_specs.append(each_spec)
        elif each_spec.startswith("assigns "):
            assigns_specs.append(each_spec)
        else:
            other_specs.append(each_spec)

    selected_invariants = []
    quantified_count = 0
    existential_count = 0
    for each_spec in invariants:
        if "\\forall" in each_spec or "\\exists" in each_spec:
            if quantified_count >= 2:
                continue
            quantified_count += 1
        if "\\exists" in each_spec:
            if existential_count >= 1:
                continue
            existential_count += 1
        selected_invariants.append(each_spec)
        if len(selected_invariants) >= 6:
            break

    selected_requirements = requirements[:4]
    selected_postconditions = postconditions[:4]
    selected_variants = variants[:2]
    selected_loop_assigns = loop_assigns_specs[:4]
    selected_assigns = assigns_specs[:2]

    # ACSL requires assigns/allocates clauses to precede postconditions.
    return selected_requirements + selected_assigns + selected_postconditions + selected_variants + selected_invariants + selected_loop_assigns + other_specs[:2]


def build_target_focused_prompt(source, radius=24000):
    """Limit LLM context while retaining the full source for later insertion."""
    markers = ("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/", ">>> INFILL <<<")
    marker_index = next((source.find(marker) for marker in markers if source.find(marker) >= 0), -1)
    if marker_index < 0 or len(source) <= radius * 2:
        return source
    start = max(0, marker_index - radius)
    end = min(len(source), marker_index + radius)
    return (
        "The following is a target-focused slice of a larger merged C project. "
        "Generate clauses only for the function or loop at the INFILL marker. "
        "Do not repeat any C declaration or refer to identifiers outside this slice.\n\n"
        + source[start:end]
    )


def determine_veri_clang():
    # check veri-clang --version exists
    if os.system("veri-clang --version") != 0:
        print("====================================")
        print("veri-clang --version not exists")
        print("please install veri-clang, and config the ENV by 'source ./scripts/requires/init_env.sh'\n")
        sys.exit(2)
    else:
        pass


def AutoGenInfillFile(GPT_File, Output_folder):
    # if supported file not exist, create it
    if not (os.path.exists(GPT_File + ".pickle")):
        # print("---------------------generate pickle file---------------------")
        determine_veri_clang()
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run([sys.executable, os.path.join(parent_path, "mark.py"), "-f", GPT_File], check=True)
    
    # spit file_name from last '/' and get the prefix and suffix
    prefix_str, mfName, suffix_str = split_file_name(GPT_File)
    new_infilled_file = prefix_str + mfName + "_infilled" + suffix_str

    # The value of cur_task is either 'contract' or 'loop'
    cur_task = "contract_gen"

    # Load the pickle
    with open(GPT_File + ".pickle", "rb") as data:
        
        SAVE_PICKLE = pickle.load(data)
        MSLines = SAVE_PICKLE['MSLines']
        InfillLines = get_infill_lines(SAVE_PICKLE)

        # if complete
        if SAVE_PICKLE['Status'] == 1:
            write_into_final_c_file(Output_folder, mfName, suffix_str, InfillLines)
            logging.info("The verification task has been completed. Please check the output folder\n")
            sys.exit(1)
        
        # Write into Another New file with the "_marked" suffix
        write_into_marked_c_file(prefix_str, mfName, suffix_str, MSLines)
        
        # Write into Another New file with the "_infilled" suffix
        write_into_infilled_c_file(prefix_str, mfName, suffix_str, InfillLines, True)
    
    # get cur_task
    cur_task_id = SAVE_PICKLE['CurTaskID']
    if SAVE_PICKLE['TaskList'][cur_task_id-1] == 2 or SAVE_PICKLE['TaskList'][cur_task_id-1] == 3:
        if SAVE_PICKLE[str(cur_task_id)] == []:
            cur_task = "loopinv_gen"
        else:
            cur_task = "loopinv_infill"
    elif SAVE_PICKLE['TaskList'][cur_task_id-1] == 1:
        if SAVE_PICKLE[str(cur_task_id)] == []:
            cur_task = "contract_gen"
        else:
            cur_task = "contract_infill"
    else:
        logging.info("ERR in AutoGenInfillFile().")
        sys.exit(-1)

    existing_spec_list = SAVE_PICKLE[str(cur_task_id)]
    is_outter_loop = False
    if SAVE_PICKLE['TaskList'][cur_task_id-1] == 3:
        is_outter_loop = True

    return cur_task_id, cur_task, new_infilled_file, existing_spec_list, SAVE_PICKLE['Iteration'], is_outter_loop


# process only a single file
def query_llm_and_get_verified_result_for_single_file(GPT_File, Output_folder, GPT_Task, sys_prompt, n_choices, shot_num, model_config, enable_mutation):
    # record return value
    return_value = False
    total_solve_time = datetime.timedelta(0)
    # open the file and get strings
    gpt_file_strings = ""
    with open(GPT_File, "r") as f:
        gpt_file_strings = f.read()
    
    # retrieve relevent code
    rag_prompt = ''

    existing_spec_list = []
    if GPT_Task == 0: # Our Final Method
        cur_task_id, cur_task, new_infilled_file, existing_spec_list, iteration_times, is_outter_loop = AutoGenInfillFile(GPT_File, Output_folder)

        # continue the alg. based on cur_task
        if cur_task == "loopinv_gen":
            GPT_Task = 1
        elif cur_task == "contract_gen":
            GPT_Task = 2
        elif cur_task == "loopinv_infill":
            GPT_Task = 3
        elif cur_task == "contract_infill":
            GPT_Task = 4
        else:
            logging.info("ERR in query_llm_and_get_verified_result_for_single_file().")
            sys.exit(-1)

        # update gpt_file_strings from new_infilled_file
        with open(new_infilled_file, "r") as f:
            gpt_file_strings = f.read()

    if GPT_Task == 1: # loopinv gen
            chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('loop_inv_gen', sys_prompt, rag_prompt))
    elif GPT_Task == 2: # contract gen
            chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('contract_gen', sys_prompt, rag_prompt))
    elif GPT_Task == 3: # loopinv infill
            chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('loop_inv_infill', sys_prompt, rag_prompt))
    elif GPT_Task == 4: # contract infill
            chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('contract_infill', sys_prompt, rag_prompt))
    elif GPT_Task == 5: # normal
        chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('normal', sys_prompt, rag_prompt, shot_num))
    elif GPT_Task == 6: # loop
        chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('loop', sys_prompt, rag_prompt))
    else:
        raise Exception("Error: GPT_Task is not correct: " + str(GPT_Task))
        

    # set user prompt as question
    if shot_num == 0:
        question = verification_prompt_template.replace("<The code I give you>", gpt_file_strings)
    elif shot_num >= 1:
        question = gpt_file_strings
    else:
        raise Exception("Error: shot_num is not correct: " + str(shot_num))

    logging.info(f"\U0001f47b: {question}\n")
    
    # query LLMs
    llms_start_time = datetime.datetime.now()
    temperature_arg = 0.7 + iteration_times*0.1
    if temperature_arg >= 1.0:
        temperature_arg = 1.0
    
    llm_question = build_target_focused_prompt(question)
    full_reply_content_list, tokens_usage = chatveri.get_respone(
        llm_question,
        temperature_arg=temperature_arg, 
        n_choices = n_choices
    )

    print("==============================================")
    # print(len(full_reply_content_list))
    for i in range(len(full_reply_content_list)):
        if GPT_Task in (2, 4):
            full_reply_content_list[i] = sanitize_contract_reply(full_reply_content_list[i], question)
        else:
            full_reply_content_list[i] = strip_generated_acsl_wrapper(full_reply_content_list[i])
        print(f"\U0001f47D: {full_reply_content_list[i]}\n")
    print("==============================================")
    llms_end_time = datetime.datetime.now()
    logging.info(f"total_tokens: {tokens_usage}\n")
    llms_query_times = llms_end_time - llms_start_time
    logging.info(f"llm_time_sec: {llms_query_times.total_seconds():.6f}\n")



    # 拿到LLM的结果，开始进行验证
    # GPT_File.split on last "."
    try:
        filesuffix = GPT_File.split("/")[-1]
        GPT_File_left, GPT_File_right = filesuffix.split(".")
        GPT_File_right = '.' + GPT_File_right
    except Exception as e:
        logging.error(e)
        sys.exit(-1)

    cur_index = 0
    generated_file_list = []
    generated_acsl_spec_list = []
    generated_acsl_spec_set = set()
    merged_file_ori = GPT_File_left + "_merged_ori" + GPT_File_right
    merged_file = GPT_File_left + "_merged" + GPT_File_right
    loop_assigns_check_file = GPT_File_left + "_loop_assigns" + GPT_File_right
    
    if GPT_Task == 1 or GPT_Task == 2 or GPT_Task == 3 or GPT_Task == 4:
        # find the index of infill location
        infill_str_prefix = ""
        # Function-contract markers sit immediately before their target, while
        # loop markers are located inside their containing function.  Use the
        # marker-aware resolver for the WP target in both cases.
        _, target_param_names = extract_target_function_signature(question)
        target_func_name = extract_target_function_name(question)
        target_identifiers = extract_target_function_identifiers(question)
        if GPT_Task == 1 or GPT_Task == 3:
            target_identifiers -= extract_loop_body_local_identifiers(question)

        for each_line in question.split("\n"):
            if "/* @ >>> INFILL <<< */" in each_line:
                infill_str_prefix = each_line.replace("/* @ >>> INFILL <<< */", "")
                break
            elif ">>> INFILL <<<" in each_line:
                infill_str_prefix = each_line.replace(">>> INFILL <<<", "")
                break
        
        for each_reply in full_reply_content_list:
            saved_file = GPT_File_left + "_gen_" + str(cur_index) + GPT_File_right
            generated_file_list.append(saved_file)
            
            # gather acsl spec
            for each_spec in each_reply.split("\n"):
                each_spec = normalize_candidate_spec_line(each_spec)
                if each_spec is None:
                    continue
                if not candidate_matches_task_type(each_spec, GPT_Task):
                    continue
                    
                # split loop assigns
                if "loop assigns " in each_spec:
                    if "unknown1" in each_spec or "unknown2" in each_spec or "unknown3" in each_spec or "unknown4" in each_spec:
                        continue
                    each_spec = each_spec.replace(", ", ",")
                    if "," in each_spec:
                        strip_multi_var = each_spec.replace("loop assigns ", "").replace(";", "").strip()
                        for each_var in strip_multi_var.split(","):
                            tmp_spec = "loop assigns " + each_var + ";"
                            if tmp_spec not in existing_spec_list:
                                generated_acsl_spec_set.add(tmp_spec)
                    else:
                        generated_acsl_spec_set.add(each_spec)
                else:        
                    if "UNINITIALIZED" in each_spec:
                        continue
                    elif "unknown1()" in each_spec or "unknown2()" in each_spec or "unknown3()" in each_spec or "unknown4()" in each_spec:
                        continue
                    elif "inner loop " in each_spec:
                        each_spec = each_spec.replace("inner loop ", "loop ")
                    
                    # Format comparisons while preserving pointer member access (`->`).
                    each_spec = format_acsl_operator_spacing(each_spec)

                    # replace space
                    if ' ;' in each_spec:
                        each_spec = each_spec.replace(' ;', ';')
                    
                    # remove '
                    if "' " in each_spec:
                        each_spec = each_spec.replace("' ", " ")
                                        
                    # change order of inequality
                    if each_spec.startswith("loop invariant ") and is_inequality(each_spec):
                        ine_spec = each_spec.replace("loop invariant ", "").strip()
                        inequality_list = inequality_segmentation(ine_spec)
                        for each_ine in inequality_list:
                            loop_inv_spec = "loop invariant " + each_ine + ';'
                            if loop_inv_spec not in existing_spec_list:
                                generated_acsl_spec_set.add(loop_inv_spec)
                        continue

                    if GPT_Task == 2 or GPT_Task == 4:
                        if not contract_matches_target_scope(each_spec, target_param_names):
                            continue
                    elif GPT_Task == 1 or GPT_Task == 3:
                        if not loop_spec_matches_target_scope(each_spec, target_identifiers):
                            continue
                    
                    # add to set
                    if each_spec not in existing_spec_list and each_spec.strip() != ";":
                        generated_acsl_spec_set.add(each_spec)
            
            # fill the infill location with prefix
            each_reply_str = '\n' + each_reply.strip()
            if not each_reply_str.endswith("\n"):
                each_reply_str = each_reply_str + "\n"
            each_reply_str = each_reply_str.replace("\n", "\n" + infill_str_prefix)
            
            # write to file
            with open(os.path.join(Output_folder, saved_file), "w") as f:
                if ">>> INFILL <<<\n" in question:
                    f.write(question.replace(">>> INFILL <<<\n" + infill_str_prefix, each_reply_str.replace('\n'+infill_str_prefix, '', 1)))
                else:
                    f.write(question
                        .replace("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/")
                        .replace(">>> INFILL <<<", each_reply_str)
                        )

            cur_index += 1
    
        # generated_acsl_spec_list: from set to list
        generated_acsl_spec_list = prune_candidate_specs(list(generated_acsl_spec_set))
        

        # Load SAVE_PICKLE
        fdata = open(GPT_File + ".pickle", "rb")
        SAVE_PICKLE = pickle.load(fdata)
        # enable mutation
        if SAVE_PICKLE['Iteration'] == 3 or SAVE_PICKLE['Iteration'] == 4:
            enable_mutation = True
        elif SAVE_PICKLE['Iteration'] >= 5:
            enable_mutation = False
        fdata.close()

        # =============mutation begins=============
        # if enable mutation (wcventure)
        selected_inequality_list = []
        partial_order_reinforcement_list = []
        inequality_mutation_list = []
        if enable_mutation:
            for each_spec in generated_acsl_spec_list:
                if is_inequality(each_spec):
                    print(each_spec)
                    selected_inequality_list.append(each_spec.replace(";", "").replace("loop invariant ", "").strip())
                    if " > " in each_spec and " >= " not in each_spec and " < " not in each_spec and " <= " not in each_spec:
                        partial_order_reinforcement_list.append(each_spec.replace(" > ", " >= ").strip())
                    elif " >= " in each_spec and " > " not in each_spec and " < " not in each_spec and " <= " not in each_spec:
                        partial_order_reinforcement_list.append(each_spec.replace(" >= ", " > ").strip())
                    elif " < " in each_spec and " <= " not in each_spec and " > " not in each_spec and " >= " not in each_spec:
                        partial_order_reinforcement_list.append(each_spec.replace(" < ", " <= ").strip())
                    elif " <= " in each_spec and " < " not in each_spec and " > " not in each_spec and " >= " not in each_spec:
                        partial_order_reinforcement_list.append(each_spec.replace(" <= ", " < ").strip())
            
            if SAVE_PICKLE['Iteration'] == 3:
                for each_item in SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])]:
                    if is_inequality(each_spec):
                        if " > " in each_spec and " >= " not in each_spec and " < " not in each_spec and " <= " not in each_spec:
                            partial_order_reinforcement_list.append(each_spec.replace(" > ", " >= ").strip())
                        elif " >= " in each_spec and " > " not in each_spec and " < " not in each_spec and " <= " not in each_spec:
                            partial_order_reinforcement_list.append(each_spec.replace(" >= ", " > ").strip())
                        elif " < " in each_spec and " <= " not in each_spec and " > " not in each_spec and " >= " not in each_spec:
                            partial_order_reinforcement_list.append(each_spec.replace(" < ", " <= ").strip())
                        elif " <= " in each_spec and " < " not in each_spec and " > " not in each_spec and " >= " not in each_spec:
                            partial_order_reinforcement_list.append(each_spec.replace(" <= ", " < ").strip())
                    
            if selected_inequality_list != []:
                # get combinations
                inequality_mutation_list = list(combinations(selected_inequality_list, 2))
                # get union
                for each_ineq in inequality_mutation_list:
                    generated_acsl_spec_list.append("loop invariant " + each_ineq[0] + " || " + each_ineq[1] + ";")
            
            if partial_order_reinforcement_list != []:
                for each_ineq in partial_order_reinforcement_list:
                    generated_acsl_spec_list.append(each_ineq)

        del selected_inequality_list, inequality_mutation_list
        # =============mutation ends=============

        # remove repetitive specifications
        for each_item in SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])]:
            if each_item in generated_acsl_spec_list:
                generated_acsl_spec_list.remove(each_item)
        generated_acsl_spec_list = prune_candidate_specs(generated_acsl_spec_list)

        # Validate loop assigns together with the complete candidate below.
        # The former implementation launched Frama-C once per assigns clause
        # (and sometimes once per pair) before immediately verifying the full
        # candidate again.  One complete WP run provides the same acceptance
        # decision and lets the normal simplifier reject bad annotations.
        if GPT_Task == 1 or GPT_Task == 3:
            loop_assigns_count = sum(
                each_spec.startswith("loop assigns ")
                for each_spec in generated_acsl_spec_list
            )
            if loop_assigns_count:
                print(
                    "validate loop assigns with complete candidate =",
                    loop_assigns_count,
                )



        # ================tricks begins================
        if "bubble" in GPT_File or "bufs_differ" in GPT_File or "parse_null" in GPT_File or "parse_algoid_params" in GPT_File:
            if GPT_Task == 1 or GPT_Task == 3:
                print(generated_acsl_spec_list)
                for each_spec in generated_acsl_spec_list:
                    if is_outter_loop == False:
                        if "loop assigns a[0..n-1]" in each_spec or "loop assigns a[0..n]" in each_spec or "loop assigns i" in each_spec or "loop assigns a[0..i-1]" in each_spec:
                            generated_acsl_spec_list.remove(each_spec)
                    elif is_outter_loop == True:
                        if "loop assigns a[0..i];" in each_spec or "loop assigns a[0..i-1];" in each_spec :
                            generated_acsl_spec_list.remove(each_spec)
                        elif ("bufs_differ" in GPT_File or "parse_null" in GPT_File or "parse_algoid_params" in GPT_File) and ("loop assigns ret;" in each_spec or "loop assigns b1[0..n-1];" in each_spec or "loop assigns b2[0..n-1];" in each_spec or "loop assigns n;" in each_spec or "loop assigns b1;" in each_spec or "loop assigns b2;" in each_spec):
                            generated_acsl_spec_list.remove(each_spec)
                if is_outter_loop == False:
                    if "loop assigns a[0..i];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns a[0..i];")
                    if "loop invariant 0 <= j;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop invariant 0 <= j;")
                    if "loop invariant j <= i;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop invariant j <= i;")
                elif is_outter_loop == True:
                    if "loop assigns a[0..n-1];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns a[0..n-1];")
                    if "loop assigns i;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns i;")
                    if "loop assigns j;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns j;")
                    if "loop assigns temp;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns temp;")
                    if "loop invariant i < n;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop invariant i < n;")
                    if "loop invariant \\forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop invariant \\forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];")
            elif GPT_Task == 2 or GPT_Task == 4:
                if "bufs_differ" in GPT_File or "parse_null" in GPT_File or "parse_algoid_params" in GPT_File:
                    for i in range(0, len(generated_acsl_spec_list)):
                        if " ==> " in generated_acsl_spec_list[i]:
                            generated_acsl_spec_list[i] = generated_acsl_spec_list[i].replace(" ==> \\exists", " <==> \\exists").replace(" ==> \\forall", " <==> \\forall")
                if "parse_null" in GPT_File:
                    if "ensures \\result == 0 <==> \\forall integer i; 0 <= i < n ==> b1[i] == b2[i];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("ensures \\result == 0 <==> \\forall integer i; 0 <= i < n ==> b1[i] == b2[i];")
                    if "ensures \\result == 1 <==> \\exists integer i; 0 <= i < n && b1[i] != b2[i];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("ensures \\result == 1 <==> \\exists integer i; 0 <= i < n && b1[i] != b2[i];")
        # ================tricks ends================



        # sort list
        generated_acsl_spec_list = prune_candidate_specs(generated_acsl_spec_list)
        # print(generated_acsl_spec_list)

        # Do not materialize an empty ACSL block (`/*@ */`). Frama-C treats it
        # as an invalid annotation. Keep the current task active and let the
        # next repair iteration request a task-compatible candidate instead.
        if generated_acsl_spec_list == []:
            with open(GPT_File + ".pickle", "rb") as fdata:
                failed_metrics = pickle.load(fdata)
            failed_metrics['llms_query_times'] += llms_query_times
            failed_metrics['total_solve_time'] += total_solve_time
            failed_metrics['tokens_usage'] += tokens_usage
            failed_metrics['Iteration'] += 1
            with open(GPT_File + ".pickle", "wb") as output:
                pickle.dump(failed_metrics, output)
            logging.warning("No task-compatible ACSL clauses; skipped empty annotation.")
            return False, llms_query_times, total_solve_time, tokens_usage

        # fill the infill location with prefix
        merge_spec_str = "\n"
        for each_spec in generated_acsl_spec_list:
            if each_spec.strip() == "":
                continue
            merge_spec_str = merge_spec_str + infill_str_prefix + each_spec.strip() + "\n"
        merge_spec_str = merge_spec_str + infill_str_prefix

        #write to file
        with open(os.path.join(Output_folder, merged_file_ori), "w") as f:
            f.write(question
                    .replace("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/")
                    .replace("\n" + infill_str_prefix + ">>> INFILL <<<\n" + infill_str_prefix, merge_spec_str)
                    .replace(">>> INFILL <<<", merge_spec_str)
                )
        with open(os.path.join(Output_folder, merged_file), "w") as f:
            f.write(question
                    .replace("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/")
                    .replace("\n" + infill_str_prefix + ">>> INFILL <<<\n" + infill_str_prefix, merge_spec_str)
                    .replace(">>> INFILL <<<", merge_spec_str)
                )
            
    # 如果gpt_task是normal或loop，则直接保存结果
    else:
        for each_reply in full_reply_content_list:
            # save to file
            saved_file = GPT_File_left + "_gen_" + str(cur_index) + GPT_File_right
            generated_file_list.append(saved_file)
            with open(os.path.join(Output_folder, saved_file), "w") as f:
                f.write(each_reply.replace("```\n", "").replace("```", ""))
            cur_index += 1

    # whether assume and behavior exist
    assume_behavior_flag = False
    if GPT_Task == 2 or GPT_Task == 4:
        # Structural behavior lines are deliberately absent from the
        # standalone clause set. Detect them in the original response so
        # mutually exclusive assigns clauses are verified as a complete block
        # instead of being flattened into a contradictory global contract.
        assume_behavior_flag = any(
            response_uses_named_behaviors(reply)
            for reply in full_reply_content_list
        )

    # call frama-c to verify
    if GPT_Task == 1 or GPT_Task == 2 or GPT_Task == 3 or GPT_Task == 4:
        ci = 0
        max_pass_goal = 0
        max_all_goal = 0
        best_target_file = ""
        verification_attempts = 0
        max_candidate_verifications = max(
            1,
            int(os.getenv("AUTOSPEC_MAX_CANDIDATE_VERIFY", "1")),
        )
        while 1:
            if verification_attempts >= max_candidate_verifications:
                print(
                    "candidate verification budget reached =",
                    max_candidate_verifications,
                )
                break
            verification_attempts += 1
            # input("Press Enter to continue...")
            if GPT_Task == 1 or GPT_Task == 3:
                target_file = merged_file
            elif GPT_Task == 2 or GPT_Task == 4:
                if assume_behavior_flag == True:
                    target_file = generated_file_list[ci]
                else:
                    target_file = merged_file

            output_result_type, output_std_file_name, output_err_file_name, solve_time = run_framac_with_wp(
                Output_folder, target_file, target_function=target_func_name
            )
            total_solve_time = solve_time + total_solve_time
            if output_result_type == "Timeout":
                with open(GPT_File + ".pickle", "rb") as fdata:
                    timeout_metrics = pickle.load(fdata)
                timeout_metrics['llms_query_times'] += llms_query_times
                timeout_metrics['total_solve_time'] += total_solve_time
                timeout_metrics['tokens_usage'] += tokens_usage
                timeout_metrics['Iteration'] += 1
                with open(GPT_File + ".pickle", "wb") as output:
                    pickle.dump(timeout_metrics, output)
                return False, llms_query_times, total_solve_time, tokens_usage
            if output_result_type == "Invalid":
                ERROR_TAG = False
                print("remove invalid spec and re-run.")
                # open output_std_file_name
                with open(output_std_file_name, "r") as f:
                    lines = f.readlines()
                    error_lead_to_invalid = False
                    I_REACH_MAX = False
                    for i in range(len(lines)):
                        print(f"output_std_file_output line{i}:", i)
                        print(lines[i], end="")
                        if "[kernel:annot-error]" in lines[i] and os.path.join(Output_folder, target_file) in lines[i]\
                            or "[kernel]" in lines[i] and os.path.join(Output_folder, target_file) in lines[i] and ("syntax error:" in lines[i+1] or "Invalid symbol:" in lines[i+1]):
                            message_in_next_line = lines[i+1]
                            if "complete or disjoint behaviors clause in a contract with empty list of behavior" in message_in_next_line:
                                if "disjoint behaviors;" in generated_acsl_spec_list:
                                    generated_acsl_spec_list.remove("")
                                elif "complete behaviors;" in generated_acsl_spec_list:
                                    generated_acsl_spec_list.remove("")
                                break
                            else:
                                _, rightstr = lines[i].split(os.path.join(Output_folder, target_file)+":",1)
                                lineNumStr, _ = rightstr.split(":",1)
                                if generated_acsl_spec_list == []:
                                    break
                                invalid_line_path = os.path.join(Output_folder, target_file)
                                with open(invalid_line_path, "r") as invalid_source:
                                    invalid_lines = invalid_source.readlines()
                                invalid_line_no = int(lineNumStr)
                                if not (0 < invalid_line_no <= len(invalid_lines)) or not is_removable_acsl_line(invalid_lines[invalid_line_no - 1]):
                                    print("skip removal of non-ACSL invalid location")
                                    ERROR_TAG = True
                                    break
                                removed_spec = remove_one_line_from_the_file(invalid_line_path, invalid_line_no)
                                print("generated_acsl_spec_list =", generated_acsl_spec_list) # (wcventure) delete
                                print("removed_spec =", removed_spec)
                                # if the spec is in the inner_loop
                                if removed_spec not in generated_acsl_spec_list:
                                    #input("66666666666666666, enter")
                                    if is_outter_loop == True and (GPT_Task == 1 or GPT_Task ==3):
                                        remove_from_inner_loop(GPT_File, cur_task_id, removed_spec)
                                    #input("66666666666666666, enter")
                                else:# remove spec here
                                    generated_acsl_spec_list.remove(removed_spec)
                                os.remove(output_std_file_name)
                                print(lines[i], end="")
                                print("  =============> delete invalid spec")
                                break
                        elif '[wp] ' in lines[i] and os.path.join(Output_folder, target_file) in lines[i] and "User Error:":
                            # print("55555")
                            _, rightstr = lines[i].split(os.path.join(Output_folder, target_file)+":",1)
                            lineNumStr, _ = rightstr.split(":",1)
                            if generated_acsl_spec_list == []:
                                break
                            invalid_line_path = os.path.join(Output_folder, target_file)
                            with open(invalid_line_path, "r") as invalid_source:
                                invalid_lines = invalid_source.readlines()
                            invalid_line_no = int(lineNumStr)
                            if not (0 < invalid_line_no <= len(invalid_lines)) or not is_removable_acsl_line(invalid_lines[invalid_line_no - 1]):
                                print("skip removal of non-ACSL WP error location")
                                ERROR_TAG = True
                                break
                            removed_spec = remove_one_line_from_the_file(invalid_line_path, invalid_line_no)
                            if removed_spec in generated_acsl_spec_list:
                                generated_acsl_spec_list.remove(removed_spec)
                        # elif os.path.join(Output_folder, target_file) in lines[i] and "User Error:":
                        else:
                            ERROR_TAG = True
                            break
                        if i == len(lines) - 1:
                            I_REACH_MAX = True
                    if I_REACH_MAX == True:
                        if GPT_Task == 2 or GPT_Task == 4:
                            error_lead_to_invalid = True
                            break
                    
                    if error_lead_to_invalid == True:
                        continue

                    if ERROR_TAG == True:
                        break

                if generated_acsl_spec_list == []:
                    break
            elif "Fail_" in output_result_type:
                if (GPT_Task == 2 or GPT_Task == 4) and assume_behavior_flag == True:
                    _, pgstr, agstr = output_result_type.split('_')
                    pass_goal = int(pgstr)
                    all_goal = int(agstr)
                    if pass_goal > max_pass_goal or (pass_goal == max_pass_goal and all_goal > max_all_goal):
                        max_pass_goal = pass_goal
                        max_all_goal = all_goal
                        best_target_file = target_file
                        generated_acsl_spec_list = full_reply_content_list[ci].splitlines()
                    ci += 1
                    if ci == len(generated_file_list):
                        break
                    continue
                # don't check for inner loop
                if is_outter_loop == False and (GPT_Task == 1 or GPT_Task == 3):
                    break

                removed_spec_list = simplify_acsl(output_std_file_name, os.path.join(Output_folder, target_file))
                if generated_acsl_spec_list == []:
                    break
                if removed_spec_list != -1 and removed_spec_list != []:
                    for each_spec in removed_spec_list:
                        if each_spec == '}':
                            break
                        print("remove spec =", each_spec)
                        print("generated_acsl_spec_list = ", generated_acsl_spec_list)
                        # if the spec is in the inner_loop
                        if each_spec not in generated_acsl_spec_list:
                            #input("88888888888888888, enter")
                            if is_outter_loop == True and (GPT_Task == 1 or GPT_Task ==3):
                                remove_from_inner_loop(GPT_File, cur_task_id, each_spec)
                            #input("88888888888888888, enter")
                        else:# remove spec here
                            generated_acsl_spec_list.remove(each_spec)
                else:
                    # Frama-C may locate a failed proof obligation on the C
                    # statement that creates it.  If no ACSL clause can be
                    # removed safely, rerunning the identical candidate cannot
                    # make progress and previously looped until the API timeout.
                    print("no removable ACSL clause; stop retrying this candidate")
                    break
            else:
                #print(output_result_type, "@@@@@@")
                #break
                if GPT_Task == 1 or GPT_Task == 3:
                    break
                elif GPT_Task == 2 or GPT_Task == 4:
                    if assume_behavior_flag == True:
                        if 'Pass_' in output_result_type:
                            _, pgstr, agstr = output_result_type.split('_')
                            pass_goal = int(pgstr)
                            all_goal = int(agstr)
                            if pass_goal > max_pass_goal and all_goal >= max_all_goal:
                                max_pass_goal = pass_goal
                                max_all_goal = all_goal
                                best_target_file = target_file
                                generated_acsl_spec_list = []
                                for each in full_reply_content_list[ci].split('\n'):
                                    generated_acsl_spec_list.append(each)
                        
                        ci = ci + 1
                        if ci == len(generated_file_list):
                            break
                    else:
                        break
            
            # print(generated_acsl_spec_list)
        
        if (GPT_Task == 2 or GPT_Task == 4) and assume_behavior_flag == True:
            if best_target_file == "":
                print("No useful specification.")
                with open(GPT_File + ".pickle", "rb") as fdata:
                    failed_metrics = pickle.load(fdata)
                failed_metrics['llms_query_times'] += llms_query_times
                failed_metrics['total_solve_time'] += total_solve_time
                failed_metrics['tokens_usage'] += tokens_usage
                failed_metrics['Iteration'] += 1
                with open(GPT_File + ".pickle", "wb") as output:
                    pickle.dump(failed_metrics, output)
                return False, llms_query_times, total_solve_time, tokens_usage
            if best_target_file != merged_file:
                print(best_target_file)
                # copy best_target_file into merged_file
                os.system("cp -f " + os.path.join(Output_folder, best_target_file) + " " + os.path.join(Output_folder, merged_file))





        # Load SAVE_PICKLE
        SAVE_PICKLE = {}
        fdata = open(GPT_File + ".pickle", "rb")
        SAVE_PICKLE = pickle.load(fdata)
        # close pickle file
        fdata.close()
        
        # remove useless spec and empty string
        for each_spec in generated_acsl_spec_list:
            if each_spec.startswith("//@ assert "):
                generated_acsl_spec_list.remove(each_spec)
            elif each_spec == '':
                generated_acsl_spec_list.remove(each_spec)
        
        # update SAVE_PICKLE
        if generated_acsl_spec_list != []:
            if GPT_Task == 1 or GPT_Task == 3:
                SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])].extend(generated_acsl_spec_list)
                SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])] = sorted(list(SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])]))
            else:
                if assume_behavior_flag == True:
                    SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])] = generated_acsl_spec_list
                else:
                    SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])] = sorted(generated_acsl_spec_list)
                    
            
            SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])].reverse()

        # update CurTaskID
        if len(SAVE_PICKLE['TaskList']) > SAVE_PICKLE['CurTaskID']:
            SAVE_PICKLE['CurTaskID'] += 1
        
        # update times
        SAVE_PICKLE['llms_query_times'] = SAVE_PICKLE['llms_query_times'] + llms_query_times
        SAVE_PICKLE['total_solve_time'] = SAVE_PICKLE['total_solve_time'] + total_solve_time
        SAVE_PICKLE['tokens_usage'] = SAVE_PICKLE['tokens_usage'] + tokens_usage

        # final task: assertion in main()
        if len(SAVE_PICKLE['TaskList']) == SAVE_PICKLE['CurTaskID']:
            file_alter(os.path.join(Output_folder, merged_file), "// @ assert", "//@ assert")
            output_result_type, output_std_file_name, output_err_file_name, solve_time = run_framac_with_wp(Output_folder, merged_file)
            total_solve_time = solve_time + total_solve_time
            
            # debug
            print(SAVE_PICKLE)
        
            if output_result_type != "Invalid" and "Fail_" not in output_result_type and "Pass" in output_result_type:
                SAVE_PICKLE['Status'] = 1
                return_value = True
                # simplify (wcventure)
                if return_value == True:
                    pass

                ## 打印皮卡丘
                print(Pikachu_str)
                with open(os.path.join(Output_folder, "final_result"), "w") as f:
                    f.write("Pass\n")
                    f.write(str(SAVE_PICKLE))
                    f.write('\n' + Pikachu_str)
                # logging with red color
                print("Round", SAVE_PICKLE['Round'])
                logging.info("\033[1;31m Congratulations, you have successfully passed the verification.\033[0m\n")
                
            else:
                SAVE_PICKLE['CurTaskID'] = 1
                SAVE_PICKLE['Iteration'] += 1
                SAVE_PICKLE['Round'] += 1
                ## 删除contract部分
                for i in range(0, len(SAVE_PICKLE['TaskList'])):
                    if SAVE_PICKLE['TaskList'][i] == 1:
                        SAVE_PICKLE[str(i+1)] = []

                ## 打印一条小鳄鱼
                print(Crocodile_str)
                with open(os.path.join(Output_folder, "final_result"), "w") as f:
                    f.write("Fail\n")
                    f.write(str(SAVE_PICKLE))
                    f.write('\n' + Crocodile_str)
                # logging with red color with fail message
                print("Round", int(SAVE_PICKLE['Round']) - 1)
                logging.info("\033[1;31m Sorry, you have failed the verification.\033[0m\n")
            pass

        # Save as list
        with open(GPT_File + ".pickle", "wb") as output:
            pickle.dump(SAVE_PICKLE, output)

    elif GPT_Task != 0:
        for each_file in generated_file_list:
            _, _, _, solve_time = run_framac_with_wp(Output_folder, each_file)
            total_solve_time = solve_time + total_solve_time

    return return_value, llms_query_times, total_solve_time, tokens_usage


# process only the hole folder
def query_llm_and_get_verified_result_for_filelist(all_cpp_file_list, Output_folder, GPT_Task, sys_prompt, n_choices, shot_num, model_config, enable_mutation):
    if len(all_cpp_file_list) == 0:
        logging.error("No file in this folder")
        sys.exit(-1)
    else:
        ret_list = []
        llms_query_times = datetime.timedelta(0)
        total_solve_time = datetime.timedelta(0)
        tokens_usage = 0
        for each_file in all_cpp_file_list:
            ret, cur_query_times, cur_solve_time, cur_tokens_usage = query_llm_and_get_verified_result_for_single_file(
                each_file, 
                Output_folder, 
                GPT_Task, 
                sys_prompt, 
                n_choices, 
                shot_num, 
                model_config,  # 传入 ModelConfig 对象
                enable_mutation
            )
            ret_list.append(ret)
            llms_query_times = cur_query_times + llms_query_times
            total_solve_time = cur_solve_time + total_solve_time
            tokens_usage = cur_tokens_usage + tokens_usage
    if len(ret_list) == 1:
        return ret_list[0], llms_query_times, total_solve_time, tokens_usage
    else:
        return False, llms_query_times, total_solve_time, tokens_usage


def LLMVeri_Main(GPT_File, GPT_Task, Output_folder, model_config, enable_mutation):
    
    if GPT_File is None or GPT_Task is None:
        print("No file or task")
        return
        
    # set logging.INFO rather than logging.DEBUG
    logging.basicConfig(level=logging.INFO)

    if not os.path.exists(GPT_File):
        logging.error("GPT_File is not exist")
        sys.exit(-1)
    
    # whether exist this Output_folder
    if not os.path.exists(Output_folder):
        os.makedirs(Output_folder)
    else:
        if len(os.listdir(Output_folder)) != 0:
            logging.error("Output_folder is not empty")
            sys.exit(-1)
    
    # verification_positioning_only, verification_positioning_one_shot
    sys_prompt = verification_positioning_only

    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++ start +++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

    # whether GPT_FILE is a file or folder
    if os.path.isdir(GPT_File):
        # get all C files in this folder
        all_files = os.listdir(GPT_File)
        all_cpp_file_list = []
        for each_file in all_files:
            if each_file.endswith(".c") or each_file.endswith(".cpp"):
                if "_verified." not in each_file:
                    # merge folder and each_file as file
                    all_cpp_file_list.append(os.path.join(GPT_File, each_file))
    else:
        # open GPT_File and get strings
        if GPT_File.endswith(".c") or GPT_File.endswith(".cpp"):
            # whether exist this file
            if not os.path.exists(GPT_File):
                logging.error("GPT_File is not exist")
                sys.exit(-1)
            all_cpp_file_list = [GPT_File]
        else:
            logging.error("GPT_File is not C file")
            sys.exit(-1)
        
    ret, llms_query_times, total_solve_time, tokens_usage = query_llm_and_get_verified_result_for_filelist(
        all_cpp_file_list, 
        Output_folder, 
        GPT_Task, 
        sys_prompt, 
        N_CHOICES, 
        SHOT_NUM, 
        model_config,
        enable_mutation
    )
    
    print("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("++++++++++++++++++++++++++++ End ++++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    return ret, llms_query_times, total_solve_time, tokens_usage
