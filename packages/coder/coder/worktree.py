"""Git worktree lifecycle management.

Creates, merges, and cleans up git worktrees for isolated spec execution.
Also handles committing task group completions with conventional messages.

Implements Requirements:
    14-REQ-5.1 (worktree creation), 14-REQ-5.2 (worktree isolation),
    14-REQ-5.3 (worktree merge), 14-REQ-5.4 (worktree cleanup),
    14-REQ-5.5 (merge failure handling), 14-REQ-5.E1 (stale cleanup),
    14-REQ-5.E2 (creation failure), 14-REQ-7.2 (commit message format).

Note: Full implementation provided in task group 6.
      Stubs provided here for import compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from coder.errors import CoderError


class WorktreeError(CoderError):
    """Raised when a git worktree operation fails.

    Attributes:
        git_output: The raw git stderr output.
    """

    def __init__(
        self,
        message: str,
        *,
        git_output: str | None = None,
    ) -> None:
        super().__init__(message)
        self.git_output = git_output


@dataclass
class WorktreeInfo:
    """Information about a created git worktree.

    Attributes:
        path: Absolute path to the worktree directory.
        branch: Name of the worktree branch.
        spec_slug: The spec slug used for naming.
        source_branch: The branch the worktree was created from.
    """

    path: Path
    branch: str
    spec_slug: str
    source_branch: str


def create_worktree(
    repo_path: Path,
    spec_slug: str,
    model_name: str,
) -> WorktreeInfo:
    """Create an isolated git worktree for spec execution.

    Parameters
    ----------
    repo_path:
        Path to the repository root.
    spec_slug:
        The spec slug used for directory and branch naming.
    model_name:
        The model name used in the branch name.

    Returns
    -------
    A :class:`WorktreeInfo` with details about the created worktree.

    Raises
    ------
    WorktreeError
        If git worktree creation fails.
    """
    raise NotImplementedError("create_worktree: task group 6")


def merge_worktree(worktree: WorktreeInfo) -> bool:
    """Fast-forward merge the worktree branch into the source branch.

    Parameters
    ----------
    worktree:
        The worktree info from :func:`create_worktree`.

    Returns
    -------
    True if merge succeeded, False if fast-forward was not possible.
    """
    raise NotImplementedError("merge_worktree: task group 6")


def cleanup_worktree(worktree: WorktreeInfo) -> None:
    """Remove the worktree directory and prune the git registry.

    Parameters
    ----------
    worktree:
        The worktree info from :func:`create_worktree`.
    """
    raise NotImplementedError("cleanup_worktree: task group 6")


def commit_task_group(
    worktree: WorktreeInfo,
    group_num: int,
    title: str,
) -> None:
    """Commit changes with conventional message format.

    Parameters
    ----------
    worktree:
        The worktree info.
    group_num:
        The task group number.
    title:
        Title of the task group.
    """
    raise NotImplementedError("commit_task_group: task group 6")
