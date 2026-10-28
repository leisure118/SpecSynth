"""Verbatim pure prompt builders from the original experiment.

Source: NL2VRAG/experiment/b3/run.py, lines 161-344.
Only the two builders, error classifier, strategy function, and their constants
are bundled. No configuration, network client, or experiment runner is imported.
"""


def build_generation_prompt(description: str, function_signature: str,
                            retrieved_examples: list) -> str:
    """构建生成 prompt，含检索到的参考代码"""
    lines = [
        "You are an expert in Verus verification. Generate a formally verified Verus function for the following task.",
        "",
        "=== INSTRUCTIONS ===",
        "1. Output ONLY Verus code (no Markdown formatting, no backticks, no explanation).",
        "2. Start with: use vstd::prelude::*;",
        "3. Then wrap everything in: verus! { ... }",
        "4. ALWAYS include 'fn main() {}' at the end.",
        "5. Use 'int' and 'nat' types ONLY in spec/proof/ghost contexts.",
        "6. For loop decreases, use comma-separated: 'decreases x, y'.",
        "7. Include proper requires/ensures specifications.",
        "8. Include loop invariants and decreases for all while loops.",
        "9. Ensure the code is syntactically correct Rust and passes Verus verification.",
        "",
    ]

    if retrieved_examples:
        lines.append("=== REFERENCE EXAMPLES (similar verified Verus functions) ===")
        for i, ex in enumerate(retrieved_examples, 1):
            lines.append(f"")
            lines.append(f"--- Reference {i} ---")
            lines.append(f"Description: {ex.get('description', '')[:300]}")
            lines.append(f"Verified Verus Code:")
            lines.append(ex.get("verified_verus", ""))
        lines.append("")
        lines.append("=== END OF REFERENCES ===")
        lines.append("")

    lines.extend([
        "=== TASK DESCRIPTION ===",
        description,
        "",
        "=== FUNCTION SIGNATURE ===",
        function_signature,
        "",
        "=== OUTPUT ===",
        "Generate only the Verus code. Do not include any explanation or commentary.",
    ])

    return "\n".join(lines)


VERUS_ERROR_KEYWORDS = {
    "mismatched types": "TypeMismatch",
    "expected curly braces": "SyntaxCurlyBraces",
    "expected `,`": "SyntaxComma",
    "cannot find value `result`": "MissingResult",
    "use `old(a)` to refer to the pre-state": "MutableRefOld",
    "can only be used in ghost code": "NatIntInExec",
    "could not automatically infer triggers": "QuantifierTrigger",
    "assertion failed": "AssertFail",
    "precondition not satisfied": "PreCondFail",
    "postcondition not satisfied": "PostCondFail",
    "invariant not satisfied": "InvFail",
    "arithmetic underflow/overflow": "ArithOverflow",
    "loop must have a decreases clause": "Decreases",
    "unexpected token": "UnexpectedToken",
    "expected parentheses": "ExpectedParens",
}

PROOF_BLOCK_INFO = """The proof block looks like this:
```
proof {
    // your proof code here
    // assert(...)
    // LEMMA_FUNCTION(...)
    // ...
} // Added by AI
```

Note, please DO NOT modify all other proof blocks that are not related to the error. Just leave them as they are."""


def classify_verus_error(error_summary: str) -> str:
    """从 Verus 错误文本中识别错误类型。返回错误类型标签。"""
    error_lower = error_summary.lower()
    for keyword, label in VERUS_ERROR_KEYWORDS.items():
        if keyword in error_lower:
            return label
    return "Other"


def strategy_for_error_type(error_label: str) -> str:
    """根据错误类型返回修复策略描述。"""
    strategies = {
        "TypeMismatch": (
            "fix the type error. Check the types of variables and function arguments, "
            "and fix any type mismatches. Use 'int'/'nat' only in ghost/spec contexts."
        ),
        "SyntaxCurlyBraces": (
            "fix the syntax error with curly braces or block structure. "
            "Check that all verus! blocks, function bodies, and loop bodies have matching braces."
        ),
        "SyntaxComma": (
            "fix the syntax error. There is a missing comma, usually in a `decreases` clause."
        ),
        "MissingResult": (
            "fix the error. `result` in an ensures clause refers to the return value. "
            "Inside while loop bodies, use a mutable local variable to accumulate results."
        ),
        "MutableRefOld": (
            "fix the error. To refer to the pre-state value of a mutable parameter, use `old(x)`."
        ),
        "NatIntInExec": (
            "fix the type error. `int` and `nat` can only be used in spec/proof/ghost contexts. "
            "In exec code, use u64, i64, u32 etc. instead."
        ),
        "QuantifierTrigger": (
            "fix the quantifier error. Add `#[trigger]` annotations to help Verus infer triggers."
        ),
        "AssertFail": (
            "fix the assertion failed error. Add proof blocks with assertions and lemma calls "
            "before the failing assertion to help the verifier prove it."
        ),
        "PreCondFail": (
            "fix the precondition not satisfied error. Add proof blocks related to the "
            "pre-condition check just before the function invocation. Use pre-conditions "
            "of the current function, loop invariants to help fix the error."
        ),
        "PostCondFail": (
            "fix the postcondition not satisfied error. Add/reinforce loop invariants, "
            "or add proof blocks before the end of the function."
        ),
        "InvFail": (
            "fix the invariant not satisfied error. Add/reinforce loop invariants and "
            "add assertions in proof blocks before/after the loop."
        ),
        "ArithOverflow": (
            "fix the arithmetic error. Add appropriate checks to prevent underflow/overflow."
        ),
        "Decreases": (
            "fix the decreases clause error. Add a `decreases` clause to the loop, "
            "use comma-separated values like `decreases x, y`."
        ),
        "UnexpectedToken": (
            "fix the syntax error. Check for unexpected tokens in the code."
        ),
        "ExpectedParens": (
            "fix the syntax error. Expected parentheses somewhere in the code."
        ),
    }
    return strategies.get(error_label, (
        "fix the error. Add/modify/delete proof blocks, assertions and loop invariants "
        "related to the error."
    ))


def build_repair_prompt(description: str, function_signature: str,
                        code: str, error_summary: str) -> str:
    """构建修复 prompt，含错误类型策略 + proof block info（与 AutoVerus/B2 一致）"""
    error_type = classify_verus_error(error_summary)
    strategy = strategy_for_error_type(error_type)

    instruction = f"Your mission is to {strategy}"
    instruction += "\n\nResponse with the Rust code only, do not include any explanation."

    if error_type in ["AssertFail", "PreCondFail", "PostCondFail", "InvFail"]:
        instruction += "\n\n" + PROOF_BLOCK_INFO

    lines = [
        "=== TASK DESCRIPTION ===",
        description,
        "",
        "=== FUNCTION SIGNATURE ===",
        function_signature,
        "",
        "=== CURRENT (FAILING) CODE ===",
        code,
        "",
        "=== VERUS ERRORS ===",
        error_summary,
        "",
        "=== OUTPUT ===",
        "Generate the corrected Verus code only.",
    ]

    return instruction + "\n\n" + "\n".join(lines)
