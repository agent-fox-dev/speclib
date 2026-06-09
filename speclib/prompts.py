"""Prompt templates for agent pipeline operations.

Stub module. Implementation will be added in task group 4.
"""

from __future__ import annotations

from typing import Any


def assessment_system_prompt() -> str:
    """Return the system prompt for PRD assessment."""
    raise NotImplementedError


def assessment_user_prompt(prd_text: str, spec_name: str) -> str:
    """Return the user message for PRD assessment."""
    raise NotImplementedError


def refinement_system_prompt() -> str:
    """Return the system prompt for PRD refinement."""
    raise NotImplementedError


def refinement_user_prompt(
    prd_text: str,
    answers: dict[str, str],
    previous_assessment: object,
) -> str:
    """Return the user message for PRD refinement."""
    raise NotImplementedError


def generation_system_prompt() -> str:
    """Return the system prompt for artifact generation."""
    raise NotImplementedError


def generation_user_prompt(
    prd_text: str,
    artifact_name: str,
    prior_artifacts: dict[str, Any] | None = None,
) -> str:
    """Return the user message for generating one artifact."""
    raise NotImplementedError
