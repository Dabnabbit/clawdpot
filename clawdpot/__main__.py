"""CLI for the clawdpot model competition system.

Usage:
    python -m clawdpot list                          # Show available scenarios
    python -m clawdpot run calculator --mode native  # Single mode
    python -m clawdpot run calculator --all          # All three modes
    python -m clawdpot score calculator              # Compare latest results
    python -m clawdpot results                       # List all stored results
    python -m clawdpot report                        # Generate RESULTS.md history
    python -m clawdpot note <timestamp> <text>       # Annotate a run
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from clawdpot.models import Mode, ScoreCard
from clawdpot.runner import run_all_modes, run_scenario, run_handoff
from clawdpot.scenarios import list_scenarios
from clawdpot.scorer import generate_report, list_all_results, load_scorecard, render_scorecard, save_note

app = typer.Typer(
    name="clawdpot",
    help="Model competition system for Claude Code",
    no_args_is_help=True,
)
console = Console(stderr=True)


@app.command("list")
def cmd_list() -> None:
    """Show available scenarios."""
    scenarios = list_scenarios()
    if not scenarios:
        console.print("[yellow]No scenarios found.[/yellow]")
        raise typer.Exit(1)

    table = Table(title="Available Scenarios", show_header=True, header_style="bold")
    table.add_column("Name", style="green", min_width=15)
    table.add_column("Description", min_width=30)
    table.add_column("Tests", justify="right")
    table.add_column("Timeout", justify="right")

    for s in scenarios:
        table.add_row(s.name, s.description, str(s.total_tests), f"{s.timeout_s}s")

    console.print()
    console.print(table)
    console.print()


@app.command("run")
def cmd_run(
    scenario: str = typer.Argument(help="Scenario name (e.g., 'calculator')"),
    mode: Optional[str] = typer.Option(None, "--mode", "-m", help="Mode: native, hybrid, offline, offline-cpu, gsd"),
    all_modes: bool = typer.Option(False, "--all", "-a", help="Run all three classic modes"),
    model: Optional[str] = typer.Option(None, "--model", help="Override primary/orchestrator model"),
    background_model: Optional[str] = typer.Option(None, "--background-model", help="Subagent model for GSD mode"),
    num_ctx: int = typer.Option(65536, "--num-ctx", help="Context window for offline mode"),
    skip_preflight: bool = typer.Option(False, "--skip-preflight", help="Skip GPU preflight check for offline-cpu mode"),
) -> None:
    """Run a scenario against one or all modes."""
    if all_modes:
        results = run_all_modes(scenario, console, model=model, num_ctx=num_ctx)
        # Show scorecard after all runs
        console.print("\n[bold]--- Final Scorecard ---[/bold]")
        card = load_scorecard(scenario)
        render_scorecard(card, console)
    elif mode:
        try:
            m = Mode(mode)
        except ValueError:
            console.print(f"[red]Invalid mode: {mode}[/red]. Choose: native, hybrid, offline, offline-cpu, gsd")
            raise typer.Exit(1)
        run_scenario(
            scenario, m, console,
            model=model, background_model=background_model,
            num_ctx=num_ctx, skip_preflight=skip_preflight,
        )
    else:
        console.print("[red]Specify --mode or --all[/red]")
        raise typer.Exit(1)


@app.command("handoff")
def cmd_handoff(
    scenario: str = typer.Argument(help="Scenario name (e.g., 'api_server_handoff')"),
    phase1_mode: str = typer.Option(..., "--phase1-mode", help="First phase mode: native, hybrid, offline, offline-cpu, gsd"),
    phase2_mode: str = typer.Option(..., "--phase2-mode", help="Second phase mode: native, hybrid, offline, offline-cpu, gsd"),
    model: Optional[str] = typer.Option(None, "--model", help="Override model for both phases"),
    phase1_model: Optional[str] = typer.Option(None, "--phase1-model", help="Override model for first phase"),
    phase2_model: Optional[str] = typer.Option(None, "--phase2-model", help="Override model for second phase"),
    num_ctx: int = typer.Option(65536, "--num-ctx", help="Context window for offline mode"),
) -> None:
    """Run a scenario with two phases (handoff)."""
    try:
        m1 = Mode(phase1_mode)
        m2 = Mode(phase2_mode)
    except ValueError:
        console.print(f"[red]Invalid mode. Choose: native, hybrid, offline, offline-cpu, gsd[/red]")
        raise typer.Exit(1)

    result = run_handoff(
        scenario, m1, m2, console,
        model=model,
        phase1_model=phase1_model,
        phase2_model=phase2_model,
        num_ctx=num_ctx,
    )

    # Show scorecard for the handoff run
    if result:
        console.print("\n[bold]--- Handoff Scorecard ---[/bold]")
        card = load_scorecard(scenario)
        # Filter the card to show only this specific run
        filtered_card = ScoreCard(scenario=scenario)
        filtered_card.results = {result.mode: result}
        render_scorecard(filtered_card, console)


@app.command("score")
def cmd_score(
    scenario: str = typer.Argument(help="Scenario name (e.g., 'calculator')"),
) -> None:
    """Compare latest results for a scenario across modes."""
    card = load_scorecard(scenario)
    render_scorecard(card, console)


@app.command("results")
def cmd_results() -> None:
    """List all stored results."""
    list_all_results(console)


@app.command("report")
def cmd_report() -> None:
    """Generate RESULTS.md with full history matrix and notes."""
    path = generate_report()
    console.print(f"Report written to {path}")


@app.command("note")
def cmd_note(
    timestamp: str = typer.Argument(help="Run timestamp (e.g., '20260223T024533Z')"),
    text: str = typer.Argument(help="Note text to attach to the run"),
) -> None:
    """Annotate a run with a note (appears in report)."""
    save_note(timestamp, text)
    console.print(f"Note saved for {timestamp}")


if __name__ == "__main__":
    app()
