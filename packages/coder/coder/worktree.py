"""Git worktree lifecycle management.

Creates, merges, and cleans up git worktrees for isolated spec execution.
Also handles committing task group completions with conventional messages.

Implements Requirements:
    14-REQ-5.1 (worktree creation), 14-REQ-5.2 (worktree isolation),
    14-REQ-5.3 (worktree merge), 14-REQ-5.4 (worktree cleanup),
    14-REQ-5.5 (merge failure handling), 14-REQ-5.E1 (stale cleanup),
    14-REQ-5.E2 (creation failure), 14-REQ-7.2 (commit message format).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from coder.errors import CoderError

logger = logging.getLogger(__name__)


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


def _get_current_branch(repo_path: Path) -> str:
    """Return the current branch name of the repository.

    Falls back to ``"main"`` if HEAD is detached.
    """
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    branch = result.stdout.strip()
    if result.returncode != 0 or branch == "HEAD":
        return "main"
    return branch


def _remove_stale_worktree(
    repo_path: Path, worktree_path: Path, branch: str
) -> None:
    """Remove a stale worktree directory and its associated branch.

    Handles the case where a worktree directory exists from a previous
    run (14-REQ-5.E1). Also removes the branch if it exists so
    ``git worktree add -b`` can recreate it.
    """
    # Try to remove via git worktree first (clean registry entry)
    subprocess.run(
        ["git", "-C", str(repo_path), "worktree", "remove", "--force",
         str(worktree_path)],
        capture_output=True,
        text=True,
    )
    # Force-remove directory if it still exists
    if worktree_path.exists():
        shutil.rmtree(worktree_path)

    # Prune stale worktree registry entries
    subprocess.run(
        ["git", "-C", str(repo_path), "worktree", "prune"],
        capture_output=True,
        text=True,
    )

    # Delete the branch if it already exists so we can recreate it
    subprocess.run(
        ["git", "-C", str(repo_path), "branch", "-D", branch],
        capture_output=True,
        text=True,
    )


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
    worktree_path = repo_path / ".coder" / "worktrees" / spec_slug
    branch = f"coder/{model_name}/{spec_slug}"
    source_branch = _get_current_branch(repo_path)

    # Handle stale worktree from a previous run (14-REQ-5.E1)
    if worktree_path.exists():
        logger.info(
            "Removing stale worktree at %s", worktree_path
        )
        _remove_stale_worktree(repo_path, worktree_path, branch)

    # Ensure parent directory exists
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the worktree with a new branch
    result = subprocess.run(
        [
            "git", "-C", str(repo_path),
            "worktree", "add",
            "-b", branch,
            str(worktree_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise WorktreeError(
            f"Failed to create worktree for '{spec_slug}': "
            f"{result.stderr.strip()}",
            git_output=result.stderr.strip(),
        )

    logger.info(
        "Created worktree at %s on branch %s",
        worktree_path, branch,
    )

    return WorktreeInfo(
        path=worktree_path,
        branch=branch,
        spec_slug=spec_slug,
        source_branch=source_branch,
    )


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
    # Determine the original repo path (parent of .coder/worktrees/<slug>)
    repo_path = worktree.path.parent.parent.parent

    result = subprocess.run(
        [
            "git", "-C", str(repo_path),
            "merge", "--ff-only", worktree.branch,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(
            "Fast-forward merge failed for branch %s: %s",
            worktree.branch,
            result.stderr.strip(),
        )
        return False

    logger.info(
        "Merged branch %s into %s",
        worktree.branch, worktree.source_branch,
    )
    return True


def cleanup_worktree(worktree: WorktreeInfo) -> None:
    """Remove the worktree directory and prune the git registry.

    Parameters
    ----------
    worktree:
        The worktree info from :func:`create_worktree`.
    """
    repo_path = worktree.path.parent.parent.parent

    # Remove the worktree via git
    subprocess.run(
        [
            "git", "-C", str(repo_path),
            "worktree", "remove", "--force", str(worktree.path),
        ],
        capture_output=True,
        text=True,
    )

    # Force-remove directory if git didn't clean it up
    if worktree.path.exists():
        shutil.rmtree(worktree.path)

    # Prune worktree registry
    subprocess.run(
        ["git", "-C", str(repo_path), "worktree", "prune"],
        capture_output=True,
        text=True,
    )

    # Delete the branch
    subprocess.run(
        ["git", "-C", str(repo_path), "branch", "-D", worktree.branch],
        capture_output=True,
        text=True,
    )

    logger.info(
        "Cleaned up worktree at %s (branch %s)",
        worktree.path, worktree.branch,
    )


def commit_task_group(
    worktree: WorktreeInfo,
    group_num: int,
    title: str,
) -> None:
    """Commit changes with conventional message format.

    The commit message follows the format:
    ``feat(<spec_slug>): complete task group <N> — <title>``

    If there is nothing to commit (clean working tree), logs a warning
    and returns without error (14-REQ-7.E1).

    Parameters
    ----------
    worktree:
        The worktree info.
    group_num:
        The task group number.
    title:
        Title of the task group.
    """
    message = (
        f"feat({worktree.spec_slug}): "
        f"complete task group {group_num} — {title}"
    )

    result = subprocess.run(
        [
            "git", "-C", str(worktree.path),
            "commit", "-m", message,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip().lower()
        stdout = result.stdout.strip().lower()
        if "nothing to commit" in stderr or "nothing to commit" in stdout:
            logger.warning(
                "Warning: nothing to commit for task group %d (%s)",
                group_num, title,
            )
        else:
            logger.warning(
                "Warning: commit failed for task group %d: %s",
                group_num,
                result.stderr.strip(),
            )
        return

    logger.info(
        "Committed task group %d: %s", group_num, title
    )
