"""Post-mortem document generation and graceful shutdown.

Generates a ``_postmortem.md`` markdown file from the final graph state
when execution is halted by the circuit breaker. Also provides the
graceful shutdown sequence that persists state and generates the
post-mortem, and a SIGINT handler installer.

Implements Requirements:
    15-REQ-3.1 (file location), 15-REQ-3.2 (sections),
    15-REQ-3.3 (terminal node), 15-REQ-3.4 (I/O error handling),
    15-REQ-3.E1 (fallback to cwd),
    15-REQ-5.1 (complete in-flight call before halt),
    15-REQ-5.2 (persist state during shutdown),
    15-REQ-5.3 (leave worktree intact),
    15-REQ-5.E1 (SIGINT handler).
"""

from __future__ import annotations

import logging
import signal
from pathlib import Path
from typing import Any

from coder.state import persist_state

logger = logging.getLogger(__name__)


def _format_postmortem(
    state: dict[str, Any],
    tracker: Any,
) -> str:
    """Format the post-mortem markdown content from state and tracker.

    Parameters
    ----------
    state:
        The halted graph state dictionary.
    tracker:
        A token tracker (or mock) with ``input_tokens``,
        ``output_tokens``, ``total_tokens``, ``call_count`` attributes
        and a ``to_dict()`` method.

    Returns
    -------
    The complete post-mortem markdown string.
    """
    spec_name = state.get("spec_name", "unknown")
    halt_reason = state.get("halt_reason", "unknown")
    model_name = state.get("model_name", "unknown")
    current_phase = state.get("current_phase", "unknown")
    current_task_group = state.get("current_task_group", 0)
    total_groups = state.get("total_groups", 0)
    attempt_count = state.get("attempt_count", 0)
    max_attempts = state.get("max_attempts", 0)
    test_results = state.get("test_results", "No test output available")
    history = state.get("history", [])

    input_tokens = getattr(tracker, "input_tokens", 0)
    output_tokens = getattr(tracker, "output_tokens", 0)
    total_tokens = getattr(tracker, "total_tokens", 0)
    call_count = getattr(tracker, "call_count", 0)

    # Build the attempt history table
    history_rows = ""
    for i, entry in enumerate(history, 1):
        if isinstance(entry, dict):
            phase = entry.get("phase", "")
            tg = entry.get("task_group", "")
            attempt = entry.get("attempt", "")
            ts = entry.get("timestamp", "")
            result = entry.get("result", "")
        else:
            phase = getattr(entry, "phase", "")
            tg = getattr(entry, "task_group", "")
            attempt = getattr(entry, "attempt", "")
            ts = getattr(entry, "timestamp", "")
            result = getattr(entry, "result", "")
        history_rows += f"| {i} | {phase} | {tg} | {attempt} | {ts} | {result} |\n"

    if not history_rows:
        history_rows = "| - | No history recorded | - | - | - | - |\n"

    # Build recommendations based on halt reason
    recommendations = _build_recommendations(halt_reason)

    return f"""# Post-mortem: {spec_name}

## Summary
Execution halted: {halt_reason}.

## Halt Reason
- **Limit breached:** {halt_reason}
- **Current phase:** {current_phase}
- **Attempt count:** {attempt_count}
- **Max attempts:** {max_attempts}

## Execution Context
- **Spec:** {spec_name}
- **Model:** {model_name}
- **Phase at halt:** {current_phase}
- **Task group:** {current_task_group} of {total_groups}
- **Attempt:** {attempt_count} of {max_attempts}

## Attempt History
| # | Phase | Task Group | Attempt | Time | Result |
|---|-------|------------|---------|------|--------|
{history_rows}
## Last Test Output
```
{test_results}
```

## Token Usage
- Input tokens: {input_tokens}
- Output tokens: {output_tokens}
- Total tokens: {total_tokens}
- LLM calls: {call_count}

## Recommendations
{recommendations}
"""


def _build_recommendations(halt_reason: str) -> str:
    """Build actionable recommendations based on the halt reason.

    Parameters
    ----------
    halt_reason:
        The reason execution was halted.

    Returns
    -------
    Markdown-formatted recommendations.
    """
    recommendations: list[str] = []

    reason_lower = halt_reason.lower()
    if "attempt" in reason_lower:
        recommendations.append(
            "- Increase `max_attempts_per_task` in `.coder.yaml` if the "
            "agent is making progress but needs more iterations."
        )
        recommendations.append(
            "- Review the test failures to identify if the agent is stuck "
            "in a loop trying the same failing approach."
        )
    elif "time" in reason_lower:
        recommendations.append(
            "- Increase `max_wall_time_seconds` in `.coder.yaml` if the "
            "task is expected to take longer."
        )
        recommendations.append(
            "- Consider breaking the spec into smaller task groups to "
            "reduce per-group execution time."
        )
    elif "token" in reason_lower:
        recommendations.append(
            "- Increase `max_tokens` in `.coder.yaml` if the task "
            "requires more LLM interaction."
        )
        recommendations.append(
            "- Consider using a more efficient model to reduce token "
            "consumption."
        )
    else:
        recommendations.append(
            "- Review the halt reason and adjust safety limits "
            "in `.coder.yaml` as needed."
        )

    recommendations.append(
        "- Inspect the worktree for partial work that can be "
        "salvaged or continued manually."
    )

    return "\n".join(recommendations)


