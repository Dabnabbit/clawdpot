# CLAUDE.md — Clawdpot

## What is this?

Clawdpot is a model competition system for Claude Code. It gives the same
coding task to multiple modes (cloud API, local Ollama) and scores results
using pytest test suites as an objective judge.

Extracted from the Hermit-Claude project where it was the "bakeoff" subsystem.

## Project Structure

```
clawdpot/
├── __init__.py        # Package docstring
├── __main__.py        # Typer CLI (list, run, score, results, report, note)
├── runner.py          # Orchestrates: setup → claude -p → judge → metrics
├── models.py          # Mode, RunResult, StatsSnapshot, TestResult, ScoreCard
├── scorer.py          # Rich comparison tables, markdown report generation
├── environment.py     # Per-mode env dict builders (native, offline, offline-cpu)
├── pricing.py         # Model classification and Anthropic cost estimation
├── notes.md           # Historical run annotations
└── scenarios/
    ├── __init__.py    # Scenario discovery and loading
    ├── calculator/    # Expression parser (15 tests)
    ├── debug_hunt/    # Fix 5 seeded bugs (10 tests)
    ├── api_server/    # Flask REST API (20 tests)
    └── refactor/      # Restructure monolithic code (20 tests)
```

## Tech Stack

- Python 3.12+, Typer (CLI), Rich (terminal output)
- Claude Code (`claude` CLI) as the model runner
- pytest as the judge framework

## Coding Conventions

- Type hints, dataclasses for data models
- Comments explain *why*, not *what*
- Test changes by running scenario judges manually or via `clawdpot run`

## Key Design Decisions

- **Workdirs in /tmp/** — Prevents claude -p from discovering parent project context
- **Ollama warm-up** — Pre-loads model in VRAM before timing starts
- **Randomized mode order** — Prevents systematic bias in multi-mode runs
- **Stats-cache.json diffing** — Token usage computed from before/after snapshots
- **No shared deps** — pricing.py is self-contained (duplicated from hermit_claude)
