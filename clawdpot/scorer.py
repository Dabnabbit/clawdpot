"""Clawdpot scorer — loads results, renders Rich tables, generates markdown reports.

Finds the latest result for each mode and displays a side-by-side comparison
table showing verdict, test pass rate, wall clock, tokens, and cost.

Also generates persistent RESULTS.md with full history matrix and run notes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from clawdpot.models import ALL_MODES, Mode, RunResult, ScoreCard

# Canonical display order — known modes first, then any extras alphabetically.
_MODE_DISPLAY_ORDER = ["native", "hybrid", "offline", "offline-cpu"]


def _results_root() -> Path:
    """Absolute path to clawdpot/results/."""
    return Path(__file__).parent / "results"


def _find_latest_result(scenario: str, mode: str) -> RunResult | None:
    """Find the most recent result for a scenario/mode combination.

    Results are stored as clawdpot/results/<scenario>/<mode>/<timestamp>/metrics.json.
    The latest timestamp (lexicographic sort) wins.
    """
    mode_dir = _results_root() / scenario / mode
    if not mode_dir.is_dir():
        return None

    # Timestamps are ISO8601 and sort lexicographically
    runs = sorted(mode_dir.iterdir(), reverse=True)
    for run_dir in runs:
        result = RunResult.load(run_dir)
        if result:
            return result
    return None


def _discover_modes(scenario: str) -> list[str]:
    """Discover all mode slugs that have results for a scenario.

    Returns modes sorted: canonical order first (native, hybrid, offline),
    then any model-specific slugs (offline-gemma3-4b, etc.) alphabetically.
    """
    scenario_dir = _results_root() / scenario
    if not scenario_dir.is_dir():
        return []
    found = [d.name for d in scenario_dir.iterdir() if d.is_dir()]
    canonical = [m for m in _MODE_DISPLAY_ORDER if m in found]
    extras = sorted(m for m in found if m not in _MODE_DISPLAY_ORDER)
    return canonical + extras


def load_scorecard(scenario: str) -> ScoreCard:
    """Load the latest results for all modes of a scenario.

    Discovers modes dynamically from result directories rather than
    hardcoding — supports model-specific slugs like 'offline-gemma3-4b'.
    """
    card = ScoreCard(scenario=scenario)
    for mode_slug in _discover_modes(scenario):
        result = _find_latest_result(scenario, mode_slug)
        if result:
            card.results[mode_slug] = result
    return card


def _fmt_tokens(n: int) -> str:
    """Format token count with K suffix."""
    if n == 0:
        return "--"
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


def _fmt_cost(c: float) -> str:
    """Format cost in USD."""
    if c == 0.0:
        return "$0.00"
    return f"${c:.4f}"


def render_scorecard(card: ScoreCard, console: Console) -> None:
    """Render a Rich comparison table for a scenario's results."""
    if not card.results:
        console.print(f"[yellow]No results found for scenario: {card.scenario}[/yellow]")
        return

    table = Table(
        title=f"Bakeoff: {card.scenario}",
        show_header=True,
        header_style="bold",
    )

    table.add_column("Metric", style="dim", min_width=16)

    # Add a column for each mode that has results (dynamically discovered)
    active_modes = list(card.results.keys())

    mode_styles = {
        "native": "green",
        "hybrid": "cyan",
        "offline": "yellow",
        "offline-cpu": "magenta",
    }

    for mode_slug in active_modes:
        # Color: use canonical color if it starts with a known prefix
        style = "white"
        for prefix, s in mode_styles.items():
            if mode_slug == prefix or mode_slug.startswith(f"{prefix}-"):
                style = s
                break
        table.add_column(
            mode_slug,
            style=style,
            justify="right",
            min_width=12,
        )

    def _row(label: str, getter) -> None:
        """Add a row by extracting a value from each mode's result."""
        vals = []
        for mode_slug in active_modes:
            r = card.results[mode_slug]
            vals.append(getter(r, mode_slug))
        table.add_row(label, *vals)

    # Model name (show if any result has one)
    if any(r.model_name for r in card.results.values()):
        _row("Model", lambda r, m: r.model_name or "[dim]cloud[/dim]")

    # Verdict
    def verdict(r: RunResult, m: str) -> str:
        if not r.test_result:
            return "[dim]--[/dim]"
        v = r.test_result.verdict
        color = {"pass": "green", "partial": "yellow", "fail": "red"}.get(v, "white")
        return f"[{color}]{v}[/{color}]"
    _row("Verdict", verdict)

    # Tests passed
    def tests(r: RunResult, m: str) -> str:
        if not r.test_result:
            return "--"
        return f"{r.test_result.passed}/{r.test_result.total}"
    _row("Tests passed", tests)

    # Wall clock
    _row("Wall clock", lambda r, m: f"{r.wall_clock_s}s" if r.wall_clock_s else "--")

    # Input tokens
    _row("Input tokens", lambda r, m: _fmt_tokens(r.total_input_tokens))

    # Output tokens
    _row("Output tokens", lambda r, m: _fmt_tokens(r.total_output_tokens))

    # Estimated cost
    _row("Est. cost", lambda r, m: _fmt_cost(r.estimated_cost_usd))

    # Exit code
    def exitcode(r: RunResult, m: str) -> str:
        if r.exit_code == 0:
            return "[green]0[/green]"
        if r.exit_code == -1:
            return "[red]timeout[/red]"
        return f"[red]{r.exit_code}[/red]"
    _row("Exit code", exitcode)

    # Timestamp
    _row("Run time", lambda r, m: r.timestamp or "--")

    console.print()
    console.print(table)
    console.print()


