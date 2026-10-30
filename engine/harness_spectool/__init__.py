"""spectool — deterministic toolbox backing the spec-* Claude Code skills.

Layer B of the design (docs/design.md §5): all deterministic / mechanical work
(static analysis, Frama-C, parsing, ACSL injection, state I/O) lives here so the
LLM never has to do it. No LLM calls are made anywhere in this package.
"""

__version__ = "0.1.0"
