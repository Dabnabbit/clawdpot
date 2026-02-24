"""GSD Calculator scenario — same task as calculator but via /gsd:quick.

Tests whether GSD's orchestration (planner → executor subagents) can
produce the same quality output as direct claude -p. Uses identical
judge tests as the calculator scenario.
"""

NAME = "gsd_calculator"
DESCRIPTION = "Calculator via /gsd:quick — tests GSD orchestration with mixed model routing"
TIMEOUT_S = 600  # GSD overhead: planner + executor subagents
TOTAL_TESTS = 15
