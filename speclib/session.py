"""Session model stubs for spec 02 types used by spec 03 tests."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class SessionState(enum.Enum):
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
