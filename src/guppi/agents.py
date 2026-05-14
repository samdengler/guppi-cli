"""Agent target registry for skill registration."""

from pathlib import Path

AGENT_TARGETS = {
    "Claude": Path.home() / ".claude" / "skills",
    "Kiro": Path.home() / ".kiro" / "skills",
}


def get_active_targets() -> dict[str, Path]:
    """Return agent targets whose parent config directory exists."""
    return {
        name: path
        for name, path in AGENT_TARGETS.items()
        if path.parent.exists()
    }
