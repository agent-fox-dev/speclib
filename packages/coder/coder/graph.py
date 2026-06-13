"""LangGraph state schema and conditional edge routing.

Defines the ``CoderState`` TypedDict used as the shared state across all
graph nodes, the factory function to create initial state, the routing
functions that encode retry / loop-back logic for the TDD workflow, and
the ``build_graph`` constructor that assembles the compiled LangGraph.

Implements Requirements:
    14-REQ-1.1 (state schema), 14-REQ-1.2 (initial defaults),
    14-REQ-3.1 (coverage routing), 14-REQ-3.2 (test failure routing),
    14-REQ-3.3 (test pass routing), 14-REQ-3.4 (drift routing),
    14-REQ-3.5 (no-drift routing), 14-REQ-3.6 (halt routing),
    14-REQ-9.1 (graph construction, partial).
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from coder.models import ParsedSpec

logger = logging.getLogger(__name__)


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


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph(
    provider: Any,
    tools: list[Any],
    config: dict[str, Any],
) -> Any:
    """Construct the LangGraph state machine with all nodes and edges.

    Creates the full TDD workflow graph with node wrappers that bind the
    LLM provider and verification runner to each node function, then
    compiles it into an executable graph.

    Parameters
    ----------
    provider:
        An :class:`LLMProvider` instance (or mock) used by LLM-calling
        nodes. Must have an ``invoke(messages)`` method.
    tools:
        List of LangChain tool definitions available to the LLM.
    config:
        Configuration dictionary. Recognised keys:

        - ``verification_runner``: a :class:`VerificationRunner` instance
          (or mock) used by the ``run_tests`` node. If absent, the
          ``run_tests`` node will be a no-op that marks tests as passed.

    Returns
    -------
    A compiled LangGraph ``CompiledGraph`` ready for ``.invoke(state)``.
    """
    from coder.nodes import (
        analyze_codebase,
        complete_node,
        halted_node,
        implement,
        next_task_group,
        run_tests,
        understand_spec,
        verify_intent,
        verify_test_coverage,
        write_tests,
    )

    runner = config.get("verification_runner")

    # -- Build the state graph ------------------------------------------------
    graph = StateGraph(CoderState)

    # Add nodes — each wraps the corresponding function to bind its deps.
    graph.add_node(
        "understand_spec",
        lambda state: understand_spec(state, provider),
    )
    graph.add_node(
        "analyze_codebase",
        lambda state: analyze_codebase(state, provider),
    )
    graph.add_node(
        "write_tests",
        lambda state: write_tests(state, provider),
    )
    graph.add_node(
        "verify_test_coverage",
        lambda state: verify_test_coverage(state, provider),
    )
    graph.add_node(
        "implement",
        lambda state: implement(state, provider),
    )
    def _run_tests_node(state: CoderState) -> CoderState:
        """Run tests node: uses the runner if available, otherwise passes."""
        state_dict: dict[str, Any] = dict(state)
        if runner:
            return run_tests(state_dict, runner)  # type: ignore[return-value]
        # No runner configured: treat tests as passing so graph can proceed
        from coder.nodes import _with_defaults
        new_state = _with_defaults(state_dict)
        new_state["test_results"] = "PASS"
        return new_state  # type: ignore[return-value]

    graph.add_node("run_tests", _run_tests_node)
    graph.add_node(
        "verify_intent",
        lambda state: verify_intent(state, provider),
    )
    graph.add_node(
        "next_task_group",
        lambda state: next_task_group(state),
    )
    graph.add_node(
        "complete",
        lambda state: complete_node(state),
    )
    graph.add_node(
        "halted",
        lambda state: halted_node(state),
    )

    # -- Wire edges -----------------------------------------------------------

    # Linear: understand_spec → analyze_codebase → write_tests
    graph.set_entry_point("understand_spec")
    graph.add_edge("understand_spec", "analyze_codebase")
    graph.add_edge("analyze_codebase", "write_tests")

    # write_tests → verify_test_coverage
    graph.add_edge("write_tests", "verify_test_coverage")

    # verify_test_coverage → conditional (coverage_ok?)
    graph.add_conditional_edges(
        "verify_test_coverage",
        route_after_coverage,
        {"write_tests": "write_tests", "implement": "implement"},
    )

    # implement → run_tests
    graph.add_edge("implement", "run_tests")

    # run_tests → conditional (pass / fail+retry / fail+halt)
    graph.add_conditional_edges(
        "run_tests",
        route_after_tests,
        {
            "verify_intent": "verify_intent",
            "implement": "implement",
            "halted": "halted",
        },
    )

    # verify_intent → conditional (no drift / drift+retry / drift+halt)
    graph.add_conditional_edges(
        "verify_intent",
        route_after_intent,
        {
            "next_task_group": "next_task_group",
            "complete": "complete",
            "verify_test_coverage": "verify_test_coverage",
            "halted": "halted",
        },
    )

    # next_task_group → write_tests (loop back for next group)
    graph.add_edge("next_task_group", "write_tests")

    # Terminal nodes
    graph.add_edge("complete", END)
    graph.add_edge("halted", END)

    logger.debug("LangGraph TDD workflow compiled with %d nodes", 10)

    return graph.compile()
