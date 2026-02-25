"""Scenario discovery and loading for clawdpot.

Each scenario is a subdirectory of clawdpot/scenarios/ containing:
    __init__.py  — NAME, DESCRIPTION, TIMEOUT_S, TOTAL_TESTS constants
    spec.md      — Full task prompt fed to claude -p
    tests/       — pytest test suite (the judge)
    seed/        — (optional) files copied into workdir before the run
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ScenarioInfo:
    """Metadata about a discovered scenario."""

    name: str
    description: str
    timeout_s: int
    total_tests: int
    path: Path
    spec_path: Path
    tests_dir: Path
    seed_dir: Optional[Path]


def _scenarios_root() -> Path:
    """Absolute path to the scenarios/ directory."""
    return Path(__file__).parent


def list_scenarios() -> list[ScenarioInfo]:
    """Discover all available scenarios.

    Scans subdirectories of clawdpot/scenarios/ for valid scenario packages
    (those with __init__.py defining NAME and spec.md existing).
    """
    root = _scenarios_root()
    scenarios = []

    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        init = child / "__init__.py"
        spec = child / "spec.md"
        if not init.exists() or not (spec.exists() or (child / "phase1_spec.md").exists()):
            continue

        info = load_scenario(child.name)
        if info:
            scenarios.append(info)

    return scenarios


def load_scenario(name: str) -> Optional[ScenarioInfo]:
    """Load a single scenario by name.

    Args:
        name: Directory name under clawdpot/scenarios/ (e.g., 'calculator').

    Returns:
        ScenarioInfo if the scenario exists and is valid, None otherwise.
    """
    root = _scenarios_root()
    scenario_dir = root / name
    spec_path = scenario_dir / "spec.md"
    tests_dir = scenario_dir / "tests"

    # Handoff scenarios don't have spec.md, but they have phase1_spec.md and phase2_spec.md
    if not scenario_dir.is_dir() or not (spec_path.exists() or (scenario_dir / "phase1_spec.md").exists()):
        return None

    # Import the scenario's __init__.py to get metadata
    try:
        mod = importlib.import_module(f"clawdpot.scenarios.{name}")
    except ImportError:
        return None

    scenario_name = getattr(mod, "NAME", name)
    description = getattr(mod, "DESCRIPTION", "")
    timeout_s = getattr(mod, "TIMEOUT_S", 600)
    total_tests = getattr(mod, "TOTAL_TESTS", 0)

    seed_dir = scenario_dir / "seed"
    if not seed_dir.is_dir():
        seed_dir = None

    return ScenarioInfo(
        name=scenario_name,
        description=description,
        timeout_s=timeout_s,
        total_tests=total_tests,
        path=scenario_dir,
        spec_path=spec_path,
        tests_dir=tests_dir,
        seed_dir=seed_dir,
    )
