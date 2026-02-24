"""Per-mode environment builders for clawdpot runs.

Each builder returns a complete env dict ready to pass to subprocess.run().
Self-contained — no external dependencies.
"""

from __future__ import annotations

import os
from typing import Optional

# Env vars that prevent claude from running inside another session.
# Bakeoff always runs claude as a subprocess, never a nested session.
_NESTING_GUARD_VARS = ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID")


def _strip_nesting_guards(env: dict[str, str]) -> dict[str, str]:
    """Remove vars that trigger Claude Code's nested-session detection."""
    for key in _NESTING_GUARD_VARS:
        env.pop(key, None)
    return env


def build_native_env() -> dict[str, str]:
    """Build env for native mode — vanilla claude CLI, full Anthropic API.

    Strips all HC_* and ANTHROPIC_* overrides so claude runs with its default
    cloud configuration. This is the control baseline.

    Also used for Mode.HYBRID post-proxy: hybrid mode now routes directly to
    the Anthropic cloud (no proxy intermediary), making it equivalent to native
    for comparison purposes.
    """
    env = os.environ.copy()

    # Strip hermit overrides that would interfere with vanilla claude
    strip_prefixes = ("HC_", "ANTHROPIC_", "OLLAMA_")
    for key in list(env.keys()):
        if any(key.startswith(p) for p in strip_prefixes):
            del env[key]

    # Also strip proxy vars and traffic suppression
    for key in ("HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
                "DISABLE_AUTOUPDATER",
                "CLAUDE_CODE_SUBAGENT_MODEL"):
        env.pop(key, None)

    return _strip_nesting_guards(env)


def build_offline_env(
    model: Optional[str] = None,
    num_ctx: int = 65536,
) -> dict[str, str]:
    """Build env for offline-gpu mode — all traffic stays on local Ollama.

    Self-contained env builder for offline mode.

    Args:
        model: Ollama model tag. Defaults to HC_MODEL or 'gpt-oss:20b'.
        num_ctx: Context window size for Ollama.
    """
    model = model or os.environ.get("HC_MODEL", "gpt-oss:20b")
    env = os.environ.copy()
    env.update({
        # Route all API calls to local Ollama (no /v1 suffix — pitfall)
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:11434",
        "ANTHROPIC_AUTH_TOKEN": "ollama",
        "ANTHROPIC_API_KEY": "",

        # All four tier vars → local model
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
        "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
        "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
        "CLAUDE_CODE_SUBAGENT_MODEL": model,

        # Stability: Ollama lacks count_tokens endpoint
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_AUTOUPDATER": "1",

        # Prevent Ollama cloud traffic
        "OLLAMA_NO_CLOUD": "1",
        "OLLAMA_REMOTES": "",

        # Bogus proxy catches any library that bypasses ANTHROPIC_BASE_URL
        "HTTPS_PROXY": "http://127.0.0.1:1",
        "HTTP_PROXY": "http://127.0.0.1:1",
        "NO_PROXY": "localhost,127.0.0.1,::1",

        # Context window
        "OLLAMA_CONTEXT_LENGTH": str(num_ctx),
    })
    return _strip_nesting_guards(env)
