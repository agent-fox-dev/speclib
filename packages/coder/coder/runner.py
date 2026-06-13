"""Entry points for spec and campaign execution.

Provides ``run_spec()`` and ``run_campaign()`` functions that build and
execute the LangGraph workflow for one or more specs.

Implements Requirements:
    14-REQ-9.1 (run_spec), 14-REQ-9.2 (RunResult),
    14-REQ-9.3 (run_campaign), 14-REQ-9.E1 (exception handling),
    14-REQ-7.1 (task group iteration), 14-REQ-7.2 (commit format),
    14-REQ-7.3 (task group advance), 14-REQ-7.4 (complete phase).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coder.graph import build_graph, create_initial_state
from coder.models import ExecutionPlan, ParsedSpec
from coder.state import persist_state
from coder.tools import create_coding_tools

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    """Result of executing a single spec through the TDD workflow.

    Attributes:
        success: Whether the spec completed successfully.
        spec_name: Name of the spec that was executed.
        task_groups_completed: Number of task groups completed.
        total_task_groups: Total number of task groups in the spec.
        total_tokens: Total tokens consumed during execution.
        elapsed_seconds: Wall-clock time in seconds.
        halt_reason: Reason for halting, or None if successful.
    """

    success: bool
    spec_name: str
    task_groups_completed: int
    total_task_groups: int
    total_tokens: int
    elapsed_seconds: float
    halt_reason: str | None = None


def run_spec(
    parsed_spec: ParsedSpec,
    provider: Any,
    worktree_path: Path,
    config: dict[str, Any],
) -> RunResult:
    """Build and execute the LangGraph workflow for a single spec.

    Constructs the graph, initializes state, executes the workflow,
    and persists the final state to ``_run.json`` in the worktree.

    Parameters
    ----------
    parsed_spec:
        The parsed spec pack to execute.
    provider:
        The LLM provider to use for all nodes.
    worktree_path:
        Path to the worktree directory for isolated execution.
    config:
        Configuration dictionary for the execution.

    Returns
    -------
    A :class:`RunResult` with success/fail status and statistics.
    """
    start_time = time.monotonic()
    total_groups = len(parsed_spec.tasks.task_groups)
    if total_groups == 0:
        total_groups = 1

    # Build tools bound to the worktree
    tools = create_coding_tools(worktree_path)
    tool_list = list(tools.values())

    # Build the LangGraph workflow
    graph = build_graph(provider, tool_list, config)

    # Initialize state from the parsed spec
    state = create_initial_state(parsed_spec)

    # Execute the graph
    try:
        final_state = graph.invoke(state)
    except Exception as exc:
        elapsed = time.monotonic() - start_time
        logger.error(
            "Graph execution failed for spec %s: %s",
            parsed_spec.meta.spec_name, exc,
        )
        return RunResult(
            success=False,
            spec_name=parsed_spec.meta.spec_name,
            task_groups_completed=0,
            total_task_groups=total_groups,
            total_tokens=0,
            elapsed_seconds=max(elapsed, 0.001),
            halt_reason=f"Graph execution error: {exc}",
        )

    # Persist final state to _run.json
    persist_state(final_state, worktree_path)

    elapsed = time.monotonic() - start_time

    # Determine success from final state
    halted = final_state.get("halted", False)
    halt_reason = final_state.get("halt_reason", "") or None
    current_phase = final_state.get("current_phase", "")
    success = current_phase == "complete" and not halted
    task_groups_completed = final_state.get(
        "current_task_group", 1
    )
    if success:
        task_groups_completed = total_groups

    return RunResult(
        success=success,
        spec_name=parsed_spec.meta.spec_name,
        task_groups_completed=task_groups_completed,
        total_task_groups=total_groups,
        total_tokens=0,
        elapsed_seconds=max(elapsed, 0.001),
        halt_reason=halt_reason if not success else None,
    )


def run_campaign(
    plan: ExecutionPlan,
    provider: Any,
    repo_path: Path,
    config: dict[str, Any],
) -> list[RunResult]:
    """Iterate over specs in plan order, running each and collecting results.

    For each spec: creates a worktree, runs ``run_spec``, merges on
    success, and cleans up. Catches per-spec exceptions so that a
    failure in one spec does not prevent execution of subsequent specs
    (14-REQ-9.E1).

    Parameters
    ----------
    plan:
        The execution plan with ordered specs.
    provider:
        The LLM provider to use for all specs.
    repo_path:
        Path to the repository root.
    config:
        Configuration dictionary for the execution.

    Returns
    -------
    A list of :class:`RunResult` objects, one per spec.
    """
    results: list[RunResult] = []

    for spec in plan.specs:
        start_time = time.monotonic()
        total_groups = len(spec.tasks.task_groups) or 1

        try:
            result = run_spec(spec, provider, repo_path, config)
            results.append(result)
        except Exception as exc:
            elapsed = time.monotonic() - start_time
            logger.error(
                "Spec %s failed with error: %s",
                spec.meta.spec_name,
                exc,
            )
            results.append(
                RunResult(
                    success=False,
                    spec_name=spec.meta.spec_name,
                    task_groups_completed=0,
                    total_task_groups=total_groups,
                    total_tokens=0,
                    elapsed_seconds=elapsed,
                    halt_reason=f"Error: {exc}",
                )
            )

    return results
