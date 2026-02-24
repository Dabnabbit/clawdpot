"""Clawdpot runner — orchestrates setup → claude -p → judge → metrics.

Data flow per run:
1. Create isolated workdir/ and result_dir/ for this run
2. Copy seed files (if any) into workdir
3. Snapshot stats-cache.json (before)
4. Build mode-specific env dict
5. Run: claude -p "<spec>" --dangerously-skip-permissions
6. Capture stdout, stderr, exit code, wall clock time
7. Snapshot stats-cache.json (after), compute token delta
8. Copy judge tests into workdir, run pytest
9. Assemble RunResult, save as metrics.json
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console

from clawdpot.environment import build_native_env, build_offline_env
from clawdpot.models import Mode, RunResult, StatsSnapshot, TestResult
from clawdpot.pricing import classify_model, estimate_cost
from clawdpot.scenarios import load_scenario


def _model_slug(model: str) -> str:
    """Normalize a model name for use in directory paths.

    'gemma3:4b' → 'gemma3-4b', 'gpt-oss:20b' → 'gpt-oss-20b'
    """
    return model.replace(":", "-").replace("/", "-")


def _warm_ollama(model: str, console: Console) -> None:
    """Send a lightweight request to Ollama to ensure the model is loaded in VRAM.

    Without this, the first mode to hit Ollama pays a 5-15s model load penalty
    that skews wall clock comparisons.
    """
    import urllib.request
    import urllib.error

    url = "http://127.0.0.1:11434/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": "hi",
        "stream": False,
        "options": {"num_predict": 1},
    }).encode()

    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
        console.print(f"  [dim]Ollama warm: {model} loaded in VRAM[/dim]")
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        console.print(f"  [yellow]Ollama warm-up failed: {e}[/yellow]")


def _results_root() -> Path:
    """Absolute path to clawdpot/results/."""
    return Path(__file__).parent / "results"


def _ensure_workdir(scenario: str, mode: str, timestamp: str) -> tuple[Path, Path]:
    """Create and return (result_dir, workdir) for a run.

    Workdir lives under /tmp/ so claude -p doesn't discover the parent
    project CLAUDE.md and context. Results are stored in-tree and the
    workdir is symlinked from result_dir for easy inspection.
    """
    result_dir = _results_root() / scenario / mode / timestamp
    result_dir.mkdir(parents=True, exist_ok=True)
    # Workdir in /tmp/ for context isolation from parent project
    workdir = Path(f"/tmp/clawdpot-{scenario}-{mode}-{timestamp}")
    workdir.mkdir(parents=True, exist_ok=True)
    # Symlink from result_dir for easy access
    link = result_dir / "workdir"
    if not link.exists():
        link.symlink_to(workdir)
    return result_dir, workdir


def _copy_seed(seed_dir: Optional[Path], workdir: Path) -> None:
    """Copy seed files into the workdir if they exist."""
    if seed_dir and seed_dir.is_dir():
        shutil.copytree(seed_dir, workdir, dirs_exist_ok=True)


def _run_claude(
    spec_text: str,
    workdir: Path,
    env: dict[str, str],
    timeout_s: int,
    mode: Mode,
    result_dir: Path,
) -> tuple[int, float, str, str]:
    """Run claude -p with the spec and capture output.

    Returns (exit_code, wall_clock_s, stdout, stderr).
    """
    cmd = [
        "claude",
        "-p", spec_text,
        "--dangerously-skip-permissions",
        # Context isolation: don't persist sessions or read parent project config
        "--no-session-persistence",
        "--setting-sources", "user",
    ]

    # Safety cap on native mode to limit cloud spend
    if mode == Mode.NATIVE:
        cmd.extend(["--max-budget-usd", "2.0"])

    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=workdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        elapsed = time.monotonic() - start
        return proc.returncode, elapsed, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return -1, elapsed, "", f"TIMEOUT after {timeout_s}s"


def _run_judge(workdir: Path, tests_dir: Path, result_dir: Path) -> TestResult:
    """Copy judge tests into workdir and run pytest.

    Returns TestResult with pass/fail counts parsed from pytest output.
    """
    # Copy test files into workdir so pytest can find the generated code
    dest_tests = workdir / "tests"
    if dest_tests.exists():
        shutil.rmtree(dest_tests)
    shutil.copytree(tests_dir, dest_tests)

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--no-header"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = proc.stdout + "\n" + proc.stderr

        # Save pytest output
        (result_dir / "pytest-output.txt").write_text(output, encoding="utf-8")

        # Parse pytest summary line: "X passed, Y failed, Z errors"
        passed = failed = errors = 0
        # Match patterns like "15 passed", "3 failed", "1 error"
        for m in re.finditer(r"(\d+) passed", output):
            passed = int(m.group(1))
        for m in re.finditer(r"(\d+) failed", output):
            failed = int(m.group(1))
        for m in re.finditer(r"(\d+) error", output):
            errors = int(m.group(1))

        total = passed + failed + errors
        return TestResult(
            passed=passed,
            failed=failed,
            errors=errors,
            total=total,
            output=output,
        )
    except subprocess.TimeoutExpired:
        return TestResult(output="pytest timed out after 60s")
    except FileNotFoundError:
        return TestResult(output="pytest not found")


def _compute_cost(token_delta: dict[str, dict[str, int]]) -> tuple[int, int, float]:
    """Compute total tokens and estimated cost from a token delta.

    Returns (total_input, total_output, cost_usd).
    """
    total_input = 0
    total_output = 0
    total_cost = 0.0

    for model, tokens in token_delta.items():
        inp = tokens.get("inputTokens", 0)
        out = tokens.get("outputTokens", 0)
        cache_read = tokens.get("cacheReadInputTokens", 0)
        cache_create = tokens.get("cacheCreationInputTokens", 0)
        total_input += inp + cache_read + cache_create
        total_output += out

        family = classify_model(model)
        total_cost += estimate_cost(
            family,
            input_tokens=inp,
            output_tokens=out,
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_create,
        )

    return total_input, total_output, total_cost


def run_scenario(
    scenario_name: str,
    mode: Mode,
    console: Console,
    model: Optional[str] = None,
    background_model: Optional[str] = None,
    num_ctx: int = 65536,
) -> RunResult:
    """Execute a single run for one scenario and one mode.

    This is the main orchestration function. It handles the full lifecycle:
    workdir setup, env building, claude execution, judging, and metrics collection.

    Args:
        scenario_name: Name of the scenario (e.g., 'calculator').
        mode: Competition mode (native, hybrid, offline).
        console: Rich Console for status output.
        model: Ollama model override for offline mode.
        background_model: Reserved for future dual-model routing.
        num_ctx: Context window size for offline mode.

    Returns:
        RunResult with all metrics populated.
    """
    scenario = load_scenario(scenario_name)
    if not scenario:
        console.print(f"[red]Error:[/red] Unknown scenario: {scenario_name}")
        return RunResult(scenario=scenario_name, mode=mode.value, timestamp="")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Derive the mode slug for result storage — when --model is set and mode
    # is offline, include the model name so different models get separate dirs.
    mode_slug = mode.value
    if model and mode == Mode.OFFLINE:
        mode_slug = f"offline-{_model_slug(model)}"

    console.print(f"\n[bold]Running:[/bold] {scenario.name} / {mode_slug}")
    console.print(f"  Timeout: {scenario.timeout_s}s")

    # 1. Create workdir and result_dir
    result_dir, workdir = _ensure_workdir(scenario.name, mode_slug, timestamp)
    console.print(f"  Result dir: {result_dir}")

    # 2. Copy seed files
    _copy_seed(scenario.seed_dir, workdir)

    # 3. Snapshot stats-cache (before)
    stats_before = StatsSnapshot.capture()

    # 4. Build mode-specific env
    ollama_model = model or os.environ.get("HC_MODEL", "gpt-oss:20b")

    if mode == Mode.NATIVE:
        env = build_native_env()
        console.print("  Mode: [green]native[/green] (vanilla Anthropic API)")
    elif mode == Mode.HYBRID:
        # Hybrid routes directly to Anthropic cloud using the API key.
        # Without a proxy there is no per-request tier routing — the session
        # goes entirely to cloud. This makes hybrid equivalent to native for
        # comparison purposes. The API key must be set in the environment.
        env = build_native_env()
        console.print("  Mode: [cyan]hybrid[/cyan] (direct Anthropic cloud)")
    elif mode == Mode.OFFLINE:
        env = build_offline_env(model=model, num_ctx=num_ctx)
        console.print(f"  Mode: [yellow]offline[/yellow] (local Ollama only)")
    else:
        env = build_native_env()

    # 4b. Warm up Ollama for offline mode — ensures model is loaded in VRAM
    # before the clock starts so offline doesn't pay a cold-load penalty
    if mode == Mode.OFFLINE:
        _warm_ollama(ollama_model, console)

    # 5. Read the spec
    spec_text = scenario.spec_path.read_text(encoding="utf-8")

    # 6. Run claude -p
    console.print("  Running claude -p ...")
    exit_code, wall_clock, stdout, stderr = _run_claude(
        spec_text, workdir, env, scenario.timeout_s, mode, result_dir,
    )

    # Save raw output
    (result_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    (result_dir / "stderr.txt").write_text(stderr, encoding="utf-8")

    if exit_code == -1:
        console.print(f"  [red]TIMEOUT[/red] after {scenario.timeout_s}s")
    else:
        console.print(f"  Exit code: {exit_code} ({wall_clock:.1f}s)")

    # 7. Snapshot stats-cache (after) and compute delta
    stats_after = StatsSnapshot.capture()
    token_delta = StatsSnapshot.token_delta(stats_before, stats_after)
    total_input, total_output, cost_usd = _compute_cost(token_delta)

    # 8. Run judge tests
    console.print("  Running judge tests...")
    test_result = _run_judge(workdir, scenario.tests_dir, result_dir)
    console.print(
        f"  Judge: {test_result.passed}/{test_result.total} passed "
        f"([{'green' if test_result.verdict == 'pass' else 'yellow' if test_result.verdict == 'partial' else 'red'}]"
        f"{test_result.verdict}[/])"
    )

    # 9. Assemble and save RunResult
    result = RunResult(
        scenario=scenario.name,
        mode=mode_slug,
        timestamp=timestamp,
        model_name=ollama_model if mode == Mode.OFFLINE else "",
        wall_clock_s=round(wall_clock, 1),
        exit_code=exit_code,
        stdout_path=str(result_dir / "stdout.txt"),
        stderr_path=str(result_dir / "stderr.txt"),
        workdir=str(workdir),
        token_delta=token_delta,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        estimated_cost_usd=round(cost_usd, 4),
        test_result=test_result,
    )
    result.save(result_dir)

    console.print(f"  [bold green]Done.[/bold green] Metrics saved to {result_dir / 'metrics.json'}")
    return result


def run_all_modes(
    scenario_name: str,
    console: Console,
    model: Optional[str] = None,
    num_ctx: int = 65536,
) -> list[RunResult]:
    """Run a scenario across all modes in randomized order.

    Randomization prevents systematic bias from Ollama model caching,
    system-level warm-up effects, or resource contention favoring whichever
    mode runs last.

    Returns list of RunResults in execution order (randomized).
    """
    modes = [Mode.NATIVE, Mode.HYBRID, Mode.OFFLINE]
    random.shuffle(modes)
    console.print(f"\n[bold]Mode order (randomized):[/bold] {', '.join(m.value for m in modes)}")

    results = []
    for mode in modes:
        result = run_scenario(
            scenario_name, mode, console, model=model, num_ctx=num_ctx,
        )
        results.append(result)
    return results
