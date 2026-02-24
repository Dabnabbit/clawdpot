"""Refactor scenario — restructure messy monolithic code into clean modules.

Hard scenario: requires reading + understanding existing code, then splitting
into multiple files while preserving all behavior and meeting structural
requirements. Tests verify both functionality and architecture.
"""

NAME = "refactor"
DESCRIPTION = "Refactor a monolithic inventory system into clean multi-module architecture"
TIMEOUT_S = 600
TOTAL_TESTS = 20
