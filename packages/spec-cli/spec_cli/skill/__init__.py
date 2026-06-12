"""Agent CLI skill for spec authoring.

Exports the path to the skill prompt file and utilities for installing
it into agent CLI configuration directories.
"""

from __future__ import annotations

from pathlib import Path

SKILL_FILE_PATH: Path = Path(__file__).parent / "spec.md"
"""Absolute path to the spec skill markdown file within the package."""

AGENT_TARGETS: dict[str, Path] = {
    "claude": Path(".claude") / "skills",
    "gemini": Path(".gemini") / "skills",
}
"""Mapping of agent CLI name to its skill directory (relative to home)."""


def detect_agent_cli() -> str | None:
    """Detect installed agent CLI by checking config directories.

    Checks for ``~/.claude/`` and ``~/.gemini/`` and returns the name
    of the first agent CLI whose parent configuration directory exists.
    Returns ``None`` if no supported agent CLI is detected.
    """
    home = Path.home()
    for name in AGENT_TARGETS:
        # Check the agent's config root (e.g. ~/.claude/), not the
        # skills subdirectory which may not exist yet.
        config_root = home / f".{name}"
        if config_root.exists():
            return name
    return None
