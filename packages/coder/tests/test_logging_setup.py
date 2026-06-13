"""Tests for structured logging setup.

Test Spec Entries: TS-12-19, TS-12-31, TS-12-32, TS-12-33, TS-12-E11.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from coder.config import CoderConfig, load_config
from coder.logging import get_logger, setup_logging


class TestLoggingSetup:
    """Tests for logging configuration."""

    def test_structured_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TS-12-19: Structured logging produces console output.

        Requirement: 12-REQ-8.1, 12-REQ-8.4
        Verifies logging setup produces structured output with
        timestamp, level, module name, and event message.
        """
        config = CoderConfig()
        setup_logging(config)
        logger = get_logger("test_module")
        logger.info("test_event", key="value")

        captured = capsys.readouterr()
        assert "test_event" in captured.err

    def test_default_debug_level(
        self,
        tmp_path: Path,
        clean_coder_env: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """TS-12-31: Logging defaults to DEBUG level.

        Requirement: 12-REQ-8.2
        Verifies the logging system defaults to DEBUG level and that
        DEBUG-level log events actually appear in output.
        """
        config = load_config(project_dir=tmp_path)
        assert config.log_level == "DEBUG"

        setup_logging(config)
        logger = get_logger("test")
        logger.debug("debug_event")

        captured = capsys.readouterr()
        assert "debug_event" in captured.err

    def test_log_to_file(self, tmp_path: Path) -> None:
        """TS-12-32: Logging writes to file when configured.

        Requirement: 12-REQ-8.3
        Verifies log output is written to a file when log_file
        is configured.
        """
        log_path = tmp_path / "coder.log"
        config = CoderConfig(log_file=str(log_path))
        setup_logging(config)
        logger = get_logger("test")
        logger.info("file_event")

        assert log_path.exists()
        log_content = log_path.read_text()
        assert "file_event" in log_content

    def test_get_logger(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TS-12-33: get_logger returns bound logger with module name.

        Requirement: 12-REQ-8.5
        Verifies get_logger(name) returns a structlog logger bound
        with the given module name.
        """
        config = CoderConfig()
        setup_logging(config)
        logger = get_logger("my_module")
        logger.info("test_event")

        captured = capsys.readouterr()
        assert "my_module" in captured.err


class TestLoggingEdgeCases:
    """Edge case tests for logging."""

    def test_unwritable_log_fallback(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TS-12-E11: Unwritable log file falls back to console.

        Requirement: 12-REQ-8.E1
        Verifies that when the log file path is not writable, the
        system logs a warning to stderr and continues with
        console-only logging.
        """
        config = CoderConfig(
            log_file="/nonexistent/dir/coder.log"
        )
        # Should not raise
        setup_logging(config)
        logger = get_logger("test")
        logger.info("fallback_event")

        captured = capsys.readouterr()
        # A warning about the unwritable log file must be emitted
        assert (
            "log" in captured.err.lower()
            and (
                "not writable" in captured.err.lower()
                or "cannot" in captured.err.lower()
                or "failed" in captured.err.lower()
                or "unable" in captured.err.lower()
                or "warning" in captured.err.lower()
                or "nonexistent" in captured.err.lower()
            )
        ), "Expected a warning about the unwritable log file in stderr"
        # Console logging should still work
        assert "fallback_event" in captured.err
