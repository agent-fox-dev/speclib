"""Spec authoring session state machine, persistence, and validation.

Defines the SpecSession class that tracks the lifecycle of authoring a
single spec within a campaign — from PRD input through assessment,
refinement, and generation. Also defines all session-related data models.

The assess(), refine(), and generate() methods are stubs in this spec;
spec 03 provides their agent implementations.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class SessionState(str, enum.Enum):
    """Session state machine states."""

    INIT = "init"
    ASSESSING = "assessing"
    REFINING = "refining"
    PRD_ACCEPTED = "prd_accepted"
    GENERATING = "generating"
    GENERATED = "generated"


@dataclass
class Question:
    """A structured question the agent asks the user."""

    id: str
    text: str
    context: str
    options: list[str] = field(default_factory=list)
    required: bool = False


@dataclass
class Assessment:
    """Structured evaluation of a PRD."""

    quality: str  # "ready" | "needs_refinement" | "incomplete"
    summary: str
    gaps: list[str] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)


@dataclass
class RepairSuggestion:
    """A suggested repair for a spec artifact."""

    artifact: str
    description: str
    patch: str
    auto_fixable: bool


@dataclass
class ValidationResult:
    """Result of validating a spec via afspec."""

    valid: bool
    schema_errors: list[str] = field(default_factory=list)
    integrity_errors: list[str] = field(default_factory=list)
    repair_suggestions: list[RepairSuggestion] = field(default_factory=list)


@dataclass
class GenerateResult:
    """Result of generating spec artifacts."""

    artifacts: list[str] = field(default_factory=list)
    validation: ValidationResult = field(
        default_factory=lambda: ValidationResult(valid=True)
    )
    warnings: list[str] = field(default_factory=list)


class SpecSession:
    """Stub for spec authoring session.

    Full implementation is provided in task group 5.
    """

    def __init__(self) -> None:
        raise NotImplementedError("SpecSession not yet implemented")
