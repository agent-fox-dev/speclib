"""Tests for spec authoring session state machine and persistence.

Test Spec Entries: TS-02-10 through TS-02-19 (acceptance criteria),
TS-02-E7 through TS-02-E11 (edge cases),
TS-02-P1, TS-02-P2, TS-02-P5, TS-02-P6 (property tests),
TS-02-SMOKE-3 through TS-02-SMOKE-5 (integration smoke tests).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from speclib.campaign import Campaign
from speclib.errors import SessionError
from speclib.session import (
    SessionState,
    SpecSession,
    ValidationResult,
)

# Methods that became async in spec 03 (agent integration).
_ASYNC_METHODS = frozenset({"assess", "refine", "generate"})


def _run_sync(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine synchronously for spec-02 tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# ---------------------------------------------------------------------------
# Helper: create a session in a specific state for testing
# ---------------------------------------------------------------------------

def _create_session(tmp_path: Path, state: SessionState | None = None) -> SpecSession:
    """Create a SpecSession in a spec directory, optionally in a given state.

    Uses Campaign.new_spec to create the session in init state, then
    directly writes the desired state to _session.json for test setup.
    """
    camp_dir = tmp_path / "camp"
    if not (camp_dir / "campaign.yaml").exists():
        Campaign.create(camp_dir, "Test", "Desc")
    camp = Campaign.open(camp_dir)

    # Create a new spec each call (unique name from state)
    spec_name = f"s_{state.value if state else 'init'}".replace(" ", "_")
    session = camp.new_spec(spec_name, "PRD content")

    if state is not None and state != SessionState.INIT:
        # Directly set state in _session.json for test precondition setup
        session_file = session.spec_dir / "_session.json"
        data = json.loads(session_file.read_text())
        data["state"] = state.value
        session_file.write_text(json.dumps(data))
        # Resume to get a session in the desired state
        session = SpecSession.resume(session.spec_dir)

    return session


def _create_session_with_all_artifacts(tmp_path: Path) -> SpecSession:
    """Create a SpecSession whose spec dir has all four required artifacts."""
    camp_dir = tmp_path / "camp_artifacts"
    if not (camp_dir / "campaign.yaml").exists():
        Campaign.create(camp_dir, "Test", "Desc")
    camp = Campaign.open(camp_dir)
    session = camp.new_spec("full_spec", "# PRD\n\nContent")

    # Create the four required artifacts
    spec_dir = session.spec_dir
    for artifact in ["requirements.md", "design.md", "test_spec.md"]:
        (spec_dir / artifact).write_text(f"# {artifact}\n\nPlaceholder content")

    return session


# ---------------------------------------------------------------------------
# Acceptance criterion tests: TS-02-10 through TS-02-19
# ---------------------------------------------------------------------------


class TestSessionStateEnum:
    """Tests for SessionState enum — TS-02-10."""

    def test_ts02_10_session_state_enum_values(self) -> None:
        """TS-02-10: SessionState enum has all six required values.

        Requirement: 02-REQ-4.1
        """
        assert SessionState.INIT.value == "init"
        assert SessionState.ASSESSING.value == "assessing"
        assert SessionState.REFINING.value == "refining"
        assert SessionState.PRD_ACCEPTED.value == "prd_accepted"
        assert SessionState.GENERATING.value == "generating"
        assert SessionState.GENERATED.value == "generated"
        assert len(SessionState) == 6


class TestStateTransitions:
    """Tests for session state machine transitions — TS-02-11 through TS-02-13."""

    def test_ts02_11_legal_state_transitions(self, tmp_path: Path) -> None:
        """TS-02-11: Legal transitions succeed, illegal transitions raise SessionError.

        Requirement: 02-REQ-4.2

        Legal transitions (from design.md):
          init -> assessing (assess)
          assessing -> refining (refine)
          assessing -> prd_accepted (accept_prd)
          refining -> assessing (assess)
          refining -> prd_accepted (accept_prd)
          prd_accepted -> generating (generate)

        The async methods (assess, refine, generate) are now implemented
        by spec 03.  For legal transitions we verify that the state check
        passes (no SessionError).  Full agent behaviour is exercised in
        test_session_agent.py.
        """
        # Legal: init -> assessing via assess()
        # assess() is async; verify no SessionError (state check passes)
        session = _create_session(tmp_path, SessionState.INIT)
        try:
            _run_sync(session.assess())
        except SessionError:
            pytest.fail("Legal transition init->assess raised SessionError")
        except Exception:
            pass  # Implementation error (no client) is fine

        # Illegal: init -> refining via refine()
        session = _create_session(tmp_path, SessionState.INIT)
        with pytest.raises(SessionError):
            _run_sync(session.refine({}))

        # Illegal: init -> generating via generate()
        session = _create_session(tmp_path, SessionState.INIT)
        with pytest.raises(SessionError):
            _run_sync(session.generate())

        # Legal: assessing -> refining via refine()
        session = _create_session(tmp_path, SessionState.ASSESSING)
        try:
            _run_sync(session.refine({}))
        except SessionError:
            pytest.fail("Legal transition assessing->refine raised SessionError")
        except Exception:
            pass

        # Legal: assessing -> prd_accepted via accept_prd()
        session = _create_session(tmp_path, SessionState.ASSESSING)
        session.accept_prd()
        assert session.state == SessionState.PRD_ACCEPTED

        # Legal: refining -> assessing via assess()
        session = _create_session(tmp_path, SessionState.REFINING)
        try:
            _run_sync(session.assess())
        except SessionError:
            pytest.fail("Legal transition refining->assess raised SessionError")
        except Exception:
            pass

        # Legal: refining -> prd_accepted via accept_prd()
        session = _create_session(tmp_path, SessionState.REFINING)
        session.accept_prd()
        assert session.state == SessionState.PRD_ACCEPTED

        # Legal: prd_accepted -> generating via generate()
        session = _create_session(tmp_path, SessionState.PRD_ACCEPTED)
        try:
            _run_sync(session.generate())
        except SessionError:
            pytest.fail("Legal transition prd_accepted->generate raised SessionError")
        except Exception:
            pass

        # Illegal: prd_accepted -> assess()
        session = _create_session(tmp_path, SessionState.PRD_ACCEPTED)
        with pytest.raises(SessionError):
            _run_sync(session.assess())

    def test_ts02_12_illegal_transition_error_message(self, tmp_path: Path) -> None:
        """TS-02-12: SessionError names current state and required state.

        Requirement: 02-REQ-4.3
        """
        session = _create_session(tmp_path, SessionState.INIT)
        with pytest.raises(SessionError) as exc_info:
            _run_sync(session.generate())

        error_msg = str(exc_info.value)
        assert "init" in error_msg
        assert "prd_accepted" in error_msg

    def test_ts02_13_accept_prd_from_assessing_and_refining(
        self, tmp_path: Path
    ) -> None:
        """TS-02-13: accept_prd() works from both assessing and refining states.

        Requirement: 02-REQ-4.4
        """
        session_a = _create_session(tmp_path, SessionState.ASSESSING)
        session_a.accept_prd()
        assert session_a.state == SessionState.PRD_ACCEPTED

        session_r = _create_session(tmp_path, SessionState.REFINING)
        session_r.accept_prd()
        assert session_r.state == SessionState.PRD_ACCEPTED


class TestSessionPersistence:
    """Tests for session persistence — TS-02-14 through TS-02-16."""

    def test_ts02_14_state_persisted_on_transition(self, tmp_path: Path) -> None:
        """TS-02-14: _session.json is updated on every state transition.

        Requirement: 02-REQ-5.1
        """
        session = _create_session(tmp_path, SessionState.ASSESSING)
        session.accept_prd()

        data = json.loads((session.spec_dir / "_session.json").read_text())
        assert data["state"] == "prd_accepted"

    def test_ts02_15_session_resume(self, tmp_path: Path) -> None:
        """TS-02-15: SpecSession.resume restores session state from _session.json.

        Requirement: 02-REQ-5.2
        """
        session = _create_session(tmp_path, SessionState.ASSESSING)
        session.accept_prd()

        resumed = SpecSession.resume(session.spec_dir)
        assert resumed.state == SessionState.PRD_ACCEPTED
        assert resumed.spec_dir == session.spec_dir

    def test_ts02_16_session_json_fields(self, tmp_path: Path) -> None:
        """TS-02-16: _session.json contains all required fields.

        Requirement: 02-REQ-5.3
        """
        camp_dir = tmp_path / "json_fields"
        camp = Campaign.create(camp_dir, "Test", "Desc")
        session = camp.new_spec("test_spec", "PRD content")

        data = json.loads((session.spec_dir / "_session.json").read_text())
        assert "state" in data
        assert "prd_path" in data
        assert "assessment_history" in data
        assert "qa_exchanges" in data
        assert "generated_artifacts" in data
        assert "mode" in data


class TestSessionValidateRender:
    """Tests for validate() and render() — TS-02-17 through TS-02-19."""

    def test_ts02_17_validate_with_artifacts(self, tmp_path: Path) -> None:
        """TS-02-17: validate() loads spec via afspec and returns ValidationResult.

        Requirement: 02-REQ-6.1
        """
        session = _create_session_with_all_artifacts(tmp_path)

        # Mock afspec at the boundary
        mock_spec = MagicMock()
        mock_validation = ValidationResult(
            valid=True,
            schema_errors=[],
            integrity_errors=[],
            repair_suggestions=[],
        )

        with (
            patch("speclib.session.afspec") as mock_afspec,
        ):
            mock_afspec.load_spec.return_value = mock_spec
            mock_afspec.validate.return_value = mock_validation

            result = session.validate()

        assert isinstance(result, ValidationResult)
        assert isinstance(result.valid, bool)
        assert isinstance(result.schema_errors, list)
        assert isinstance(result.integrity_errors, list)

    def test_ts02_18_render_combined(self, tmp_path: Path) -> None:
        """TS-02-18: render(combined=True) returns a single markdown string.

        Requirement: 02-REQ-6.2
        """
        session = _create_session_with_all_artifacts(tmp_path)

        mock_spec = MagicMock()

        with patch("speclib.session.afspec") as mock_afspec:
            mock_afspec.load_spec.return_value = mock_spec
            mock_afspec.render_combined.return_value = "# Combined"

            result = session.render(combined=True)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_ts02_19_render_individual(self, tmp_path: Path) -> None:
        """TS-02-19: render(combined=False) returns artifact name dict.

        Requirement: 02-REQ-6.3
        """
        session = _create_session_with_all_artifacts(tmp_path)

        mock_spec = MagicMock()

        with patch("speclib.session.afspec") as mock_afspec:
            mock_afspec.load_spec.return_value = mock_spec
            mock_afspec.render_individual.return_value = {"prd": "# PRD content"}

            result = session.render(combined=False)

        assert isinstance(result, dict)
        assert all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in result.items()
        )


# ---------------------------------------------------------------------------
# Edge case tests: TS-02-E7 through TS-02-E11
# ---------------------------------------------------------------------------


class TestSessionEdgeCases:
    """Edge case tests for session operations — TS-02-E7 through TS-02-E11."""

    def test_ts02_e7_generate_from_wrong_state(self, tmp_path: Path) -> None:
        """TS-02-E7: SessionError when generate() called from non-prd_accepted state.

        Requirement: 02-REQ-4.E1
        """
        session_init = _create_session(tmp_path, SessionState.INIT)
        with pytest.raises(SessionError):
            _run_sync(session_init.generate())

        session_assessing = _create_session(tmp_path, SessionState.ASSESSING)
        with pytest.raises(SessionError):
            _run_sync(session_assessing.generate())

    def test_ts02_e8_assess_from_generated(self, tmp_path: Path) -> None:
        """TS-02-E8: SessionError when assess() called from generated terminal state.

        Requirement: 02-REQ-4.E2
        """
        session = _create_session(tmp_path, SessionState.GENERATED)
        with pytest.raises(SessionError):
            _run_sync(session.assess())

    def test_ts02_e9_resume_no_session_json(self, tmp_path: Path) -> None:
        """TS-02-E9: SessionError when resume() called without _session.json.

        Requirement: 02-REQ-5.E1
        """
        empty_dir = tmp_path / "no_session"
        empty_dir.mkdir()

        with pytest.raises(SessionError):
            SpecSession.resume(empty_dir)

    def test_ts02_e10_resume_invalid_json(self, tmp_path: Path) -> None:
        """TS-02-E10: SessionError when _session.json contains invalid JSON.

        Requirement: 02-REQ-5.E2
        """
        bad_dir = tmp_path / "bad_json"
        bad_dir.mkdir()
        (bad_dir / "_session.json").write_text("{invalid json!!!")

        with pytest.raises(SessionError):
            SpecSession.resume(bad_dir)

    def test_ts02_e11_validate_render_missing_artifacts(
        self, tmp_path: Path
    ) -> None:
        """TS-02-E11: SessionError when validate/render called with missing artifacts.

        Requirement: 02-REQ-6.E1
        """
        # Session with only prd.md — missing requirements.md, design.md, test_spec.md
        camp_dir = tmp_path / "missing_artifacts"
        camp = Campaign.create(camp_dir, "Test", "Desc")
        session = camp.new_spec("incomplete", "PRD content")

        with pytest.raises(SessionError) as exc_info:
            session.validate()
        error_msg = str(exc_info.value)
        assert "requirements.md" in error_msg
        assert "design.md" in error_msg
        assert "test_spec.md" in error_msg

        with pytest.raises(SessionError) as exc_info:
            session.render()
        error_msg = str(exc_info.value)
        assert "requirements.md" in error_msg


# ---------------------------------------------------------------------------
# Property tests: TS-02-P1, TS-02-P2, TS-02-P5, TS-02-P6
# ---------------------------------------------------------------------------

# Legal transitions: (source_state, method_name) -> target_state
_LEGAL_TRANSITIONS: dict[tuple[str, str], str] = {
    ("init", "assess"): "assessing",
    ("assessing", "refine"): "refining",
    ("assessing", "accept_prd"): "prd_accepted",
    ("refining", "assess"): "assessing",
    ("refining", "accept_prd"): "prd_accepted",
    ("prd_accepted", "generate"): "generating",
    ("generating", "generate"): "generated",  # resume after partial failure
}

# All four required artifacts for validate/render
_REQUIRED_ARTIFACTS = frozenset(
    {"prd.md", "requirements.md", "design.md", "test_spec.md"}
)


class TestSessionProperties:
    """Property tests for session state machine.

    Covers TS-02-P1, TS-02-P2, TS-02-P5, TS-02-P6.
    """

    def test_ts02_p1_property_state_machine_total(
        self, tmp_path: Path
    ) -> None:
        """TS-02-P1: State machine transitions are total and exclusive.

        Property 1: For any session state and method call, the result is
        either a successful transition to a defined target state or a
        SessionError. No other outcome.

        Validates: 02-REQ-4.2, 02-REQ-4.3

        Note: assess, refine, and generate are now async (spec 03).
        For legal transitions of async methods, we verify the state
        check passes (no SessionError) without running the full agent
        implementation.  For illegal transitions, we run the coroutine
        and verify SessionError.
        """
        methods = ["assess", "refine", "accept_prd", "generate"]

        for state in SessionState:
            for method_name in methods:
                session = _create_session(tmp_path, state)
                key = (state.value, method_name)
                is_async = method_name in _ASYNC_METHODS

                if key in _LEGAL_TRANSITIONS:
                    if is_async:
                        # Async methods: verify state check passes
                        # (no SessionError).  Full behavior tested
                        # in spec 03 tests.
                        try:
                            if method_name == "refine":
                                _run_sync(
                                    getattr(session, method_name)({})
                                )
                            else:
                                _run_sync(
                                    getattr(session, method_name)()
                                )
                        except SessionError:
                            pytest.fail(
                                f"Legal transition {key} raised "
                                f"SessionError"
                            )
                        except Exception:
                            pass  # Agent/config error is fine
                    else:
                        # Sync method (accept_prd)
                        getattr(session, method_name)()
                        expected = _LEGAL_TRANSITIONS[key]
                        assert session.state == SessionState(expected), (
                            f"Expected state {expected} after "
                            f"{method_name}() from {state.value}, "
                            f"got {session.state.value}"
                        )
                else:
                    # Illegal transition — must raise SessionError
                    if is_async:
                        with pytest.raises(SessionError):
                            if method_name == "refine":
                                _run_sync(
                                    getattr(session, method_name)({})
                                )
                            else:
                                _run_sync(
                                    getattr(session, method_name)()
                                )
                    else:
                        with pytest.raises(SessionError):
                            if method_name == "refine":
                                getattr(session, method_name)({})
                            else:
                                getattr(session, method_name)()

    def test_ts02_p2_property_persistence_idempotent(
        self, tmp_path: Path
    ) -> None:
        """TS-02-P2: Session persistence is idempotent on resume.

        Property 2: For any session that has undergone valid transitions,
        persisting and resuming produces an equivalent session.

        Validates: 02-REQ-5.1, 02-REQ-5.2
        """
        # Test various reachable states via non-stub transitions
        # Only accept_prd is non-stub, so reachable persisted states are:
        # init (from creation), assessing (set directly), prd_accepted (via accept_prd)
        reachable_states = [
            SessionState.INIT,
            SessionState.ASSESSING,
            SessionState.REFINING,
            SessionState.PRD_ACCEPTED,
            SessionState.GENERATING,
            SessionState.GENERATED,
        ]

        for state in reachable_states:
            session = _create_session(tmp_path, state)
            original_state = session.state
            original_dir = session.spec_dir

            resumed = SpecSession.resume(session.spec_dir)

            assert resumed.state == original_state, (
                f"Resumed state {resumed.state} != original {original_state}"
            )
            assert resumed.spec_dir == original_dir

    @given(
        subset_bits=st.integers(min_value=0, max_value=14),
    )
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_ts02_p5_property_artifacts_required(
        self, subset_bits: int, tmp_path: Path
    ) -> None:
        """TS-02-P5: validate() and render() require all four artifacts.

        Property 5: For any strict subset of the four required artifacts,
        validate() and render() raise SessionError.

        Validates: 02-REQ-6.1, 02-REQ-6.E1
        """
        all_artifacts = sorted(_REQUIRED_ARTIFACTS)
        # Generate a subset from bits (0-14 maps to all strict subsets
        # since 15 = full set)
        subset = {
            a for i, a in enumerate(all_artifacts) if subset_bits & (1 << i)
        }

        # Skip the full set — that's not a strict subset
        if subset == _REQUIRED_ARTIFACTS:
            return

        # Create session with only the selected artifacts
        camp_dir = tmp_path / f"art_{subset_bits}"
        if not (camp_dir / "campaign.yaml").exists():
            Campaign.create(camp_dir, "Test", "Desc")
        camp = Campaign.open(camp_dir)
        session = camp.new_spec(f"s{subset_bits}", "PRD content")

        # prd.md is always created by new_spec, add the rest from subset
        for artifact in subset:
            if artifact != "prd.md":
                (session.spec_dir / artifact).write_text(f"# {artifact}")

        missing = _REQUIRED_ARTIFACTS - subset - {"prd.md"}

        if missing or "prd.md" not in subset:
            # Not all artifacts present — should raise SessionError
            actual_missing = _REQUIRED_ARTIFACTS - (subset | {"prd.md"})
            if actual_missing:
                with pytest.raises(SessionError) as exc_info:
                    session.validate()
                error_msg = str(exc_info.value)
                for name in actual_missing:
                    assert name in error_msg

                with pytest.raises(SessionError):
                    session.render()

    def test_ts02_p6_property_accept_prd_states(
        self, tmp_path: Path
    ) -> None:
        """TS-02-P6: accept_prd() is only callable from assessing or refining.

        Property 6: accept_prd() succeeds only from assessing or refining;
        all other states raise SessionError.

        Validates: 02-REQ-4.4
        """
        for state in SessionState:
            session = _create_session(tmp_path, state)
            if state in {SessionState.ASSESSING, SessionState.REFINING}:
                session.accept_prd()
                assert session.state == SessionState.PRD_ACCEPTED
            else:
                with pytest.raises(SessionError):
                    session.accept_prd()


# ---------------------------------------------------------------------------
# Integration smoke tests: TS-02-SMOKE-3 through TS-02-SMOKE-5
# ---------------------------------------------------------------------------


class TestSessionSmokeTests:
    """Integration smoke tests for session operations."""

    def test_ts02_smoke_3_session_lifecycle(self, tmp_path: Path) -> None:
        """TS-02-SMOKE-3: Full lifecycle through accept_prd.

        Execution Path: Path 4 from design.md.
        Must NOT satisfy with: Mocking SpecSession or its persistence layer.
        """
        camp = Campaign.create(tmp_path / "smoke3", "Test", "Desc")
        session = camp.new_spec("lifecycle", "PRD content")

        # Simulate assess having run (set state directly for test)
        session_file = session.spec_dir / "_session.json"
        data = json.loads(session_file.read_text())
        data["state"] = SessionState.ASSESSING.value
        session_file.write_text(json.dumps(data))
        session = SpecSession.resume(session.spec_dir)

        session.accept_prd()
        assert session.state == SessionState.PRD_ACCEPTED

        resumed = SpecSession.resume(session.spec_dir)
        assert resumed.state == SessionState.PRD_ACCEPTED

    def test_ts02_smoke_4_session_resume(self, tmp_path: Path) -> None:
        """TS-02-SMOKE-4: Create session, transition states, resume.

        Execution Path: Path 5 from design.md.
        Must NOT satisfy with: Mocking SpecSession persistence.
        """
        camp = Campaign.create(tmp_path / "smoke4", "Test", "Desc")
        session = camp.new_spec("resume_test", "PRD")

        # Set to assessing state directly, then accept_prd
        session_file = session.spec_dir / "_session.json"
        data = json.loads(session_file.read_text())
        data["state"] = SessionState.ASSESSING.value
        session_file.write_text(json.dumps(data))
        session = SpecSession.resume(session.spec_dir)

        session.accept_prd()
        assert session.state == SessionState.PRD_ACCEPTED
        original_dir = session.spec_dir

        resumed = SpecSession.resume(original_dir)
        assert resumed.state == SessionState.PRD_ACCEPTED
        assert resumed.spec_dir == original_dir

    def test_ts02_smoke_5_validate_and_render(self, tmp_path: Path) -> None:
        """TS-02-SMOKE-5: Validation and rendering end-to-end.

        Execution Path: Path 6 from design.md.
        Must NOT satisfy with: Mocking validate/render methods themselves
        (afspec internals may be mocked).
        """
        session = _create_session_with_all_artifacts(tmp_path)

        # Mock afspec at the boundary — real session logic, mocked afspec
        mock_spec = MagicMock()
        mock_validation = ValidationResult(
            valid=True,
            schema_errors=[],
            integrity_errors=[],
            repair_suggestions=[],
        )

        with patch("speclib.session.afspec") as mock_afspec:
            mock_afspec.load_spec.return_value = mock_spec
            mock_afspec.validate.return_value = mock_validation
            mock_afspec.render_combined.return_value = "# Combined Output"
            mock_afspec.render_individual.return_value = {
                "prd": "# PRD",
                "requirements": "# Requirements",
            }

            result = session.validate()
            assert isinstance(result, ValidationResult)

            combined = session.render(combined=True)
            assert isinstance(combined, str)

            individual = session.render(combined=False)
            assert isinstance(individual, dict)


# ---------------------------------------------------------------------------
# pending_questions tests: TS-06 spec
# ---------------------------------------------------------------------------


class TestPendingQuestions:
    """Tests for SpecSession.pending_questions()."""

    def test_pending_questions_returns_dicts(self, tmp_path: Path) -> None:
        """TS-06-P2 (partial): pending_questions returns list of dicts with
        correct keys from latest assessment.

        Requirement: 06-REQ-2.1
        """
        session = _create_session(tmp_path, SessionState.ASSESSING)
        session_file = session.spec_dir / "_session.json"
        data = json.loads(session_file.read_text())
        data["assessment_history"] = [
            {
                "quality": "needs_refinement",
                "summary": "Needs work",
                "gaps": [],
                "questions": [
                    {
                        "id": "q1",
                        "text": "What scope?",
                        "context": "Clarify scope",
                        "options": ["A", "B"],
                        "required": True,
                    },
                    {
                        "id": "q2",
                        "text": "Which DB?",
                        "context": "Pick database",
                        "options": [],
                        "required": False,
                    },
                ],
            }
        ]
        session_file.write_text(json.dumps(data))
        session = SpecSession.resume(session.spec_dir)

        result = session.pending_questions()

        assert len(result) == 2
        assert all(isinstance(q, dict) for q in result)
        for q in result:
            assert set(q.keys()) == {"id", "text", "context", "options", "required"}
        assert result[0]["id"] == "q1"
        assert result[0]["text"] == "What scope?"
        assert result[0]["options"] == ["A", "B"]
        assert result[0]["required"] is True
        assert result[1]["id"] == "q2"

    def test_pending_questions_empty_history(self, tmp_path: Path) -> None:
        """TS-06-P2 (partial): pending_questions returns empty list when
        no assessment exists.

        Requirement: 06-REQ-2.2
        """
        session = _create_session(tmp_path, SessionState.INIT)
        result = session.pending_questions()
        assert result == []

    def test_pending_questions_defaults(self, tmp_path: Path) -> None:
        """TS-06-E3: pending_questions uses defaults for missing optional fields.

        Requirement: 06-REQ-2.E1
        """
        session = _create_session(tmp_path, SessionState.ASSESSING)
        session_file = session.spec_dir / "_session.json"
        data = json.loads(session_file.read_text())
        data["assessment_history"] = [
            {
                "quality": "needs_refinement",
                "summary": "Needs work",
                "gaps": [],
                "questions": [
                    {
                        "id": "q1",
                        "text": "Question?",
                        "context": "Context",
                    }
                ],
            }
        ]
        session_file.write_text(json.dumps(data))
        session = SpecSession.resume(session.spec_dir)

        result = session.pending_questions()
        assert result[0]["options"] == []
        assert result[0]["required"] is False

    def test_pending_questions_read_only(self, tmp_path: Path) -> None:
        """TS-06-P3: pending_questions does not modify session state.

        Requirement: 06-REQ-2.3
        """
        session = _create_session(tmp_path, SessionState.ASSESSING)
        session_file = session.spec_dir / "_session.json"
        data = json.loads(session_file.read_text())
        data["assessment_history"] = [
            {
                "quality": "needs_refinement",
                "summary": "S",
                "gaps": [],
                "questions": [
                    {
                        "id": "q1", "text": "Q?", "context": "C",
                        "options": [], "required": True,
                    }
                ],
            }
        ]
        session_file.write_text(json.dumps(data))
        session = SpecSession.resume(session.spec_dir)

        state_before = session.state
        history_before = json.loads(session_file.read_text())

        session.pending_questions()

        assert session.state == state_before
        history_after = json.loads(session_file.read_text())
        assert history_before == history_after
