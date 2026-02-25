"""Parse OLLAMA_DEBUG=1 log output for per-model request stats and swap events.

The debug log contains structured key=value fields on each line. We extract:
- Per-model request counts and prompt token totals from completion lines
- Model swap events from "resetting model to expire" lines
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OllamaModelStats:
    """Aggregated stats for a single model from one run."""

    model: str
    requests: int
    prompt_tokens: int

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "requests": self.requests,
            "prompt_tokens": self.prompt_tokens,
        }


# Patterns for OLLAMA_DEBUG=1 log lines:
# "context for request finished" has runner.name=registry.ollama.ai/library/<model>:<tag>
_RUNNER_NAME_RE = re.compile(r'runner\.name=registry\.ollama\.ai/library/(\S+)')
# "completion request" has prompt=N (token count)
_PROMPT_TOKENS_RE = re.compile(r'\bprompt=(\d+)\b')
# Swap events
_SWAP_RE = re.compile(r'resetting model to expire')


def parse_ollama_log(log_path: Path) -> tuple[list[OllamaModelStats], int]:
    """Parse an Ollama debug log for per-model stats and swap count.

    Returns (per_model_stats, swap_count).
    """
    if not log_path.exists():
        return [], 0

    text = log_path.read_bytes().decode("utf-8", errors="replace")

    # Track per-model aggregates
    model_requests: dict[str, int] = {}
    model_tokens: dict[str, int] = {}
    current_model: str | None = None
    swap_count = 0

    for line in text.splitlines():
        # Track which model is active from "context for request finished" lines
        runner_match = _RUNNER_NAME_RE.search(line)
        if runner_match:
            current_model = runner_match.group(1)

        # Count prompt tokens from "completion request" lines
        if "completion request" in line:
            token_match = _PROMPT_TOKENS_RE.search(line)
            if token_match and current_model:
                tokens = int(token_match.group(1))
                model_requests[current_model] = model_requests.get(current_model, 0) + 1
                model_tokens[current_model] = model_tokens.get(current_model, 0) + tokens

        # Count swaps
        if _SWAP_RE.search(line):
            swap_count += 1

    stats = [
        OllamaModelStats(
            model=model,
            requests=model_requests[model],
            prompt_tokens=model_tokens.get(model, 0),
        )
        for model in sorted(model_requests.keys())
    ]

    return stats, swap_count
