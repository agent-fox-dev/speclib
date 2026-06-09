"""Tool definitions for structured output via Anthropic tool use.

Stub module. Implementation will be added in task group 3.
"""

from __future__ import annotations


def assessment_tools() -> list[dict]:
    """Return tool definitions for PRD assessment."""
    raise NotImplementedError


def refinement_tools() -> list[dict]:
    """Return tool definitions for PRD refinement."""
    raise NotImplementedError


def artifact_tool(artifact_name: str) -> list[dict]:
    """Return tool definition for generating one artifact."""
    raise NotImplementedError
