"""Entry points for spec and campaign execution.

Provides ``run_spec()`` and ``run_campaign()`` functions that build and
execute the LangGraph workflow for one or more specs.

Implements Requirements:
    14-REQ-9.1 (run_spec), 14-REQ-9.2 (RunResult),
    14-REQ-9.3 (run_campaign), 14-REQ-9.E1 (exception handling).

Note: Full implementation provided in task group 6.
      Stub implementations provided here for import compatibility.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coder.models import ExecutionPlan, ParsedSpec

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

    # Stub: mark as successful for now
    elapsed = time.monotonic() - start_time

    return RunResult(
        success=True,
        spec_name=parsed_spec.meta.spec_name,
        task_groups_completed=total_groups,
        total_task_groups=total_groups,
        total_tokens=0,
        elapsed_seconds=max(elapsed, 0.001),
        halt_reason=None,
    )


def run_campaign(
    plan: ExecutionPlan,
    provider: Any,
    repo_path: Path,
    config: dict[str, Any],
) -> list[RunResult]:
    """Iterate over specs in plan order, running each and collecting results.

    Catches per-spec exceptions so that a failure in one spec does not
    prevent execution of subsequent specs (14-REQ-9.E1).

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
        try:
            result = run_spec(spec, provider, repo_path, config)
            results.append(result)
        except Exception as exc:
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
                    total_task_groups=len(spec.tasks.task_groups) or 1,
                    total_tokens=0,
                    elapsed_seconds=0.0,
                    halt_reason=f"Error: {exc}",
                )
            )
    return results
