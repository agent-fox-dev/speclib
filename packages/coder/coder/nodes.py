"""LangGraph workflow node implementations.

Each node function takes the current ``CoderState`` dictionary and an
LLM (or runner) instance, performs its step, and returns the updated
state. Nodes check the ``halted`` flag on entry and pass through
unchanged if set.

Implements Requirements:
    14-REQ-2.1 through 14-REQ-2.7 (node behavior),
    14-REQ-2.E1 (empty response retry),
    14-REQ-3.E1 (halted passthrough),
    14-REQ-7.3 (task group advance).
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

_STATE_DEFAULTS: dict[str, Any] = {
    "attempt_count": 0,
    "max_attempts": 5,
    "halted": False,
    "halt_reason": "",
    "spec_context": "",
    "codebase_analysis": "",
    "test_results": "",
    "coverage_ok": False,
    "drift_detected": False,
    "current_task_group": 1,
    "current_phase": "understand_spec",
}
"""Sensible defaults for all standard CoderState fields (14-REQ-1.E1)."""


def _get_state_default(
    state: dict[str, Any], key: str, default: Any
) -> Any:
    """Get a value from state with a sensible default (14-REQ-1.E1)."""
    return state.get(key, default)


def _with_defaults(state: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *state* with missing fields filled from defaults.

    Ensures that every node returns a state dictionary containing all
    standard fields, even if the input state was incomplete (14-REQ-1.E1).
    """
    result = dict(state)
    for key, default in _STATE_DEFAULTS.items():
        if key not in result:
            result[key] = default
    return result


