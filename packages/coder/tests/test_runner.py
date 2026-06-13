"""Tests for run_spec and run_campaign entry points.

Covers: TS-14-24, TS-14-25, TS-14-34 through TS-14-36.
Edge cases: TS-14-E8.
Property tests: TS-14-P1.
Smoke tests: TS-14-SMOKE-1, TS-14-SMOKE-3.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from afspec.models import Requirements, SpecMeta, Tasks, TestSpec
from coder.graph import create_initial_state, route_after_intent
from coder.models import ExecutionPlan, ParsedSpec
from coder.nodes import next_task_group
from coder.runner import RunResult, run_campaign, run_spec
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_parsed_spec(
    spec_id: str = "1",
    spec_name: str = "test_spec",
    n_groups: int = 1,
) -> ParsedSpec:
    """Create a ParsedSpec with the specified number of task groups."""
    meta = SpecMeta(
        spec_id=spec_id,
        spec_name=spec_name,
        status="active",
        dir="/tmp/fake",
    )
    groups = [
        {
            "id": i,
            "kind": "standard",
            "title": f"Group {i}",
            "subtasks": [],
            "verification": {},
        }
        for i in range(1, n_groups + 1)
    ]
    return ParsedSpec(
        meta=meta,
        requirements=Requirements(
            spec_id=spec_id, spec_name=spec_name
        ),
        test_spec=TestSpec(
            spec_id=spec_id, spec_name=spec_name
        ),
        tasks=Tasks(
            spec_id=spec_id,
            spec_name=spec_name,
            task_groups=groups,
        ),
        prd_text="# Test PRD\n",
    )


# ---------------------------------------------------------------------------
# Acceptance-criterion tests
# ---------------------------------------------------------------------------


class TestRunSpec:
    """TS-14-24: run_spec returns RunResult.

    Requirement: 14-REQ-9.1, 14-REQ-9.2
    """

    def test_returns_run_result(self, git_repo: Path) -> None:
        """Verify run_spec produces a complete RunResult."""
        spec = _make_parsed_spec(n_groups=1)
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        config: dict = {}
        wt_path = git_repo / ".coder" / "worktrees" / "test_spec"
        wt_path.mkdir(parents=True)

        result = run_spec(spec, mock_provider, wt_path, config)

        assert isinstance(result, RunResult)
        assert result.success is True
        assert result.total_task_groups > 0
        assert result.elapsed_seconds > 0

    def test_run_result_fields(self, git_repo: Path) -> None:
        """Verify RunResult contains all required fields."""
        spec = _make_parsed_spec(n_groups=2)
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        config: dict = {}
        wt_path = git_repo / ".coder" / "worktrees" / "test_spec"
        wt_path.mkdir(parents=True)

        result = run_spec(spec, mock_provider, wt_path, config)

        assert hasattr(result, "success")
        assert hasattr(result, "task_groups_completed")
        assert hasattr(result, "total_task_groups")
        assert hasattr(result, "total_tokens")
        assert hasattr(result, "elapsed_seconds")
        assert hasattr(result, "halt_reason")


class TestRunCampaign:
    """TS-14-25: run_campaign catches per-spec failures.

    Requirement: 14-REQ-9.3, 14-REQ-9.E1
    """

    def test_catches_spec_failure(self, git_repo: Path) -> None:
        """Verify campaign continues after a spec failure."""
        spec1 = _make_parsed_spec(
            spec_id="1", spec_name="failing_spec"
        )
        spec2 = _make_parsed_spec(
            spec_id="2", spec_name="passing_spec"
        )
        plan = ExecutionPlan(
            specs=[spec1, spec2],
            count=2,
            timestamp="2026-06-13T10:00:00Z",
        )
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        config: dict = {}

        with patch(
            "coder.runner.run_spec",
            side_effect=[
                RuntimeError("boom"),
                RunResult(
                    success=True,
                    spec_name="passing_spec",
                    task_groups_completed=1,
                    total_task_groups=1,
                    total_tokens=0,
                    elapsed_seconds=1.0,
                    halt_reason=None,
                ),
            ],
        ):
            results = run_campaign(
                plan, mock_provider, git_repo, config
            )

        assert len(results) == 2
        assert results[0].success is False


class TestGroupOrder:
    """TS-14-34: Task groups iterated in order.

    Requirement: 14-REQ-7.1
    """

    def test_groups_processed_in_order(self) -> None:
        """Verify task groups are processed in order 1, 2, 3."""
        state = create_initial_state(
            _make_parsed_spec(n_groups=3)
        )
        groups_visited = []
        current_state = state
        for _ in range(3):
            groups_visited.append(
                current_state["current_task_group"]
            )
            current_state = next_task_group(current_state)
        assert groups_visited == [1, 2, 3]


class TestAdvanceGroup:
    """TS-14-35: Task group advances counter and resets attempts.

    Requirement: 14-REQ-7.3
    """

    def test_advances_and_resets(self) -> None:
        """Verify next_task_group advances group and resets attempts."""
        state: dict = {
            "current_task_group": 2,
            "attempt_count": 3,
            "current_phase": "next_task_group",
            "halted": False,
            "total_groups": 3,
        }
        new_state = next_task_group(state)
        assert new_state["current_task_group"] == 3
        assert new_state["attempt_count"] == 0


class TestCompletePhase:
    """TS-14-36: All groups complete sets phase to complete.

    Requirement: 14-REQ-7.4
    """

    def test_last_group_routes_to_complete(self) -> None:
        """Verify last group routes to 'complete' node."""
        state: dict = {
            "current_task_group": 3,
            "total_groups": 3,
            "drift_detected": False,
            "attempt_count": 0,
            "max_attempts": 5,
            "halted": False,
        }
        next_node = route_after_intent(state)
        assert next_node == "complete"


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------


class TestCampaignCatchesException:
    """TS-14-E8: Unhandled exception in run_spec caught by campaign.

    Requirement: 14-REQ-9.E1
    """

    def test_exception_caught_and_recorded(
        self, git_repo: Path
    ) -> None:
        """Verify run_campaign catches exceptions per spec."""
        spec1 = _make_parsed_spec(
            spec_id="1", spec_name="exploding"
        )
        spec2 = _make_parsed_spec(
            spec_id="2", spec_name="normal"
        )
        plan = ExecutionPlan(
            specs=[spec1, spec2],
            count=2,
            timestamp="2026-06-13T10:00:00Z",
        )
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        config: dict = {}

        with patch(
            "coder.runner.run_spec",
            side_effect=[
                RuntimeError("unhandled error"),
                RunResult(
                    success=True,
                    spec_name="normal",
                    task_groups_completed=1,
                    total_task_groups=1,
                    total_tokens=0,
                    elapsed_seconds=1.0,
                    halt_reason=None,
                ),
            ],
        ):
            results = run_campaign(
                plan, mock_provider, git_repo, config
            )

        assert len(results) == 2
        assert results[0].success is False
        assert "error" in (results[0].halt_reason or "").lower()


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestPropertyMonotonicProgress:
    """TS-14-P1: Monotonic task group progress.

    Property 1 from design.md.
    Validates: 14-REQ-7.1, 14-REQ-7.3

    Task groups never decrease during execution.
    """

    @given(n_groups=st.integers(min_value=2, max_value=5))
    @settings(max_examples=20, deadline=10000)
    def test_property_monotonic_groups(
        self, n_groups: int
    ) -> None:
        """Task group numbers strictly increase."""
        state: dict = {
            "current_task_group": 1,
            "attempt_count": 0,
            "current_phase": "next_task_group",
            "halted": False,
            "total_groups": n_groups,
        }
        groups = [state["current_task_group"]]
        for _ in range(n_groups - 1):
            state = next_task_group(state)
            groups.append(state["current_task_group"])
        assert groups == sorted(groups)
        assert len(groups) == len(set(groups))


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


class TestSmokeFullGraphExecution:
    """TS-14-SMOKE-1: Full graph execution with mock LLM.

    Execution Path: Path 1 from design.md.
    """

    @pytest.mark.smoke
    def test_full_graph_execution(self, git_repo: Path) -> None:
        """Verify complete workflow from understand_spec to completion."""
        spec = _make_parsed_spec(n_groups=1)
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        mock_provider.get_chat_model.return_value.invoke.return_value = (
            MagicMock(content="Mock response")
        )
        config: dict = {}
        wt_path = git_repo / ".coder" / "worktrees" / "test_spec"
        wt_path.mkdir(parents=True)

        result = run_spec(spec, mock_provider, wt_path, config)

        assert result.success is True
        run_json_path = wt_path / "_run.json"
        if run_json_path.exists():
            run_json = json.loads(run_json_path.read_text())
            assert run_json["current_phase"] == "complete"


class TestSmokeCampaignMultipleSpecs:
    """TS-14-SMOKE-3: Campaign runs multiple specs.

    Execution Path: Path 3 from design.md.
    """

    @pytest.mark.smoke
    def test_campaign_runs_all_specs(
        self, git_repo: Path
    ) -> None:
        """Verify run_campaign iterates over specs in plan order."""
        spec1 = _make_parsed_spec(
            spec_id="1", spec_name="spec_one", n_groups=1
        )
        spec2 = _make_parsed_spec(
            spec_id="2", spec_name="spec_two", n_groups=1
        )
        plan = ExecutionPlan(
            specs=[spec1, spec2],
            count=2,
            timestamp="2026-06-13T10:00:00Z",
        )
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        config: dict = {}

        results = run_campaign(
            plan, mock_provider, git_repo, config
        )

        assert len(results) == 2
