"""Data models for the clawdpot competition system.

Mode enum, RunResult, StatsSnapshot, TestResult, ScoreCard — all the typed
structures that flow through runner → scorer → CLI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Mode(str, Enum):
    """Competition modes."""

    NATIVE = "native"
    HYBRID = "hybrid"
    OFFLINE = "offline"
    OFFLINE_CPU = "offline-cpu"
    GSD = "gsd"


ALL_MODES = [Mode.NATIVE, Mode.HYBRID, Mode.OFFLINE, Mode.OFFLINE_CPU]


@dataclass
class TestResult:
    """Pytest judge results for a single run."""

    passed: int = 0
    failed: int = 0
    errors: int = 0
    total: int = 0
    output: str = ""

    @property
    def verdict(self) -> str:
        if self.total == 0:
            return "no-tests"
        if self.passed == self.total:
            return "pass"
        if self.passed > 0:
            return "partial"
        return "fail"


@dataclass
class StatsSnapshot:
    """Snapshot of ~/.claude/stats-cache.json modelUsage at a point in time.

    Used before/after a run to compute token deltas.
    """

    model_usage: dict[str, dict[str, int]] = field(default_factory=dict)

    @classmethod
    def capture(cls, path: Optional[Path] = None) -> StatsSnapshot:
        """Read current stats-cache.json and extract modelUsage."""
        p = path or Path.home() / ".claude" / "stats-cache.json"
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            raw = data.get("modelUsage", {})
            # Extract the token fields we care about
            usage: dict[str, dict[str, int]] = {}
            for model, vals in raw.items():
                usage[model] = {
                    "inputTokens": vals.get("inputTokens", 0),
                    "outputTokens": vals.get("outputTokens", 0),
                    "cacheReadInputTokens": vals.get("cacheReadInputTokens", 0),
                    "cacheCreationInputTokens": vals.get("cacheCreationInputTokens", 0),
                }
            return cls(model_usage=usage)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return cls()

    @staticmethod
    def token_delta(
        before: StatsSnapshot, after: StatsSnapshot
    ) -> dict[str, dict[str, int]]:
        """Compute per-model token differences between two snapshots."""
        delta: dict[str, dict[str, int]] = {}
        all_models = set(before.model_usage) | set(after.model_usage)
        for model in all_models:
            b = before.model_usage.get(model, {})
            a = after.model_usage.get(model, {})
            d = {}
            for key in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens"):
                diff = a.get(key, 0) - b.get(key, 0)
                if diff > 0:
                    d[key] = diff
            if d:
                delta[model] = d
        return delta


@dataclass
class RunResult:
    """Complete result of a single clawdpot run."""

    scenario: str
    mode: str
    timestamp: str
    wall_clock_s: float = 0.0
    exit_code: int = -1
    stdout_path: str = ""
    stderr_path: str = ""
    workdir: str = ""

    # Token usage (delta between before/after snapshots)
    token_delta: dict[str, dict[str, int]] = field(default_factory=dict)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    # Judge results
    test_result: Optional[TestResult] = None

    # Model identification (for per-model baselining)
    model_name: str = ""

    # Ollama debug log stats (per-model request counts + prompt tokens)
    ollama_model_stats: list[dict] = field(default_factory=list)
    ollama_swap_count: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        d = {
            "scenario": self.scenario,
            "mode": self.mode,
            "timestamp": self.timestamp,
            "wall_clock_s": self.wall_clock_s,
            "exit_code": self.exit_code,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "workdir": self.workdir,
            "token_delta": self.token_delta,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "model_name": self.model_name,
            "ollama_model_stats": self.ollama_model_stats,
            "ollama_swap_count": self.ollama_swap_count,
        }
        if self.test_result:
            d["test_result"] = {
                "passed": self.test_result.passed,
                "failed": self.test_result.failed,
                "errors": self.test_result.errors,
                "total": self.test_result.total,
                "verdict": self.test_result.verdict,
            }
        return d

    @classmethod
    def from_dict(cls, d: dict) -> RunResult:
        """Deserialize from a JSON dict (metrics.json)."""
        tr_data = d.get("test_result")
        tr = None
        if tr_data:
            tr = TestResult(
                passed=tr_data.get("passed", 0),
                failed=tr_data.get("failed", 0),
                errors=tr_data.get("errors", 0),
                total=tr_data.get("total", 0),
            )
        return cls(
            scenario=d.get("scenario", ""),
            mode=d.get("mode", ""),
            timestamp=d.get("timestamp", ""),
            wall_clock_s=d.get("wall_clock_s", 0.0),
            exit_code=d.get("exit_code", -1),
            stdout_path=d.get("stdout_path", ""),
            stderr_path=d.get("stderr_path", ""),
            workdir=d.get("workdir", ""),
            token_delta=d.get("token_delta", {}),
            total_input_tokens=d.get("total_input_tokens", 0),
            total_output_tokens=d.get("total_output_tokens", 0),
            estimated_cost_usd=d.get("estimated_cost_usd", 0.0),
            test_result=tr,
            model_name=d.get("model_name", ""),
            ollama_model_stats=d.get("ollama_model_stats", []),
            ollama_swap_count=d.get("ollama_swap_count", 0),
        )

    def save(self, result_dir: Path) -> None:
        """Write metrics.json to the result directory."""
        result_dir.mkdir(parents=True, exist_ok=True)
        (result_dir / "metrics.json").write_text(
            json.dumps(self.to_dict(), indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, result_dir: Path) -> Optional[RunResult]:
        """Load metrics.json from a result directory."""
        p = result_dir / "metrics.json"
        if not p.exists():
            return None
        try:
            return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return None


@dataclass
class ScoreCard:
    """Comparison of RunResults across modes for a single scenario."""

    scenario: str
    results: dict[str, RunResult] = field(default_factory=dict)
