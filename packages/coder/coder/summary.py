"""Run summary document generation.

Generates a ``_run_summary.md`` markdown file after execution completes,
summarizing spec name, model, groups, tokens, time, and status.

Implements Requirements:
    15-REQ-6.1 (file location and logging),
    15-REQ-6.2 (required fields),
    15-REQ-6.3 (console output),
    15-REQ-6.E1 (write failure fallback to console).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _format_run_summary(
    state: dict[str, Any],
    tracker: Any,
) -> str:
    """Format the run summary markdown content.

    Parameters
    ----------
    state:
        The final execution state dictionary.
    tracker:
        A token tracker with ``input_tokens``, ``output_tokens``,
        ``total_tokens``, and ``call_count`` attributes.

    Returns
    -------
    The complete run summary markdown string.
    """
    spec_name = state.get("spec_name", "unknown")
    model_name = state.get("model_name", "unknown")
    current_task_group = state.get("current_task_group", 0)
    total_groups = state.get("total_groups", 0)
    halted = state.get("halted", False)
    success = state.get("success", False)
    halt_reason = state.get("halt_reason", "")
    elapsed_seconds = state.get("elapsed_seconds", 0.0)

    # Determine final status
    if halted:
        status = "halted"
    elif success:
        status = "success"
    else:
        status = "failed"

    input_tokens = getattr(tracker, "input_tokens", 0)
    output_tokens = getattr(tracker, "output_tokens", 0)
    total_tokens = getattr(tracker, "total_tokens", 0)
    call_count = getattr(tracker, "call_count", 0)

    # Format elapsed time
    elapsed = float(elapsed_seconds) if elapsed_seconds else 0.0
    minutes = int(elapsed // 60)
    seconds = elapsed % 60

    summary = f"""# Run Summary

## Spec
- **Name:** {spec_name}
- **Model:** {model_name}

## Task Groups
- **Completed:** {current_task_group} of {total_groups}

## Token Usage
- **Input tokens:** {input_tokens:,}
- **Output tokens:** {output_tokens:,}
- **Total tokens:** {total_tokens:,}
- **LLM calls:** {call_count}

## Timing
- **Elapsed:** {minutes}m {seconds:.1f}s ({elapsed:.1f}s total)

## Status
- **Final status:** {status}
"""

    if halt_reason:
        summary += f"- **Halt reason:** {halt_reason}\n"

    return summary


def write_run_summary(
    state: dict[str, Any],
    worktree: Path,
    tracker: Any,
) -> Path:
    """Generate ``_run_summary.md`` and return its path.

    Writes the run summary file to the worktree directory. If writing
    fails (e.g. read-only directory), logs a warning and prints the
    summary to the console instead (15-REQ-6.E1).

    Parameters
    ----------
    state:
        The final execution state dictionary.
    worktree:
        Path to the worktree directory.
    tracker:
        A token tracker with token usage attributes.

    Returns
    -------
    The path to the generated run summary file (even if writing
    failed — in that case the path was not actually created).
    """
    content = _format_run_summary(state, tracker)
    output_path = worktree / "_run_summary.md"

    try:
        output_path.write_text(content, encoding="utf-8")
        logger.info("Run summary written to %s", output_path)
    except OSError as exc:
        logger.warning(
            "Failed to write run summary to %s: %s. "
            "Printing to console instead.",
            output_path,
            exc,
        )
        # Fallback: print to console (stdout)
        print(content)

    return output_path
