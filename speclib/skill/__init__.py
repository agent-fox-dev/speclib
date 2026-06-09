"""Agent CLI skill for spec authoring.

Exports the path to the skill prompt file and utilities for installing
it into agent CLI configuration directories.
"""

from __future__ import annotations

from pathlib import Path

SKILL_FILE_PATH: Path = Path(__file__).parent / "af-spec.md"
"""Absolute path to the af-spec skill markdown file within the package."""
