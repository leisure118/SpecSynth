---
name: verus-baseline
description: Generate complete Verus Rust programs from natural-language tasks and repair them using verifier diagnostics.
---

# NL to Verus Baseline

Produce a complete, self-contained Rust source file for the platform's Verus verifier. The platform performs verification after generation and provides diagnostics for bounded repair attempts; no shell or filesystem tools are available in this generation step.

## Generate

- Preserve the requested function name, parameter types, return type, and observable behavior. Follow the provided function signature when present.
- Translate the natural-language task into meaningful `requires` and `ensures`. Use only task-stated input assumptions or necessary representability constraints; do not exclude intended inputs to make verification easier. Never use contradictory preconditions or trivial postconditions.
- Include `use vstd::prelude::*;` and place Verus definitions inside `verus! { ... }`. Return one complete compilable file, including all required helpers.
- Distinguish machine integers from mathematical `int`/`nat`. Establish index bounds and arithmetic safety; use explicit casts in specifications when needed.
- For loops, add inductive invariants that establish bounds and connect the computed prefix or search interval to the postcondition. Add a nonnegative, strictly decreasing termination measure when required by the task.
- Use small `proof` blocks or proved helper lemmas when necessary. Do not use `assume`, `admit`, `external_body`, unimplemented stubs, or other proof bypasses.
- Prefer a simple implementation and standard Verus syntax. Keep executable code, specifications, and proof steps distinguishable.

## Repair

Use the supplied verifier diagnostics and previous candidate to fix the specific failing obligations. Keep the intended behavior and contract; strengthen invariants or add valid proof steps rather than weakening the task. Return the entire revised file, not a patch.

## Output

Return Rust/Verus source only, without Markdown fences or explanatory prose. Do not claim successful verification: the platform records the actual verifier result separately.
