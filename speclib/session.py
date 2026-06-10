"""Spec authoring session state machine, persistence, and validation.

Defines the SpecSession class that tracks the lifecycle of authoring a
single spec within a campaign -- from PRD input through assessment,
refinement, and generation. Also defines all session-related data models.

The assess(), refine(), and generate() methods delegate to SpecAgent
for AI-driven operations (spec 03 implementation).
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

from speclib.agent import SpecAgent
from speclib.auth import create_client
from speclib.errors import AgentError, SessionError

_SESSION_FILE = "_session.json"
_DEFAULT_MODEL = "claude-sonnet-4-6"

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

    The ``assess()``, ``refine()``, and ``generate()`` methods delegate
    to ``SpecAgent`` for AI-driven PRD evaluation and artifact generation.
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
        self._last_error: str | None = None

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

    async def assess(self) -> Assessment:
        """Begin or continue PRD assessment.

        Creates a ``SpecAgent``, sends the PRD for assessment, persists
        the returned ``Assessment`` to ``_session.json``, and transitions
        state to ``assessing``.

        Transitions: init -> assessing, refining -> assessing.

        Returns:
            An ``Assessment`` instance.

        Raises:
            SessionError: If current state does not allow assessment.
            AgentError: If the API call fails or the response cannot
                be parsed.
        """
        self._check_transition("assess", required_states=("init", "refining"))

        prd_text = (self._spec_dir / self._prd_path).read_text()
        spec_name = self._spec_dir.name

        agent = _create_agent()

        try:
            assessment = await agent.assess_prd(prd_text, spec_name)
        except AgentError as exc:
            self._last_error = exc.detail
            self._persist()
            raise

        self._assessment_history.append(
            _assessment_to_dict(assessment)
        )
        self._state = SessionState.ASSESSING
        self._last_error = None
        self._persist()

        return assessment

    async def refine(self, answers: dict[str, str]) -> Assessment:
        """Refine assessment with user answers.

        Creates a ``SpecAgent``, sends the PRD with answers and the
        previous assessment for refinement, updates ``prd.md`` with the
        returned text, persists the new ``Assessment``, and transitions
        state to ``refining``.

        Transitions: assessing -> refining.

        Args:
            answers: Dict mapping question IDs to user answers.

        Returns:
            An ``Assessment`` instance.

        Raises:
            SessionError: If current state is not assessing.
            AgentError: If the API call fails or the response cannot
                be parsed.
        """
        self._check_transition(
            "refine", required_states=("assessing", "refining")
        )

        prd_text = (self._spec_dir / self._prd_path).read_text()
        previous_assessment = self.assessment
        if previous_assessment is None:
            raise AgentError("Cannot refine without a previous assessment")

        assessment_index = len(self._assessment_history) - 1
        timestamp = _utcnow()

        agent = _create_agent()

        try:
            updated_prd, new_assessment = await agent.refine_prd(
                prd_text, answers, previous_assessment
            )
        except AgentError as exc:
            self._last_error = exc.detail
            self._persist()
            raise

        # Update PRD file with the revised text
        (self._spec_dir / self._prd_path).write_text(updated_prd)

        # Record the QA exchange (07-REQ-1.1)
        self._qa_exchanges.append({
            "assessment_index": assessment_index,
            "answers": dict(answers),
            "timestamp": timestamp,
        })

        self._assessment_history.append(
            _assessment_to_dict(new_assessment)
        )
        self._state = SessionState.REFINING
        self._last_error = None
        self._persist()

        return new_assessment

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

    async def generate(self) -> GenerateResult:
        """Generate spec artifacts from the accepted PRD.

        Creates a ``SpecAgent`` and generates three artifacts
        (requirements, test_spec, tasks) sequentially.  Each artifact
        is written to disk as it is generated so that partial results
        survive failures.  On resume after a partial failure, existing
        artifacts are detected and only missing ones are regenerated.

        Transitions: prd_accepted -> generating -> generated.

        Returns:
            A ``GenerateResult`` instance.

        Raises:
            SessionError: If current state is not prd_accepted or
                generating.
            AgentError: If the API call fails, the model does not
                produce structured output, or an artifact fails schema
                validation.
        """
        self._check_transition(
            "generate", required_states=("prd_accepted", "generating")
        )

        # Transition to GENERATING immediately for partial-failure
        # support (03-REQ-6.E1)
        if self._state != SessionState.GENERATING:
            self._state = SessionState.GENERATING
            self._persist()

        prd_text = (self._spec_dir / self._prd_path).read_text()
        spec_name = self._spec_dir.name

        agent = _create_agent()

        # Detect existing artifacts for resume (03-REQ-6.E2)
        existing: dict[str, Any] = {}
        artifact_names = ["requirements", "test_spec", "tasks"]
        for name in artifact_names:
            path = self._spec_dir / f"{name}.json"
            if path.exists():
                existing[name] = json.loads(path.read_text())

        def _write_artifact(name: str, content: dict[str, Any]) -> None:
            """Write a single artifact to disk incrementally."""
            path = self._spec_dir / f"{name}.json"
            path.write_text(json.dumps(content, indent=2))

        try:
            artifacts = await agent.generate_artifacts(
                prd_text,
                spec_name,
                spec_name,
                existing_artifacts=existing if existing else None,
                on_artifact=_write_artifact,
            )
        except AgentError as exc:
            self._last_error = exc.detail
            self._persist()
            raise

        # Write any artifacts not yet on disk (covers the case where
        # SpecAgent is mocked and the on_artifact callback was not
        # invoked)
        for name, content in artifacts.items():
            path = self._spec_dir / f"{name}.json"
            if not path.exists():
                path.write_text(json.dumps(content, indent=2))

        # Cross-file validation via afspec (03-REQ-6.3)
        afspec.validate(self._spec_dir)

        self._generated_artifacts = list(artifacts.keys())
        self._state = SessionState.GENERATED
        self._last_error = None
        self._persist()

        return GenerateResult(artifacts=list(artifacts.keys()))

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

    def pending_questions(self) -> list[dict[str, Any]]:
        """Return questions from the latest assessment as serializable dicts.

        Returns an empty list if no assessment exists. Does not trigger
        a state transition.
        """
        if not self._assessment_history:
            return []
        last = self._assessment_history[-1]
        return [
            {
                "id": q["id"],
                "text": q["text"],
                "context": q["context"],
                "options": q.get("options", []),
                "required": q.get("required", False),
            }
            for q in last.get("questions", [])
        ]

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
        data: dict[str, Any] = {
            "state": self._state.value,
            "prd_path": self._prd_path,
            "assessment_history": self._assessment_history,
            "qa_exchanges": self._qa_exchanges,
            "generated_artifacts": self._generated_artifacts,
            "mode": self._mode,
        }
        if self._last_error is not None:
            data["last_error"] = self._last_error
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


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _utcnow() -> str:
    """Return current UTC time as ISO 8601 string. Patchable in tests."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _create_agent() -> SpecAgent:
    """Create a SpecAgent from the configured auth client.

    Handles the ``create_client()`` return value which is a tuple
    ``(client, model)`` in production, but may be a single mock object
    in tests.
    """
    result = create_client()
    if isinstance(result, tuple):
        client, model = result
    else:
        client, model = result, _DEFAULT_MODEL
    return SpecAgent(client, model)


def _assessment_to_dict(assessment: Assessment) -> dict[str, Any]:
    """Convert an Assessment dataclass to a dict for JSON persistence."""
    return {
        "quality": assessment.quality,
        "summary": assessment.summary,
        "gaps": assessment.gaps,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "context": q.context,
                "options": q.options,
                "required": q.required,
            }
            for q in assessment.questions
        ],
    }
