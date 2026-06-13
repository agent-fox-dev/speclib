"""Run state persistence for the TDD execution engine.

Persists execution state to ``_run.json`` in the worktree root after
every node transition. Uses atomic write (temp file + rename) to
prevent corruption on crash.

Implements Requirements:
    14-REQ-8.1 (state persistence), 14-REQ-8.2 (transition history),
    14-REQ-8.3 (atomic write), 14-REQ-8.E1 (write failure handling).

Note: Full implementation provided in task group 3.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StateTransition:
    """A single state transition record for the history array.

    Attributes:
        phase: The workflow phase name.
        task_group: The task group number.
        attempt: The attempt count at the time of transition.
        timestamp: ISO 8601 timestamp of the transition.
        result: Result indicator (e.g. "ok", "fail", or null).
    """

    phase: str
    task_group: int
    attempt: int
    timestamp: str
    result: str | None = None


def persist_state(
    state: dict[str, Any],
    worktree_path: Path,
) -> None:
    """Write the current state to ``_run.json`` atomically.

    Writes to a temporary file first, then renames to the target path
    to ensure crash safety (14-REQ-8.3). If the write fails, logs a
    warning and continues (14-REQ-8.E1).

    Parameters
    ----------
    state:
        Current graph state dictionary.
    worktree_path:
        Path to the worktree root directory.
    """
    run_json_path = worktree_path / "_run.json"

    # Serialize history entries if they are StateTransition objects
    serializable_state: dict[str, Any] = {}
    for key, value in state.items():
        if key == "history" and isinstance(value, list):
            serializable_state[key] = [
                asdict(t) if isinstance(t, StateTransition) else t
                for t in value
            ]
        else:
            serializable_state[key] = value

    try:
        # Write to temp file, then atomic rename (14-REQ-8.3)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(worktree_path), suffix=".tmp"
        )
        # Close the low-level fd immediately; we re-open via builtins.open
        # so that standard Python I/O (and test mocks) can intercept writes.
        os.close(fd)
        try:
            with open(tmp_path, "w") as f:  # noqa: SIM115
                json.dump(serializable_state, f, indent=2)
            os.rename(tmp_path, str(run_json_path))
        except BaseException:
            # Clean up temp file on failure if it still exists
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except OSError as exc:
        logger.warning(
            "Warning: Failed to write _run.json: %s", exc
        )
