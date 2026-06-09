"""Spec authoring session state machine, persistence, and validation.

Defines the SpecSession class that tracks the lifecycle of authoring a
single spec within a campaign -- from PRD input through assessment,
refinement, and generation. Also defines all session-related data models.

The assess(), refine(), and generate() methods are stubs in this spec;
spec 03 provides their agent implementations.
"""

from __future__ import annotations

import enum
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import afspec  # type: ignore[import-untyped]

from speclib.errors import SessionError

_SESSION_FILE = "_session.json"

# The four required artifacts for validate() and render()
_REQUIRED_ARTIFACTS = frozenset(
    {"prd.md", "requirements.md", "design.md", "test_spec.md"}
)


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


# States from which accept_prd is allowed (02-REQ-4.4)
_ACCEPT_PRD_STATES = frozenset(
    {SessionState.ASSESSING, SessionState.REFINING}
)


class SpecSession:
    """Spec authoring session state machine.

    Tracks the lifecycle of authoring a single spec within a campaign.
    Persists state to ``_session.json`` in the spec directory on every
    state transition.

    The ``assess()``, ``refine()``, and ``generate()`` methods are stubs
    in this spec; spec 03 provides their agent implementations.
    """

    def __init__(
        self,
        spec_dir: Path,
        state: SessionState,
        mode: str,
        prd_path: str,
        assessment_history: list[dict[str, Any]],
        qa_exchanges: list[dict[str, Any]],
        generated_artifacts: list[str],
    ) -> None:
        self._spec_dir = spec_dir
        self._state = state
        self._mode = mode
        self._prd_path = prd_path
        self._assessment_history = assessment_history
        self._qa_exchanges = qa_exchanges
        self._generated_artifacts = generated_artifacts

    @staticmethod
    def _create(spec_dir: Path, mode: str = "interactive") -> SpecSession:
        """Create a new session in init state and persist it.

        This is called by ``Campaign.new_spec()`` to create the initial
        session for a new spec directory.
        """
        session = SpecSession(
            spec_dir=spec_dir,
            state=SessionState.INIT,
            mode=mode,
            prd_path="prd.md",
            assessment_history=[],
            qa_exchanges=[],
            generated_artifacts=[],
        )
        session._persist()
        return session

    @staticmethod
    def resume(spec_dir: Path) -> SpecSession:
        """Resume a session from _session.json.

        Args:
            spec_dir: Path to the spec directory containing
                ``_session.json``.

        Returns:
            A ``SpecSession`` instance in the persisted state.

        Raises:
            SessionError: If ``_session.json`` does not exist or
                contains invalid JSON.
        """
        session_file = spec_dir / _SESSION_FILE
        if not session_file.exists():
            msg = f"Session file not found: {session_file}"
            raise SessionError(msg)

        try:
            data = json.loads(session_file.read_text())
        except json.JSONDecodeError as exc:
            msg = f"Invalid JSON in {session_file}: {exc}"
            raise SessionError(msg) from exc

        return SpecSession(
            spec_dir=spec_dir,
            state=SessionState(data["state"]),
            mode=data.get("mode", "interactive"),
            prd_path=data.get("prd_path", "prd.md"),
            assessment_history=data.get("assessment_history", []),
            qa_exchanges=data.get("qa_exchanges", []),
            generated_artifacts=data.get("generated_artifacts", []),
        )

    def assess(self) -> Assessment:
        """Begin or continue PRD assessment.

        Transitions: init -> assessing, refining -> assessing.
        Stub in this spec: raises NotImplementedError after state check.

        Returns:
            An ``Assessment`` instance.

        Raises:
            SessionError: If current state does not allow assessment.
        """
        self._check_transition("assess", required_states=("init", "refining"))
        # State check passed -- transition would occur here
        # Stub: spec 03 provides the implementation
        raise NotImplementedError(
            "assess() is a stub; spec 03 provides implementation"
        )

    def refine(self, answers: dict[str, str]) -> Assessment:
        """Refine assessment with user answers.

        Transitions: assessing -> refining.
        Stub in this spec: raises NotImplementedError after state check.

        Args:
            answers: Dict mapping question IDs to user answers.

        Returns:
            An ``Assessment`` instance.

        Raises:
            SessionError: If current state is not assessing.
        """
        self._check_transition("refine", required_states=("assessing",))
        # State check passed -- transition would occur here
        # Stub: spec 03 provides the implementation
        raise NotImplementedError(
            "refine() is a stub; spec 03 provides implementation"
        )

    def accept_prd(self) -> None:
        """Accept the PRD as-is (skip or complete assessment).

        Transitions: init -> prd_accepted (one-shot mode),
        assessing -> prd_accepted, refining -> prd_accepted.

        Raises:
            SessionError: If current state does not allow acceptance.
        """
        if self._state not in _ACCEPT_PRD_STATES:
            allowed = ", ".join(
                sorted(s.value for s in _ACCEPT_PRD_STATES)
            )
            msg = (
                f"Cannot accept PRD in state {self._state.value!r}; "
                f"allowed states: {allowed}"
            )
            raise SessionError(msg)

        self._state = SessionState.PRD_ACCEPTED
        self._persist()

    def generate(self) -> GenerateResult:
        """Generate spec artifacts from the accepted PRD.

        Transitions: prd_accepted -> generating.
        Stub in this spec: raises NotImplementedError after state check.

        Returns:
            A ``GenerateResult`` instance.

        Raises:
            SessionError: If current state is not prd_accepted.
        """
        self._check_transition(
            "generate", required_states=("prd_accepted",)
        )
        # State check passed -- transition would occur here
        # Stub: spec 03 provides the implementation
        raise NotImplementedError(
            "generate() is a stub; spec 03 provides implementation"
        )

    def validate(self) -> ValidationResult:
        """Validate the spec using afspec.

        Checks that all four required artifacts exist, then delegates to
        ``afspec.load_spec()`` and ``afspec.validate()``.

        Returns:
            A ``ValidationResult`` instance.

        Raises:
            SessionError: If required artifacts are missing.
        """
        self._check_artifacts()

        spec = afspec.load_spec(self._spec_dir)
        result: ValidationResult = afspec.validate(spec)
        return result

    def render(self, combined: bool = False) -> str | dict[str, str]:
        """Render the spec using afspec.

        Args:
            combined: If ``True``, returns a single combined markdown
                string. If ``False``, returns a dict mapping artifact
                name to markdown string.

        Returns:
            Combined markdown string or dict of artifact markdowns.

        Raises:
            SessionError: If required artifacts are missing.
        """
        self._check_artifacts()

        spec = afspec.load_spec(self._spec_dir)

        if combined:
            rendered: str = afspec.render_combined(spec)
            return rendered
        individual: dict[str, str] = afspec.render_individual(spec)
        return individual

    @property
    def state(self) -> SessionState:
        """Current session state."""
        return self._state

    @property
    def spec_dir(self) -> Path:
        """Spec directory path."""
        return self._spec_dir

    @property
    def assessment(self) -> Assessment | None:
        """Most recent assessment, or None if not yet assessed."""
        if not self._assessment_history:
            return None
        last = self._assessment_history[-1]
        questions = [
            Question(
                id=q["id"],
                text=q["text"],
                context=q["context"],
                options=q.get("options", []),
                required=q.get("required", False),
            )
            for q in last.get("questions", [])
        ]
        return Assessment(
            quality=last["quality"],
            summary=last["summary"],
            gaps=last.get("gaps", []),
            questions=questions,
        )

    def _check_transition(
        self,
        method: str,
        required_states: tuple[str, ...],
    ) -> None:
        """Check if a state transition is legal.

        Args:
            method: The method name being called.
            required_states: Tuple of state values that allow this
                transition.

        Raises:
            SessionError: If the current state is not in
                required_states.
        """
        if self._state.value not in required_states:
            allowed = ", ".join(required_states)
            msg = (
                f"Cannot call {method}() in state "
                f"{self._state.value!r}; "
                f"requires state: {allowed}"
            )
            raise SessionError(msg)

    def _check_artifacts(self) -> None:
        """Check that all four required artifacts exist.

        Raises:
            SessionError: If any required artifact is missing,
                listing the missing artifact names.
        """
        missing = [
            name
            for name in sorted(_REQUIRED_ARTIFACTS)
            if not (self._spec_dir / name).exists()
        ]
        if missing:
            msg = (
                f"Missing required artifacts in {self._spec_dir}: "
                f"{', '.join(missing)}"
            )
            raise SessionError(msg)

    def _persist(self) -> None:
        """Atomically write the session state to _session.json.

        Uses a temporary file and rename for crash safety.
        """
        data = {
            "state": self._state.value,
            "prd_path": self._prd_path,
            "assessment_history": self._assessment_history,
            "qa_exchanges": self._qa_exchanges,
            "generated_artifacts": self._generated_artifacts,
            "mode": self._mode,
        }
        content = json.dumps(data, indent=2)

        target = self._spec_dir / _SESSION_FILE
        fd, tmp_path_str = tempfile.mkstemp(
            dir=self._spec_dir, suffix=".tmp"
        )
        try:
            os.close(fd)
            Path(tmp_path_str).write_text(content)
            Path(tmp_path_str).rename(target)
        except BaseException:
            Path(tmp_path_str).unlink(missing_ok=True)
            raise