def understand_spec(
    state: dict[str, Any], llm: Any
) -> dict[str, Any]:
    """Read the spec pack and produce a summary of intent.

    Writes the summary to ``spec_context`` in the state.
    """
    if _get_state_default(state, "halted", False):
        return state

    new_state = _with_defaults(state)
    messages = [
        SystemMessage(content="You are a spec analyst."),
        HumanMessage(
            content=(
                "Analyze this specification and summarize its intent:\n"
                + _get_state_default(state, "spec_context", "")
            )
        ),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    if not content:
        new_state["attempt_count"] = (
            _get_state_default(new_state, "attempt_count", 0) + 1
        )
    else:
        new_state["spec_context"] = content
        new_state["current_phase"] = "analyze_codebase"
    return new_state


def analyze_codebase(
    state: dict[str, Any], llm: Any
) -> dict[str, Any]:
    """Examine the codebase and produce a structural analysis.

    Writes the analysis to ``codebase_analysis`` in the state.
    """
    if _get_state_default(state, "halted", False):
        return state

    new_state = _with_defaults(state)
    messages = [
        SystemMessage(content="You are a codebase analyst."),
        HumanMessage(
            content=(
                "Analyze the codebase structure:\n"
                + _get_state_default(state, "spec_context", "")
            )
        ),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    if not content:
        new_state["attempt_count"] = (
            _get_state_default(new_state, "attempt_count", 0) + 1
        )
    else:
        new_state["codebase_analysis"] = content
        new_state["current_phase"] = "write_tests"
    return new_state


def write_tests(
    state: dict[str, Any], llm: Any
) -> dict[str, Any]:
    """Instruct the LLM to create failing tests for the current task group.

    The LLM receives the test_spec content as part of the prompt.
    """
    if _get_state_default(state, "halted", False):
        return state

    new_state = _with_defaults(state)
    group = _get_state_default(state, "current_task_group", 1)
    messages = [
        SystemMessage(content="You are a test writer."),
        HumanMessage(
            content=(
                f"Write failing tests for task group {group} "
                f"based on the test specification:\n"
                + _get_state_default(state, "spec_context", "")
            )
        ),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    if not content:
        new_state["attempt_count"] = (
            _get_state_default(new_state, "attempt_count", 0) + 1
        )
    else:
        new_state["current_phase"] = "verify_test_coverage"
    return new_state


def verify_test_coverage(
    state: dict[str, Any], llm: Any
) -> dict[str, Any]:
    """Check whether written tests cover all test cases for the task group.

    Sets the ``coverage_ok`` flag in the state.
    """
    if _get_state_default(state, "halted", False):
        return state

    new_state = _with_defaults(state)
    messages = [
        SystemMessage(content="You are a test coverage reviewer."),
        HumanMessage(
            content=(
                "Check test coverage for the current task group:\n"
                + _get_state_default(state, "spec_context", "")
            )
        ),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    content_str = str(content) if content else ""

    if not content_str:
        new_state["attempt_count"] = (
            _get_state_default(new_state, "attempt_count", 0) + 1
        )
    else:
        # Determine coverage from LLM response: default to covered
        # unless the response explicitly indicates insufficient coverage.
        lower = content_str.lower()
        insufficient = any(
            kw in lower
            for kw in ("insufficient", "missing", "not covered", "gaps")
        )
        new_state["coverage_ok"] = not insufficient
        new_state["current_phase"] = "implement"
    return new_state


def implement(
    state: dict[str, Any], llm: Any
) -> dict[str, Any]:
    """Instruct the LLM to write implementation code.

    Uses the coder persona to produce code that makes tests pass.
    """
    if _get_state_default(state, "halted", False):
        return state

    new_state = _with_defaults(state)
    messages = [
        SystemMessage(content="You are an expert coder."),
        HumanMessage(
            content=(
                "Implement code to make the tests pass:\n"
                + _get_state_default(state, "spec_context", "")
                + "\n\nCodebase analysis:\n"
                + _get_state_default(state, "codebase_analysis", "")
                + "\n\nTest results:\n"
                + _get_state_default(state, "test_results", "")
            )
        ),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    if not content:
        new_state["attempt_count"] = (
            _get_state_default(new_state, "attempt_count", 0) + 1
        )
    else:
        new_state["current_phase"] = "run_tests"
    return new_state


def run_tests(
    state: dict[str, Any], runner: Any
) -> dict[str, Any]:
    """Execute the verification runner and write results to the state.

    Parameters
    ----------
    state:
        Current graph state.
    runner:
        A :class:`VerificationRunner` (or mock) with a ``.run()`` method.
    """
    if _get_state_default(state, "halted", False):
        return state

    new_state = _with_defaults(state)
    result = runner.run()
    new_state["test_results"] = "PASS" if result.passed else "FAIL"
    new_state["current_phase"] = "verify_intent" if result.passed else "implement"
    return new_state


def verify_intent(
    state: dict[str, Any], llm: Any
) -> dict[str, Any]:
    """Use the reviewer persona to check implementation against spec intent.

    Sets the ``drift_detected`` flag in the state.
    """
    if _get_state_default(state, "halted", False):
        return state

    new_state = _with_defaults(state)
    messages = [
        SystemMessage(content="You are a code reviewer."),
        HumanMessage(
            content=(
                "Review the implementation for spec drift:\n"
                + _get_state_default(state, "spec_context", "")
                + "\n\nTest results:\n"
                + _get_state_default(state, "test_results", "")
            )
        ),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    content_str = str(content) if content else ""

    if not content_str:
        new_state["attempt_count"] = (
            _get_state_default(new_state, "attempt_count", 0) + 1
        )
    else:
        # Determine drift from LLM response: default to no drift
        # unless the response explicitly indicates drift (and not
        # a "no drift" negation).
        lower = content_str.lower()
        new_state["drift_detected"] = (
            "drift" in lower and "no drift" not in lower
        )
    return new_state


def next_task_group(state: dict[str, Any]) -> dict[str, Any]:
    """Advance to the next task group and reset attempt count.

    Per 14-REQ-7.3, increments ``current_task_group`` and resets
    ``attempt_count`` to 0.
    """
    new_state = _with_defaults(state)
    new_state["current_task_group"] = (
        _get_state_default(state, "current_task_group", 1) + 1
    )
    new_state["attempt_count"] = 0
    return new_state


def complete_node(state: dict[str, Any]) -> dict[str, Any]:
    """Terminal node marking the workflow as successfully completed.

    Sets ``current_phase`` to ``"complete"`` per 14-REQ-7.4.
    """
    new_state = _with_defaults(state)
    new_state["current_phase"] = "complete"
    return new_state


def halted_node(state: dict[str, Any]) -> dict[str, Any]:
    """Terminal node marking the workflow as halted due to exceeded attempts.

    Ensures ``halted`` is True and preserves the halt reason.
    """
    new_state = _with_defaults(state)
    new_state["halted"] = True
    if not new_state.get("halt_reason"):
        new_state["halt_reason"] = (
            f"Max attempts ({new_state.get('max_attempts', 5)}) exceeded"
        )
    return new_state