def generate_postmortem(
    state: dict[str, Any],
    worktree: Path,
    tracker: Any,
) -> Path:
    """Generate ``_postmortem.md`` and return its path.

    Writes the post-mortem markdown file to the worktree directory.
    If the worktree does not exist, falls back to the current working
    directory (15-REQ-3.E1). If writing fails, logs the error and
    continues without crashing (15-REQ-3.4).

    Parameters
    ----------
    state:
        The halted graph state dictionary.
    worktree:
        Path to the worktree directory.
    tracker:
        A token tracker with token usage attributes.

    Returns
    -------
    The path to the generated post-mortem file.
    """
    content = _format_postmortem(state, tracker)

    # Determine output directory: worktree if it exists, else cwd
    if worktree.exists() and worktree.is_dir():
        output_dir = worktree
    else:
        output_dir = Path.cwd()
        logger.warning(
            "Worktree directory %s does not exist; "
            "writing post-mortem to %s",
            worktree,
            output_dir,
        )

    output_path = output_dir / "_postmortem.md"

    try:
        output_path.write_text(content, encoding="utf-8")
        logger.info("Post-mortem written to %s", output_path)
    except OSError as exc:
        logger.error(
            "Failed to write post-mortem to %s: %s",
            output_path,
            exc,
        )

    return output_path


def generate_postmortem_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    """Terminal graph node that generates the post-mortem.

    Reads the worktree path and token tracker from the state,
    generates the post-mortem file, and returns the state unchanged
    (15-REQ-3.3).

    Parameters
    ----------
    state:
        The halted graph state dictionary. Must contain ``worktree``
        (str path) and ``token_tracker`` (tracker object).

    Returns
    -------
    The input state, unchanged.
    """
    worktree_str = state.get("worktree", ".")
    worktree = Path(worktree_str)
    tracker = state.get("token_tracker")

    try:
        generate_postmortem(state, worktree, tracker)
    except Exception as exc:
        logger.error(
            "Post-mortem generation failed in terminal node: %s",
            exc,
        )

    return state


def perform_graceful_shutdown(
    state: dict[str, Any],
    worktree: Path,
    tracker: Any,
) -> None:
    """Graceful shutdown: persist state and generate post-mortem.

    Executes the shutdown sequence:
    1. Persist the final run state to ``_run.json`` (15-REQ-5.2).
    2. Generate the post-mortem document (15-REQ-3.1).
    3. Leave the worktree intact (15-REQ-5.3) — no merge or cleanup.

    Parameters
    ----------
    state:
        The halted graph state dictionary.
    worktree:
        Path to the worktree directory.
    tracker:
        A token tracker with token usage attributes.
    """
    # Step 1: Persist state to _run.json
    try:
        persist_state(state, worktree)
    except Exception as exc:
        logger.error("Failed to persist state during shutdown: %s", exc)

    # Step 2: Generate post-mortem
    try:
        generate_postmortem(state, worktree, tracker)
    except Exception as exc:
        logger.error(
            "Failed to generate post-mortem during shutdown: %s", exc
        )

    # Step 3: Worktree is left intact — no merge or cleanup actions.
    logger.info("Graceful shutdown complete. Worktree left intact at %s", worktree)


def install_sigint_handler(
    state: dict[str, Any],
    worktree: Path,
    tracker: Any,
) -> Any:
    """Install a SIGINT handler that triggers graceful shutdown.

    Registers a signal handler for ``SIGINT`` (Ctrl+C) that calls
    :func:`perform_graceful_shutdown` with the provided state, worktree,
    and token tracker (15-REQ-5.E1).

    Parameters
    ----------
    state:
        The current graph state dictionary (will be captured by
        the handler closure).
    worktree:
        Path to the worktree directory.
    tracker:
        A token tracker with token usage attributes.

    Returns
    -------
    The previous signal handler, so it can be restored by the caller.
    """

    def _sigint_handler(signum: int, frame: Any) -> None:
        """Handle SIGINT by performing graceful shutdown."""
        logger.warning("SIGINT received — initiating graceful shutdown")
        state["halted"] = True
        state["halt_reason"] = state.get("halt_reason", "") or "SIGINT received"
        perform_graceful_shutdown(state, worktree, tracker)

    previous_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, _sigint_handler)
    return previous_handler
