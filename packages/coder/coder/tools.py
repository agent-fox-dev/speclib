"""LangChain coding tools for the TDD execution engine.

Provides file I/O and shell access tools that operate within a worktree
boundary. All path arguments are resolved relative to the worktree root
and must not escape it.

Implements Requirements:
    14-REQ-4.1 (read_file), 14-REQ-4.2 (write_file),
    14-REQ-4.3 (run_command), 14-REQ-4.4 (list_directory),
    14-REQ-4.5 (path containment),
    14-REQ-4.E1 (command timeout), 14-REQ-4.E2 (binary file),
    14-REQ-4.E3 (symlink rejection).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from langchain_core.tools import StructuredTool


def _validate_path(worktree: Path, rel_path: str) -> Path | str:
    """Resolve *rel_path* relative to *worktree* and enforce containment.

    Returns the resolved :class:`Path` if valid, or an error string if the
    path escapes the worktree boundary.

    Parameters
    ----------
    worktree:
        Absolute path to the worktree root.
    rel_path:
        A relative path string provided by the caller.

    Returns
    -------
    Resolved :class:`Path` on success, or an error message string.
    """
    # Reject absolute paths outright
    if rel_path.startswith("/"):
        return (
            "Error: Absolute paths are denied. "
            "Use paths relative to the worktree root."
        )

    resolved_worktree = worktree.resolve()
    resolved = (resolved_worktree / rel_path).resolve()

    if not str(resolved).startswith(str(resolved_worktree)):
        return "Error: Path traversal denied. Path escapes the worktree boundary."

    return resolved


def _is_binary(path: Path, sample_size: int = 8192) -> bool:
    """Heuristic check for binary file content.

    Reads at most *sample_size* bytes and checks for null bytes.

    Parameters
    ----------
    path:
        Path to the file to inspect.
    sample_size:
        Number of bytes to sample.

    Returns
    -------
    True if the file appears to be binary.
    """
    try:
        chunk = path.read_bytes()[:sample_size]
    except OSError:
        return False
    return b"\x00" in chunk


def create_coding_tools(worktree_dir: Path) -> dict[str, StructuredTool]:
    """Create coding tools bound to *worktree_dir*.

    Returns a dictionary of tool name -> ``StructuredTool`` instances that
    perform file I/O and shell execution within the worktree directory.

    Parameters
    ----------
    worktree_dir:
        Absolute path to the worktree root directory.

    Returns
    -------
    Dictionary mapping tool names to LangChain tool objects.
    """

    def read_file(path: str) -> str:
        """Read a file at *path* relative to the worktree root.

        Returns the file contents as a string, or an error message if
        the file cannot be read (e.g., binary, missing, path escape).
        """
        result = _validate_path(worktree_dir, path)
        if isinstance(result, str):
            return result

        resolved: Path = result
        if not resolved.exists():
            return f"Error: File not found: {path}"
        if not resolved.is_file():
            return f"Error: Not a file: {path}"
        if _is_binary(resolved):
            return f"Error: Binary file cannot be read as text: {path}"

        try:
            return resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"Error: Binary file cannot be read as text: {path}"
        except OSError as exc:
            return f"Error: {exc}"

    def write_file(path: str, content: str) -> str:
        """Write *content* to a file at *path* relative to the worktree.

        Creates parent directories if they don't exist. Rejects writes
        to symlinks for security.

        Returns a confirmation message or an error string.
        """
        # Reject absolute paths
        if path.startswith("/"):
            return (
                "Error: Absolute paths are denied. "
                "Use paths relative to the worktree root."
            )

        resolved_worktree = worktree_dir.resolve()

        # Check the unresolved (literal) path for symlinks BEFORE resolving
        # (14-REQ-4.E3). Path.resolve() follows symlinks, so we must check
        # the raw join first.
        literal_path = resolved_worktree / path
        if literal_path.is_symlink():
            return f"Error: Security error — refusing to write to symlink: {path}"

        # Now validate containment using the resolved path
        result = _validate_path(worktree_dir, path)
        if isinstance(result, str):
            return result

        resolved: Path = result

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
        except OSError as exc:
            return f"Error: {exc}"
        return f"OK: Wrote {len(content)} bytes to {path}"

    def run_command(command: str, timeout: int = 120) -> str:
        """Execute a shell command in the worktree directory.

        Returns a formatted string with stdout, stderr, and exit code.

        Parameters
        ----------
        command:
            The shell command to run.
        timeout:
            Timeout in seconds (default 120, per 14-REQ-4.E1).
        """
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(worktree_dir),
                timeout=timeout,
            )
            parts = []
            if proc.stdout:
                parts.append(f"stdout:\n{proc.stdout}")
            if proc.stderr:
                parts.append(f"stderr:\n{proc.stderr}")
            parts.append(f"exit_code: {proc.returncode}")
            return "\n".join(parts)
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds (timeout)"
        except OSError as exc:
            return f"Error: {exc}"

    def list_directory(path: str = ".") -> str:
        """List files and directories at *path* relative to the worktree.

        Returns a formatted listing string.
        """
        result = _validate_path(worktree_dir, path)
        if isinstance(result, str):
            return result

        resolved: Path = result
        if not resolved.exists():
            return f"Error: Directory not found: {path}"
        if not resolved.is_dir():
            return f"Error: Not a directory: {path}"

        try:
            entries = sorted(resolved.iterdir())
        except OSError as exc:
            return f"Error: {exc}"

        lines = []
        for entry in entries:
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"  {entry.name}{suffix}")
        return f"{path}/\n" + "\n".join(lines) if lines else f"{path}/ (empty)"

    # Build and return the tool dictionary
    read_file_tool = StructuredTool.from_function(
        func=read_file,
        name="read_file",
        description="Read a file at a path relative to the worktree root.",
    )
    write_file_tool = StructuredTool.from_function(
        func=write_file,
        name="write_file",
        description="Write content to a file at a path relative to the worktree root.",
    )
    run_command_tool = StructuredTool.from_function(
        func=run_command,
        name="run_command",
        description="Execute a shell command in the worktree directory.",
    )
    list_directory_tool = StructuredTool.from_function(
        func=list_directory,
        name="list_directory",
        description=(
            "List files and directories at a path "
            "relative to the worktree root."
        ),
    )

    return {
        "read_file": read_file_tool,
        "write_file": write_file_tool,
        "run_command": run_command_tool,
        "list_directory": list_directory_tool,
    }