def list_all_results(console: Console) -> None:
    """List all available results across all scenarios and modes."""
    root = _results_root()
    if not root.is_dir():
        console.print("[yellow]No results yet. Run a scenario first.[/yellow]")
        return

    for scenario_dir in sorted(root.iterdir()):
        if not scenario_dir.is_dir():
            continue
        console.print(f"\n[bold]{scenario_dir.name}[/bold]")
        for mode_dir in sorted(scenario_dir.iterdir()):
            if not mode_dir.is_dir():
                continue
            runs = sorted(mode_dir.iterdir(), reverse=True)
            for run_dir in runs:
                result = RunResult.load(run_dir)
                if result:
                    tr = result.test_result
                    verdict = tr.verdict if tr else "?"
                    tests = f"{tr.passed}/{tr.total}" if tr else "?"
                    console.print(
                        f"  {mode_dir.name:10s} {run_dir.name}  "
                        f"{verdict:8s} {tests:6s} {result.wall_clock_s:>6.1f}s"
                    )


# ---------------------------------------------------------------------------
# Notes system
# ---------------------------------------------------------------------------

def _notes_path() -> Path:
    """Path to the run notes file (outside results/ so it can be committed)."""
    return Path(__file__).parent / "notes.md"


def load_notes() -> dict[str, str]:
    """Load run notes keyed by timestamp.

    Notes file format: lines of `TIMESTAMP: note text`
    """
    path = _notes_path()
    if not path.exists():
        return {}
    notes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ": " in line:
            ts, text = line.split(": ", 1)
            notes[ts.strip()] = text.strip()
    return notes


def save_note(timestamp: str, text: str) -> None:
    """Append a note for a specific run timestamp."""
    path = _notes_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}: {text}\n")


# ---------------------------------------------------------------------------
# History loading
# ---------------------------------------------------------------------------

def _load_all_runs(scenario: str) -> list[RunResult]:
    """Load every run for a scenario across all modes, sorted by timestamp."""
    root = _results_root() / scenario
    if not root.is_dir():
        return []
    runs: list[RunResult] = []
    for mode_dir in root.iterdir():
        if not mode_dir.is_dir():
            continue
        for run_dir in sorted(mode_dir.iterdir()):
            result = RunResult.load(run_dir)
            if result:
                runs.append(result)
    runs.sort(key=lambda r: r.timestamp)
    return runs


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def _report_path() -> Path:
    """Path to the generated RESULTS.md."""
    return Path(__file__).parent / "RESULTS.md"


def generate_report() -> Path:
    """Generate RESULTS.md with full history matrix per scenario.

    Returns the path to the generated file.
    """
    root = _results_root()
    scenarios = sorted(d.name for d in root.iterdir() if d.is_dir()) if root.is_dir() else []
    notes = load_notes()

    lines: list[str] = []
    lines.append("# Bakeoff Results")
    lines.append("")
    lines.append(f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

    if not scenarios:
        lines.append("No results yet.")
        out = _report_path()
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out

    for scenario in scenarios:
        lines.append(f"## {scenario}")
        lines.append("")

        # History matrix: all runs chronologically
        runs = _load_all_runs(scenario)
        if not runs:
            lines.append("No runs recorded.")
            lines.append("")
            continue

        # Table header
        lines.append("| # | Timestamp | Mode | Verdict | Tests | Wall Clock | Input Tok | Output Tok | Cost | Exit | Notes |")
        lines.append("|---|-----------|------|---------|-------|------------|-----------|------------|------|------|-------|")

        for i, r in enumerate(runs, 1):
            tr = r.test_result
            verdict = tr.verdict if tr else "--"
            tests = f"{tr.passed}/{tr.total}" if tr else "--"
            inp = _fmt_tokens(r.total_input_tokens)
            out = _fmt_tokens(r.total_output_tokens)
            cost = _fmt_cost(r.estimated_cost_usd)
            exitcode = str(r.exit_code) if r.exit_code != -1 else "timeout"
            note = notes.get(r.timestamp, "")

            lines.append(
                f"| {i} | `{r.timestamp}` | {r.mode} | **{verdict}** | {tests} "
                f"| {r.wall_clock_s}s | {inp} | {out} | {cost} | {exitcode} | {note} |"
            )

        lines.append("")

        # Latest scorecard summary
        lines.append("### Latest by Mode")
        lines.append("")
        latest: dict[str, RunResult] = {}
        for r in runs:
            latest[r.mode] = r  # last one wins since sorted by time

        # Sort modes: canonical first, then extras alphabetically
        active_set = set(latest.keys())
        active = [m for m in _MODE_DISPLAY_ORDER if m in active_set]
        active += sorted(m for m in active_set if m not in _MODE_DISPLAY_ORDER)

        lines.append("| Metric | " + " | ".join(active) + " |")
        lines.append("|--------| " + " | ".join("---" for _ in active) + " |")

        def _metric_row(label: str, fn) -> str:
            vals = [fn(latest[m]) for m in active]
            return f"| {label} | " + " | ".join(vals) + " |"

        lines.append(_metric_row("Verdict", lambda r: f"**{r.test_result.verdict}**" if r.test_result else "--"))
        lines.append(_metric_row("Tests", lambda r: f"{r.test_result.passed}/{r.test_result.total}" if r.test_result else "--"))
        lines.append(_metric_row("Wall clock", lambda r: f"{r.wall_clock_s}s"))
        lines.append(_metric_row("Cost", lambda r: _fmt_cost(r.estimated_cost_usd)))
        lines.append("")

    out = _report_path()
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
