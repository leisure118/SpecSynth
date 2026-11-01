"""Prepared-input C workflow: native delegation, one candidate write, platform proof."""

def task_prompt(prompt):
    return prompt + '''

COMPACT C EXECUTION PLAN (replaces procedural split/orchestration examples above):
The platform already supplied every original file and the full Skill instructions in this message.
Do not list directories, read Skill files, inspect tools/help, create function slices or initialize a contract store.
Apply the semantic requirements of spec-bottomup directly to the complete input; preserve all C tokens and original ACSL assertions.
If Previous candidate and Verifier diagnostics are supplied, repair that candidate narrowly instead of generating from scratch.
Group consecutive loop invariant/assigns/variant clauses in ONE /*@ ... */ block. Do not emit consecutive //@ loop clauses.
For a root main with no explicit return, do not invent a result postcondition or add a return statement. Preserve its original assertions and generate the loop annotations needed to prove them.
1. Call the native subagent tool ONCE. Include the complete original files, any previous candidate, the diagnostics and the spec-bottomup instructions in its task.
The worker is text-only: it must return ONLY JSON {"files":[{"path":"original path","content":"complete annotated source"}]}.
It must not read files, use tools, run a verifier, poll, or create plans. It must not add admit/assume/axiom or weaken existing assertions.
2. Wait for the runtime to deliver the worker's completed answer. Do not poll job_list or send_message.
3. Use one native file-write tool to save that JSON verbatim to answer.json in this workspace.
Do not run an internal proof, slice verifier or contract saver. The platform independently validates the complete candidate and runs Frama-C immediately after you finish.
Do not write summary files or duplicate C files. Do not claim success: your job ends when answer.json is saved.
If the child fails or cannot provide the JSON, report the failure rather than replacing its work.
'''
