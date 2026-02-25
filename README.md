# clawdpot

Model competition system for Claude Code. Throw models in, see which one comes out on top.

Like a [crab pot](https://en.wikipedia.org/wiki/Crab_trap) — models go in, results come out. The best model wins.

## What it does

Gives the same coding task to multiple modes (cloud API, local Ollama) and scores the results using pre-written pytest test suites as an objective judge.

Each run:
1. Sets up an isolated workdir
2. Feeds the task spec to `claude -p`
3. Runs pytest judge tests against the output
4. Records metrics (pass rate, wall clock, tokens, cost)

## Install

```bash
pip install -e .
```

Requires Claude Code (`claude` CLI) on PATH.

## Usage

```bash
# List available scenarios
clawdpot list

# Run a single scenario in one mode
clawdpot run calculator --mode offline --model qwen3-coder

# Run all three modes (native, hybrid, offline)
clawdpot run calculator --all

# Run a two-phase handoff scenario
clawdpot handoff api_server_handoff --phase1-mode native --phase2-mode offline

# Compare latest results
clawdpot score calculator

# List all stored results
clawdpot results

# Generate RESULTS.md report
clawdpot report
```

Also works as a module:

```bash
python -m clawdpot list
python -m clawdpot run calculator --mode native
```

## Scenarios

| Scenario | Description | Tests |
|----------|-------------|-------|
| calculator | Expression parser (no eval) | 15 |
| debug_hunt | Find and fix 5 seeded bugs | 10 |
| api_server | Flask REST API to spec | 20 |
| api_server_handoff | Two-phase: CRUD then validation | 20 |
| gsd_calculator | Calculator with GSD scaffold | 15 |
| refactor | Restructure monolithic code | 20 |

## Modes

- **native** — Vanilla Anthropic cloud API (control baseline)
- **hybrid** — Direct Anthropic cloud (same as native post-proxy)
- **offline** — Local Ollama only, zero network calls
