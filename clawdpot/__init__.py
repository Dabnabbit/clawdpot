"""clawdpot — Model competition system for Claude Code.

Throw models in, see which one comes out on top. Gives the same coding task
to multiple modes (native cloud, offline local) and scores the results using
pre-written pytest test suites as the judge.

Usage:
    python -m clawdpot list                          # Show scenarios
    python -m clawdpot run calculator --mode native  # Single mode
    python -m clawdpot run calculator --all          # All three modes
    python -m clawdpot score calculator              # Compare results
"""
