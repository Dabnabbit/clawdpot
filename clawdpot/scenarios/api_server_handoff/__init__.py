"""API Server Handoff scenario — two-phase build to test model switching.

Phase 1: Core CRUD (GET, POST, DELETE, basic stats)
Phase 2: Validation, PUT updates, genre filtering, full stats

Uses phase1_spec.md and phase2_spec.md instead of a single spec.md.
Judged by the same 20 tests as api_server, run once at the end.
"""

NAME = "api_server_handoff"
DESCRIPTION = "Two-phase API build to test cloud/local model handoff"
TIMEOUT_S = 600
TOTAL_TESTS = 20
