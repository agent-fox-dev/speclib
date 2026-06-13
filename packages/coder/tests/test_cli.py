"""Tests for CLI entry point.

Test Spec Entries: TS-12-17, TS-12-18, TS-12-28, TS-12-29, TS-12-30,
TS-12-E10, TS-12-E14.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner
from coder.cli import cli


@pytest.fixture()
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner(mix_stderr=False)


class TestRunCommand:
    """Tests for the coder run subcommand."""

    def test_run_command(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
        fake_anthropic_key: str,
    ) -> None:
        """TS-12-17: CLI run command validates campaign directory.

        Requirement: 12-REQ-7.1, 12-REQ-7.3
        Verifies coder run with a valid campaign dir succeeds.

        Note: ANTHROPIC_API_KEY is required since the CLI creates
        the provider from the model name (per skeptic review finding).
        """
        result = cli_runner.invoke(
            cli,
            [
                "run",
                str(campaign_dir),
                "--model",
                "claude-opus-4-6",
            ],
        )
        assert result.exit_code == 0

    def test_missing_campaign_dir(
        self, cli_runner: CliRunner
    ) -> None:
        """TS-12-18 / TS-12-E14: CLI run rejects missing campaign directory.

        Requirement: 12-REQ-7.E1
        Verifies coder run fails for nonexistent directory.
        """
        result = cli_runner.invoke(
            cli, ["run", "/nonexistent/path"]
        )
        assert result.exit_code == 1
        output = result.output + (result.stderr or "")
        assert (
            "not exist" in output.lower()
            or "not found" in output.lower()
            or "no such" in output.lower()
            or "error" in output.lower()
        )

    def test_run_arguments(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
        fake_anthropic_key: str,
    ) -> None:
        """TS-12-28: CLI run accepts campaign_dir, --model, and --repo.

        Requirement: 12-REQ-7.2
        Verifies coder run accepts all documented arguments.
        """
        result = cli_runner.invoke(
            cli,
            [
                "run",
                str(campaign_dir),
                "--model",
                "claude-opus-4-6",
                "--repo",
                "/tmp/repo",
            ],
        )
        assert result.exit_code == 0

    def test_run_help(self, cli_runner: CliRunner) -> None:
        """TS-12-30: CLI run --help displays usage.

        Requirement: 12-REQ-7.5
        Verifies coder run --help displays usage information for all
        arguments and options including the positional campaign_dir.
        """
        result = cli_runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        output = result.output.lower()
        assert (
            "campaign_dir" in output or "campaign-dir" in output
        ), "Help output should mention campaign_dir positional argument"
        assert "--model" in output
        assert "--repo" in output


class TestModelsCommand:
    """Tests for the coder models subcommand."""

    def test_models_subcommand(
        self, cli_runner: CliRunner
    ) -> None:
        """TS-12-29: CLI models subcommand lists providers.

        Requirement: 12-REQ-7.4
        Verifies coder models lists known model name prefixes and
        their associated providers.
        """
        result = cli_runner.invoke(cli, ["models"])
        assert result.exit_code == 0
        output = result.output.lower()
        assert "claude" in output
        assert "gemini" in output


class TestCLIEdgeCases:
    """Edge case tests for CLI."""

    def test_provider_creation_failure(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
        clean_coder_env: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """TS-12-E10: CLI prints provider error on creation failure.

        Requirement: 12-REQ-7.E2
        Verifies coder run prints the provider error to stderr and
        exits with code 1 when the provider cannot be created.
        """
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = cli_runner.invoke(
            cli,
            [
                "run",
                str(campaign_dir),
                "--model",
                "claude-opus-4-6",
            ],
        )
        assert result.exit_code == 1
        output = result.output + (result.stderr or "")
        assert (
            "ANTHROPIC_API_KEY" in output
            or "provider" in output.lower()
            or "error" in output.lower()
        )
