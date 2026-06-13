"""Verification runner for executing test commands.

Executes shell commands from the spec pack's ``test_commands`` section
and reports pass/fail status. Captures stdout, stderr, exit code, and
enforces configurable timeouts.

Implements Requirements:
    14-REQ-6.1 (command order), 14-REQ-6.2 (result capture),
    14-REQ-6.3 (exit code semantics), 14-REQ-6.4 (timeout),
    14-REQ-6.E1 (empty command skip), 14-REQ-6.E2 (binary not found).
"""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from afspec.models import TestCommands  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of executing a verification command.

    Attributes:
        passed: Whether all commands succeeded (exit code 0).
        exit_code: Exit code of the last (or failing) command.
        stdout: Combined stdout from all commands.
        stderr: Combined stderr from all commands.
        command: The command string that was executed.
        elapsed_seconds: Total wall-clock time in seconds.
        timed_out: Whether the command was killed due to timeout.
        commands_run: List of command category names that were executed.
    """

    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    command: str
    elapsed_seconds: float
    timed_out: bool = False
    commands_run: list[str] = field(default_factory=list)


class VerificationRunner:
    """Execute test commands within a worktree and report results.

    Parameters
    ----------
    worktree_path:
        Path to the git worktree where commands are executed.
    """

    def __init__(self, worktree_path: Path) -> None:
        self.worktree_path = worktree_path

    def run(
        self,
        test_commands: TestCommands,
        *,
        is_final_group: bool = True,
        timeout: int = 300,
    ) -> VerificationResult:
        """Execute test commands and return a verification result.

        Parameters
        ----------
        test_commands:
            The test command configuration from the spec pack.
        is_final_group:
            If True, run all commands (spec_tests, all_tests, linter).
            If False, run only spec_tests.
        timeout:
            Per-command timeout in seconds (default 300).

        Returns
        -------
        A :class:`VerificationResult` with aggregated results.
        """
        # Build ordered list of (category_name, command_string) pairs
        commands_to_run: list[tuple[str, str]] = []

        if is_final_group:
            commands_to_run.append(("spec_tests", test_commands.spec_tests))
            commands_to_run.append(("all_tests", test_commands.all_tests))
            commands_to_run.append(("linter", test_commands.linter))
        else:
            commands_to_run.append(("spec_tests", test_commands.spec_tests))

        all_stdout: list[str] = []
        all_stderr: list[str] = []
        commands_run: list[str] = []
        last_exit_code = 0
        overall_passed = True
        timed_out = False
        total_start = time.monotonic()

        for category, cmd in commands_to_run:
            # Skip empty/null commands (14-REQ-6.E1)
            if not cmd or not cmd.strip():
                logger.warning(
                    "Skipping empty %s command", category
                )
                continue

            commands_run.append(category)

            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(self.worktree_path),
                    timeout=timeout,
                )
                last_exit_code = proc.returncode
                if proc.stdout:
                    all_stdout.append(proc.stdout)
                if proc.stderr:
                    all_stderr.append(proc.stderr)

                if proc.returncode != 0:
                    overall_passed = False
                    break  # Stop on first failure

            except subprocess.TimeoutExpired:
                timed_out = True
                overall_passed = False
                last_exit_code = -1
                all_stderr.append(
                    f"Command timed out after {timeout} seconds: {cmd}"
                )
                break

            except FileNotFoundError as exc:
                overall_passed = False
                last_exit_code = 127
                all_stderr.append(f"Command not found: {exc}")
                break

            except OSError as exc:
                overall_passed = False
                last_exit_code = 1
                all_stderr.append(f"Error executing command: {exc}")
                break

        elapsed = time.monotonic() - total_start

        return VerificationResult(
            passed=overall_passed,
            exit_code=last_exit_code,
            stdout="\n".join(all_stdout),
            stderr="\n".join(all_stderr),
            command="; ".join(cmd for _, cmd in commands_to_run if cmd),
            elapsed_seconds=elapsed,
            timed_out=timed_out,
            commands_run=commands_run,
        )
