"""LangGraph state schema and conditional edge routing.

Defines the ``CoderState`` TypedDict used as the shared state across all
graph nodes, the factory function to create initial state, and the routing
functions that encode retry / loop-back logic for the TDD workflow.

Implements Requirements:
    14-REQ-1.1 (state schema), 14-REQ-1.2 (initial defaults),
    14-REQ-3.1 (coverage routing), 14-REQ-3.2 (test failure routing),
    14-REQ-3.3 (test pass routing), 14-REQ-3.4 (drift routing),
    14-REQ-3.5 (no-drift routing), 14-REQ-3.6 (halt routing).
"""

from __future__ import annotations

from typing import Any, TypedDict

from coder.models import ParsedSpec


class CoderState(TypedDict, total=False):
    """Shared state for the LangGraph TDD workflow.

    All fields use ``total=False`` so that nodes can read missing keys
    via ``.get()`` and fall back to sensible defaults per 14-REQ-1.E1.
    """

    current_phase: str
    current_task_group: int
    attempt_count: int
    max_attempts: int
    test_results: str
    spec_context: str
    codebase_analysis: str
    coverage_ok: bool
    drift_detected: bool
    messages: list[Any]
    halted: bool
    halt_reason: str
    history: list[Any]
    total_groups: int


def create_initial_state(parsed_spec: ParsedSpec) -> dict[str, Any]:
    """Create the initial CoderState for a spec execution.

    Parameters
    ----------
    parsed_spec:
        The parsed spec pack to execute.

    Returns
    -------
    A dictionary conforming to :class:`CoderState` with default values
    per 14-REQ-1.2.
    """
    total_groups = len(parsed_spec.tasks.task_groups)
    return {
        "current_phase": "understand_spec",
        "current_task_group": 1,
        "attempt_count": 0,
        "max_attempts": 5,
        "test_results": "",
        "spec_context": "",
        "codebase_analysis": "",
        "coverage_ok": False,
        "drift_detected": False,
        "messages": [],
        "halted": False,
        "halt_reason": "",
        "history": [],
        "total_groups": total_groups if total_groups > 0 else 1,
    }


# ---------------------------------------------------------------------------
# Conditional edge routing functions
# ---------------------------------------------------------------------------


def route_after_coverage(state: dict[str, Any]) -> str:
    """Route after the ``verify_test_coverage`` node.

    14-REQ-3.1: coverage insufficient -> write_tests
    Otherwise -> implement

    Parameters
    ----------
    state:
        Current graph state.

    Returns
    -------
    Name of the next node.
    """
    if not state.get("coverage_ok", False):
        return "write_tests"
    return "implement"


def route_after_tests(state: dict[str, Any]) -> str:
    """Route after the ``run_tests`` node.

    14-REQ-3.3: tests pass -> verify_intent
    14-REQ-3.6: tests fail + max attempts -> halted
    14-REQ-3.2: tests fail + attempts left -> implement

    Parameters
    ----------
    state:
        Current graph state.

    Returns
    -------
    Name of the next node.
    """
    test_results = state.get("test_results", "")
    attempt_count = state.get("attempt_count", 0)
    max_attempts = state.get("max_attempts", 5)

    if test_results.upper() == "PASS":
        return "verify_intent"

    # Test failure path
    if attempt_count >= max_attempts:
        return "halted"

    return "implement"


def route_after_intent(state: dict[str, Any]) -> str:
    """Route after the ``verify_intent`` node.

    14-REQ-3.5: no drift + last group -> complete
    14-REQ-3.5: no drift + more groups -> next_task_group
    14-REQ-3.6: drift + max attempts -> halted
    14-REQ-3.4: drift + attempts left -> verify_test_coverage

    Parameters
    ----------
    state:
        Current graph state.

    Returns
    -------
    Name of the next node.
    """
    drift_detected = state.get("drift_detected", False)
    attempt_count = state.get("attempt_count", 0)
    max_attempts = state.get("max_attempts", 5)
    current_group = state.get("current_task_group", 1)
    total_groups = state.get("total_groups", 1)

    if not drift_detected:
        if current_group >= total_groups:
            return "complete"
        return "next_task_group"

    # Drift detected
    if attempt_count >= max_attempts:
        return "halted"

    return "verify_test_coverage"
