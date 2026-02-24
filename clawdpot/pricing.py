"""Model classification and cost estimation for clawdpot runs.

Provides model family detection (Anthropic vs local) and per-token cost
estimation using public Anthropic API rates.
"""

from __future__ import annotations

from enum import Enum


class ModelFamily(str, Enum):
    """Anthropic model family classification."""

    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"
    LOCAL = "local"
    UNKNOWN = "unknown"


def classify_model(name: str) -> ModelFamily:
    """Classify a model name into an Anthropic model family.

    Checks for Anthropic family keywords first.  Models without a known
    Anthropic keyword but containing 'claude' or 'anthropic' are UNKNOWN.
    Everything else is LOCAL (Ollama-served).

    Args:
        name: Model identifier (e.g., "claude-opus-4-6", "gpt-oss:20b").

    Returns:
        ModelFamily enum value.
    """
    n = name.lower()
    if "opus" in n:
        return ModelFamily.OPUS
    if "sonnet" in n:
        return ModelFamily.SONNET
    if "haiku" in n:
        return ModelFamily.HAIKU
    if any(k in n for k in ("claude", "anthropic")):
        return ModelFamily.UNKNOWN
    return ModelFamily.LOCAL


# Public API rates per 1M tokens: (input, output)
# Cache read tokens are 90% cheaper than input tokens for all tiers.
# Cache creation tokens are 25% more expensive than input tokens.
_RATES: dict[ModelFamily, tuple[float, float]] = {
    ModelFamily.OPUS: (15.00, 75.00),
    ModelFamily.SONNET: (3.00, 15.00),
    ModelFamily.HAIKU: (0.80, 4.00),
}

_CACHE_READ_DISCOUNT = 0.10  # cache reads cost 10% of input price
_CACHE_CREATION_MARKUP = 1.25  # cache creation costs 125% of input price


def estimate_cost(
    family: ModelFamily,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> float:
    """Estimate USD cost from token counts using public Anthropic rates.

    Args:
        family: Model family for rate lookup.
        input_tokens: Non-cached input tokens.
        output_tokens: Output tokens.
        cache_read_tokens: Cached input tokens (90% discount).
        cache_creation_tokens: Cache creation tokens (25% markup).

    Returns:
        Estimated cost in USD.  Returns 0.0 for LOCAL/UNKNOWN families.
    """
    rates = _RATES.get(family)
    if not rates:
        return 0.0
    input_rate, output_rate = rates
    return (
        (input_tokens / 1e6) * input_rate
        + (output_tokens / 1e6) * output_rate
        + (cache_read_tokens / 1e6) * input_rate * _CACHE_READ_DISCOUNT
        + (cache_creation_tokens / 1e6) * input_rate * _CACHE_CREATION_MARKUP
    )
