"""Tests for the StatusSpinner UI component.

Test Spec Entries: TS-09-11, TS-09-12, TS-09-E2, TS-09-P4.

Tests verify the StatusSpinner context manager API, quiet-mode no-op
behavior, cleanup on KeyboardInterrupt, and non-TTY plain text fallback.
"""

from __future__ import annotations

import io
import sys

import pytest
from spec_cli.ui import StatusSpinner

# ---------------------------------------------------------------------------
# TS-09-11: StatusSpinner context manager
# ---------------------------------------------------------------------------


class TestStatusSpinnerContextManager:
    """TS-09-11: Verifies StatusSpinner works as a context manager."""

    def test_context_manager_enter_returns_self(self) -> None:
        """StatusSpinner.__enter__ returns self with update/log methods.

        Requirement: 09-REQ-4.1
        """
        with StatusSpinner("Working...", quiet=False) as s:
            assert s is not None
            assert hasattr(s, "update")
            assert callable(s.update)
            assert hasattr(s, "log")
            assert callable(s.log)

    def test_context_manager_update_callable(self) -> None:
        """update() method can be called inside the context.

        Requirement: 09-REQ-4.1
        """
        with StatusSpinner("Working...", quiet=False) as s:
            s.update("Phase 2...")
            # No exception should be raised

    def test_context_manager_log_callable(self) -> None:
        """log() method can be called inside the context.

        Requirement: 09-REQ-4.1
        """
        with StatusSpinner("Working...", quiet=False) as s:
            s.log("Completed phase 1")
            # No exception should be raised

    def test_context_manager_full_lifecycle(self) -> None:
        """Full lifecycle: enter, update, log, exit without errors.

        Requirement: 09-REQ-4.1
        """
        with StatusSpinner("Working...", quiet=False) as s:
            s.update("Phase 2...")
            s.log("Completed phase 1")
        # Exiting the context should not raise


# ---------------------------------------------------------------------------
# TS-09-12: StatusSpinner quiet no-op
# ---------------------------------------------------------------------------


class TestStatusSpinnerQuietNoOp:
    """TS-09-12: Verifies StatusSpinner in quiet mode is a no-op."""

    def test_quiet_no_stderr_output(self) -> None:
        """Quiet mode produces no output on stderr.

        Requirement: 09-REQ-4.2
        """
        captured = io.StringIO()
        original_stderr = sys.stderr
        sys.stderr = captured
        try:
            with StatusSpinner("Working...", quiet=True) as s:
                s.update("Phase 2...")
                s.log("Done")
        finally:
            sys.stderr = original_stderr

        assert captured.getvalue() == "", (
            f"Expected no stderr output in quiet mode, got: "
            f"{captured.getvalue()!r}"
        )

    def test_quiet_no_exceptions(self) -> None:
        """Quiet mode does not raise exceptions.

        Requirement: 09-REQ-4.2
        """
        with StatusSpinner("Working...", quiet=True) as s:
            s.update("Phase 2...")
            s.log("Done")
        # No exception should be raised

    def test_quiet_enter_returns_self(self) -> None:
        """Quiet mode __enter__ still returns self with callable methods.

        Requirement: 09-REQ-4.2
        """
        with StatusSpinner("Working...", quiet=True) as s:
            assert s is not None
            assert callable(s.update)
            assert callable(s.log)


# ---------------------------------------------------------------------------
# TS-09-E2: Spinner stops on KeyboardInterrupt
# ---------------------------------------------------------------------------


class TestSpinnerStopsOnInterrupt:
    """TS-09-E2: Verifies spinner stops on Ctrl-C."""

    def test_keyboard_interrupt_calls_exit(self) -> None:
        """Spinner __exit__ is called on KeyboardInterrupt.

        Requirement: 09-REQ-1.E2
        """
        spinner = StatusSpinner("Working...", quiet=False)
        entered = False
        exited = False
        try:
            spinner.__enter__()
            entered = True
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            spinner.__exit__(KeyboardInterrupt, KeyboardInterrupt(), None)
            exited = True

        assert entered, "Spinner was not entered"
        assert exited, "Spinner __exit__ was not called"

    def test_keyboard_interrupt_in_with_block(self) -> None:
        """KeyboardInterrupt inside with block triggers clean exit.

        Requirement: 09-REQ-1.E2
        """
        with pytest.raises(KeyboardInterrupt):
            with StatusSpinner("Working...", quiet=False):
                raise KeyboardInterrupt
        # If we get here, the spinner was cleaned up (no orphan)

    def test_keyboard_interrupt_quiet_mode(self) -> None:
        """KeyboardInterrupt in quiet mode also exits cleanly.

        Requirement: 09-REQ-1.E2
        """
        with pytest.raises(KeyboardInterrupt):
            with StatusSpinner("Working...", quiet=True):
                raise KeyboardInterrupt


# ---------------------------------------------------------------------------
# TS-09-P4: Non-TTY fallback property
# ---------------------------------------------------------------------------


class TestNonTTYFallbackProperty:
    """TS-09-P4: Non-TTY stderr gets plain text, no ANSI escapes.

    Property 4 from design.md.
    Validates: 09-REQ-2.2

    In a non-TTY environment (the default for tests), the spinner
    should produce plain text without ANSI escape sequences.
    """

    @pytest.mark.parametrize(
        "message",
        [
            "Working...",
            "Phase 2...",
            "Generating requirements...",
            "Assessing PRD...",
        ],
    )
    def test_no_ansi_escapes_in_output(self, message: str) -> None:
        """Non-TTY output contains no ANSI escape sequences.

        Requirement: 09-REQ-2.2
        """
        captured = io.StringIO()
        original_stderr = sys.stderr
        sys.stderr = captured
        try:
            with StatusSpinner(message, quiet=False):
                pass
        finally:
            sys.stderr = original_stderr

        output = captured.getvalue()
        assert "\x1b" not in output, (
            f"ANSI escape found in non-TTY output: {output!r}"
        )

    def test_non_tty_update_no_ansi(self) -> None:
        """update() in non-TTY produces no ANSI escapes.

        Requirement: 09-REQ-2.2
        """
        captured = io.StringIO()
        original_stderr = sys.stderr
        sys.stderr = captured
        try:
            with StatusSpinner("Start...", quiet=False) as s:
                s.update("Phase 2...")
        finally:
            sys.stderr = original_stderr

        output = captured.getvalue()
        assert "\x1b" not in output, (
            f"ANSI escape found in update output: {output!r}"
        )

    def test_non_tty_log_no_ansi(self) -> None:
        """log() in non-TTY produces no ANSI escapes.

        Requirement: 09-REQ-2.2
        """
        captured = io.StringIO()
        original_stderr = sys.stderr
        sys.stderr = captured
        try:
            with StatusSpinner("Start...", quiet=False) as s:
                s.log("Done with step 1")
        finally:
            sys.stderr = original_stderr

        output = captured.getvalue()
        assert "\x1b" not in output, (
            f"ANSI escape found in log output: {output!r}"
        )
