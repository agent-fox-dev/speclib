"""Tests for the install-skill CLI command.

Test Spec Entries: TS-05-14 through TS-05-18,
TS-05-E1 through TS-05-E3, TS-05-P2, TS-05-SMOKE-1.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture()
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture()
def patched_home(tmp_path: Path) -> Path:
    """Patch Path.home() to return tmp_path for install-skill isolation."""
    with patch.object(Path, "home", return_value=tmp_path):
        yield tmp_path


# ===================================================================
# TS-05-14: install-skill detects agent CLI
# Requirement: 05-REQ-5.1
# ===================================================================


class TestDetectAgentCli:
    """TS-05-14: Verify detect_agent_cli finds Claude Code and Gemini CLI."""

    def test_detect_claude(self, patched_home: Path) -> None:
        """detect_agent_cli returns 'claude' when ~/.claude/ exists."""
        from spec_cli.skill import detect_agent_cli

        (patched_home / ".claude").mkdir()
        result = detect_agent_cli()
        assert result == "claude"

    def test_detect_gemini(self, patched_home: Path) -> None:
        """detect_agent_cli returns 'gemini' when ~/.gemini/ exists."""
        from spec_cli.skill import detect_agent_cli

        (patched_home / ".gemini").mkdir()
        result = detect_agent_cli()
        assert result == "gemini"

    def test_detect_none(self, patched_home: Path) -> None:
        """detect_agent_cli returns None when no agent CLI directory exists."""
        from spec_cli.skill import detect_agent_cli

        result = detect_agent_cli()
        assert result is None


# ===================================================================
# TS-05-15: install-skill copies file to detected location
# Requirement: 05-REQ-5.2
# ===================================================================


class TestInstallCopiesFile:
    """TS-05-15: Verify install-skill copies skill file to agent dir."""

    def test_install_copies_file(
        self, cli_runner: CliRunner, patched_home: Path
    ) -> None:
        """install-skill copies the skill file when agent CLI is detected."""
        from spec_cli.cli import cli
        from spec_cli.skill import SKILL_FILE_PATH

        (patched_home / ".claude").mkdir()
        result = cli_runner.invoke(cli, ["install-skill"])
        assert result.exit_code == 0, f"Expected exit code 0, got: {result.output}"
        installed = patched_home / ".claude" / "skills" / "spec.md"
        assert installed.exists(), "Installed skill file must exist"
        assert installed.read_text() == SKILL_FILE_PATH.read_text(), (
            "Installed file content must match source"
        )


# ===================================================================
# TS-05-16: install-skill with --target flag
# Requirement: 05-REQ-5.3
# ===================================================================


class TestInstallWithTarget:
    """TS-05-16: Verify install-skill uses explicit --target."""

    def test_install_with_target_claude(
        self, cli_runner: CliRunner, patched_home: Path
    ) -> None:
        """install-skill --target claude creates the skill file."""
        from spec_cli.cli import cli

        result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
        assert result.exit_code == 0, f"Expected exit code 0, got: {result.output}"
        installed = patched_home / ".claude" / "skills" / "spec.md"
        assert installed.exists(), "Installed skill file must exist with --target"


# ===================================================================
# TS-05-17: install-skill overwrites existing file
# Requirement: 05-REQ-5.4
# ===================================================================


class TestInstallOverwrites:
    """TS-05-17: Verify install-skill overwrites an existing skill file."""

    def test_install_overwrites_existing(
        self, cli_runner: CliRunner, patched_home: Path
    ) -> None:
        """install-skill overwrites an existing skill file with current content."""
        from spec_cli.cli import cli
        from spec_cli.skill import SKILL_FILE_PATH

        skill_dir = patched_home / ".claude" / "skills"
        skill_dir.mkdir(parents=True)
        (skill_dir / "spec.md").write_text("old content")

        result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
        assert result.exit_code == 0, f"Expected exit code 0, got: {result.output}"
        assert (skill_dir / "spec.md").read_text() == SKILL_FILE_PATH.read_text(), (
            "File content must be replaced with current skill file content"
        )
        output_lower = result.output.lower()
        assert "updated" in output_lower or "installed" in output_lower, (
            "Output must indicate the file was updated or installed"
        )


# ===================================================================
# TS-05-18: install-skill prints success message
# Requirement: 05-REQ-5.5
# ===================================================================


class TestInstallSuccessMessage:
    """TS-05-18: Verify install-skill prints the installed file path on success."""

    def test_install_success_message(
        self, cli_runner: CliRunner, patched_home: Path
    ) -> None:
        """install-skill output contains the installed file path."""
        from spec_cli.cli import cli

        result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
        assert result.exit_code == 0, f"Expected exit code 0, got: {result.output}"
        assert ".claude/skills/spec.md" in result.output, (
            "Output must contain the installed file path"
        )


# ===================================================================
# Edge Case Tests
# ===================================================================


class TestEdgeCases:
    """Edge case tests for install-skill command."""

    def test_ts05_e1_no_agent_detected(
        self, cli_runner: CliRunner, patched_home: Path
    ) -> None:
        """TS-05-E1: install-skill errors without agent CLI or --target.

        Requirement: 05-REQ-5.E1
        """
        from spec_cli.cli import cli

        result = cli_runner.invoke(cli, ["install-skill"])
        assert result.exit_code != 0, (
            "Must exit with non-zero when no agent CLI detected"
        )
        output_lower = result.output.lower()
        assert "claude" in output_lower, (
            "Error must list supported agent: claude"
        )
        assert "gemini" in output_lower, (
            "Error must list supported agent: gemini"
        )

    def test_ts05_e2_creates_missing_dir(
        self, cli_runner: CliRunner, patched_home: Path
    ) -> None:
        """TS-05-E2: install-skill creates the skill directory if it does not exist.

        Requirement: 05-REQ-5.E2
        """
        from spec_cli.cli import cli

        (patched_home / ".claude").mkdir()
        # Note: ~/.claude/skills/ does NOT exist yet
        result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
        assert result.exit_code == 0, f"Expected exit code 0, got: {result.output}"
        assert (patched_home / ".claude" / "skills").is_dir(), (
            "Skills directory must be created"
        )
        assert (patched_home / ".claude" / "skills" / "spec.md").exists(), (
            "Skill file must be installed"
        )

    def test_ts05_e3_missing_source(
        self, cli_runner: CliRunner, patched_home: Path
    ) -> None:
        """TS-05-E3: install-skill raises SpeclibError if source file is missing.

        Requirement: 05-REQ-5.E3

        Note: We test both the exit code and that a SpeclibError is the
        underlying cause. The CLI error handler may catch SpeclibError and
        convert it to a non-zero exit, so we verify the error message too.
        """
        from spec_cli.cli import cli

        with patch("spec_cli.skill.SKILL_FILE_PATH", Path("/nonexistent/spec.md")):
            result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
        assert result.exit_code != 0, (
            "Must exit with non-zero code when source file is missing"
        )
        output_lower = result.output.lower()
        has_error_msg = "missing" in output_lower or "not found" in output_lower
        assert has_error_msg, (
            "Error output must mention missing or not found source file"
        )


# ===================================================================
# Property Tests
# ===================================================================


class TestProperties:
    """Property tests for install-skill command."""

    @pytest.mark.parametrize("target", ["claude", "gemini"])
    def test_ts05_p2_property_installed_matches_source(
        self, cli_runner: CliRunner, patched_home: Path, target: str
    ) -> None:
        """TS-05-P2: Installed file matches source.

        Property 2 from design.md.
        Validates: 05-REQ-5.2, 05-REQ-5.4.
        For any target, the installed file is byte-identical to the source.
        """
        from spec_cli.cli import cli
        from spec_cli.skill import SKILL_FILE_PATH

        result = cli_runner.invoke(cli, ["install-skill", "--target", target])
        assert result.exit_code == 0, f"Expected exit code 0, got: {result.output}"
        target_dirs = {"claude": ".claude/skills", "gemini": ".gemini/skills"}
        installed = patched_home / target_dirs[target] / "spec.md"
        assert installed.read_bytes() == SKILL_FILE_PATH.read_bytes(), (
            f"Installed file for target '{target}' must be byte-identical to source"
        )


# ===================================================================
# Integration Smoke Test
# ===================================================================


class TestSmoke:
    """Integration smoke tests for install-skill."""

    def test_ts05_smoke1_full_install_flow(
        self, cli_runner: CliRunner, patched_home: Path
    ) -> None:
        """TS-05-SMOKE-1: Full install-skill flow.

        End-to-end skill installation from package source to agent CLI directory.
        """
        from spec_cli.cli import cli
        from spec_cli.skill import SKILL_FILE_PATH

        (patched_home / ".claude").mkdir()
        result = cli_runner.invoke(cli, ["install-skill"])
        assert result.exit_code == 0, f"Expected exit code 0, got: {result.output}"
        installed = patched_home / ".claude" / "skills" / "spec.md"
        assert installed.exists(), "Installed skill file must exist"
        assert installed.read_bytes() == SKILL_FILE_PATH.read_bytes(), (
            "Installed file must be byte-identical to source"
        )
        has_path_in_output = (
            str(installed) in result.output
            or ".claude/skills/spec.md" in result.output
        )
        assert has_path_in_output, (
            "Success message must include the installed file path"
        )
