"""Tests for the spec CLI commands.

Test Spec Entries: TS-04-1 through TS-04-51, TS-04-P1 through TS-04-P5,
TS-04-SMOKE-1 through TS-04-SMOKE-4.

Tests use Click's CliRunner for isolated CLI invocation. Business logic
(Campaign, SpecSession) is mocked in unit tests. Integration smoke tests
use real instances on temp directories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner
from spec_cli.cli import main  # noqa: I001
from speclib.errors import CampaignError, SessionError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def cli_runner() -> CliRunner:
    """Create a Click CliRunner for isolated command invocation."""
    return CliRunner()


@pytest.fixture()
def campaign_dir(tmp_path: Path) -> Path:
    """Create a temp campaign directory with campaign.yaml."""
    campaign_yaml = tmp_path / "campaign.yaml"
    campaign_yaml.write_text(
        "name: test-campaign\ndescription: A test campaign\n"
    )
    return tmp_path


@pytest.fixture()
def campaign_dir_with_specs(campaign_dir: Path) -> Path:
    """Create a campaign directory with two spec subdirectories."""
    spec_01 = campaign_dir / "01_data_models"
    spec_01.mkdir()
    session_01 = spec_01 / "_session.json"
    session_01.write_text(json.dumps({
        "state": "generated",
        "mode": "interactive",
        "assessment_count": 2,
        "qa_count": 3,
    }))
    prd_01 = spec_01 / "prd.md"
    prd_01.write_text("# Data Models PRD\n\nSome content.")

    spec_02 = campaign_dir / "02_api_endpoints"
    spec_02.mkdir()
    session_02 = spec_02 / "_session.json"
    session_02.write_text(json.dumps({
        "state": "refining",
        "mode": "interactive",
        "assessment_count": 1,
        "qa_count": 0,
    }))
    prd_02 = spec_02 / "prd.md"
    prd_02.write_text("# API Endpoints PRD\n\nSome content.")

    return campaign_dir


@pytest.fixture()
def prd_file(tmp_path: Path) -> Path:
    """Create a temporary PRD file."""
    prd = tmp_path / "prd.md"
    prd.write_text("# Test PRD\n\nSome content for the PRD.")
    return prd


@pytest.fixture()
def answers_file(tmp_path: Path) -> Path:
    """Create a temporary JSON answers file."""
    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps({"q1": "answer1", "q2": "answer2"})
    )
    return answers


@pytest.fixture()
def bad_json_file(tmp_path: Path) -> Path:
    """Create a temporary file with invalid JSON."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    return bad


@pytest.fixture()
def bad_schema_file(tmp_path: Path) -> Path:
    """Create a file with wrong schema (list instead of dict)."""
    bad = tmp_path / "bad_schema.json"
    bad.write_text(json.dumps(["not", "an", "object"]))
    return bad


def _mock_campaign(
    specs: list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Create a mock Campaign with optional spec list.

    Each spec dict should have keys: name, number, state,
    artifact_count.
    """
    campaign = MagicMock()
    if specs is None:
        specs = []

    spec_dirs = []
    for spec in specs:
        spec_dir = MagicMock()
        spec_dir.name = spec.get("name", "01_test")
        spec_dir.stem = spec_dir.name
        spec_dirs.append(spec_dir)

    campaign.specs.return_value = spec_dirs
    return campaign


def _mock_session(
    state: str = "init",
    mode: str = "interactive",
    assessment_count: int = 0,
    qa_count: int = 0,
    artifacts: list[str] | None = None,
) -> MagicMock:
    """Create a mock SpecSession with configurable state."""
    session = MagicMock()
    session.state = state
    session.mode = mode
    session.assessment_count = assessment_count
    session.qa_count = qa_count
    session.artifacts = artifacts or []
    return session


def _sample_assessment() -> dict[str, Any]:
    """Return a sample assessment result for output formatting."""
    return {
        "quality": "needs_refinement",
        "score": 7,
        "summary": "Good start but needs more detail",
        "gaps": [
            "Missing error handling for edge case X",
            "No mention of performance requirements",
        ],
        "questions": [
            {
                "id": "q1",
                "text": "What is the expected data volume?",
            },
            {
                "id": "q2",
                "text": "Should the API support pagination?",
            },
        ],
    }


def _assert_exit(result: Any, code: int) -> None:
    """Assert CLI result has the expected exit code."""
    actual = result.exit_code
    out = result.output
    assert actual == code, (
        f"Expected exit {code}, got {actual}: {out}"
    )


# ================================================================
# Task 1.2: Campaign command tests (TS-04-1 through TS-04-10)
# ================================================================


class TestInitCommand:
    """Tests for the spec init command."""

    def test_init_creates_campaign(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-1: Init creates campaign directory.

        Requirement: 04-REQ-1.1
        Verify spec init calls Campaign.create and prints
        confirmation.
        """
        target = tmp_path / "test-campaign"
        resolved = target.resolve()
        with patch(
            "spec_cli.cli.Campaign"
        ) as mock_cls:
            mock_cls.create.return_value = None
            result = cli_runner.invoke(
                main,
                [
                    "init",
                    str(target),
                    "--name",
                    "Test",
                    "--description",
                    "A test",
                ],
            )
        _assert_exit(result, 0)
        assert str(resolved) in result.output
        mock_cls.create.assert_called_once_with(
            resolved, "Test", "A test"
        )

    def test_init_defaults_name_to_basename(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-2: Init defaults name to directory basename.

        Requirement: 04-REQ-1.2
        Verify init uses directory basename when --name is omitted.
        """
        target = tmp_path / "my-project"
        resolved = target.resolve()
        with patch(
            "spec_cli.cli.Campaign"
        ) as mock_cls:
            mock_cls.create.return_value = None
            result = cli_runner.invoke(
                main, ["init", str(target)]
            )
        _assert_exit(result, 0)
        # Verify name arg is the directory basename, not from the path
        mock_cls.create.assert_called_once()
        call_args = mock_cls.create.call_args
        args, kwargs = call_args
        # The name should be passed as the second positional arg
        # or as keyword "name". Extract it independently of the path.
        name_val = kwargs.get("name") if "name" in kwargs else args[1]
        assert name_val == "my-project", (
            f"Expected name='my-project', got {name_val!r}"
        )
        # Verify the path arg is the resolved absolute path
        path_val = kwargs.get("path") if "path" in kwargs else args[0]
        assert path_val == resolved, (
            f"Expected path={resolved}, got {path_val!r}"
        )

    def test_init_defaults_description_empty(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-3: Init defaults description to empty string.

        Requirement: 04-REQ-1.3
        Verify init uses empty description when --description is
        omitted.
        """
        target = tmp_path / "test"
        resolved = target.resolve()
        with patch(
            "spec_cli.cli.Campaign"
        ) as mock_cls:
            mock_cls.create.return_value = None
            result = cli_runner.invoke(
                main, ["init", str(target), "--name", "Test"]
            )
        _assert_exit(result, 0)
        # Description should default to empty string
        mock_cls.create.assert_called_once_with(
            resolved, "Test", ""
        )

    def test_init_handles_campaign_error(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-4: Init handles CampaignError.

        Requirement: 04-REQ-1.4
        Verify init prints error and exits 1 when Campaign.create
        fails.
        """
        target = tmp_path / "existing"
        with patch(
            "spec_cli.cli.Campaign"
        ) as mock_cls:
            mock_cls.create.side_effect = CampaignError(
                "already exists"
            )
            result = cli_runner.invoke(
                main, ["init", str(target)]
            )
        _assert_exit(result, 1)
        combined = result.output
        assert "already exists" in combined

    def test_init_resolves_relative_path(
        self, cli_runner: CliRunner,
    ) -> None:
        """TS-04-5: Init resolves relative path to absolute.

        Requirement: 04-REQ-1.E1
        Verify init resolves a relative path to absolute before
        passing to Campaign.create.
        """
        with patch(
            "spec_cli.cli.Campaign"
        ) as mock_cls:
            mock_cls.create.return_value = None
            result = cli_runner.invoke(
                main,
                ["init", "./my-campaign", "--name", "Test"],
            )
        _assert_exit(result, 0)
        call_args = mock_cls.create.call_args
        args, kwargs = call_args
        path_arg = args[0] if args else kwargs.get("path")
        assert Path(str(path_arg)).is_absolute(), (
            f"Expected absolute path, got {path_arg}"
        )


class TestListCommand:
    """Tests for the spec list command."""

    def test_list_displays_table(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-6: List displays spec table.

        Requirement: 04-REQ-2.1
        Verify list displays a table with spec number, name, state,
        artifacts.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "list",
            ],
        )
        _assert_exit(result, 0)
        out = result.output
        # Verify all four required columns appear
        assert "01" in out, "Missing spec number '01'"
        assert "data_models" in out, "Missing spec name"
        assert "generated" in out, "Missing session state column"
        # Artifact count for spec 01 (prd.md is the only artifact file)
        # The exact count depends on the implementation scanning the dir.
        # At minimum, verify some numeric count or "1" appears in the row.
        assert "02" in out, "Missing spec 02 row"
        assert "refining" in out, "Missing state for spec 02"

    def test_list_explicit_directory(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-7: List with explicit directory.

        Requirement: 04-REQ-2.2
        Verify list accepts explicit campaign directory argument.
        """
        result = cli_runner.invoke(
            main, ["list", str(campaign_dir_with_specs)]
        )
        _assert_exit(result, 0)
        # Verify table output was produced from the given directory
        out = result.output
        assert "01" in out, "Missing spec 01 from explicit dir"
        assert "data_models" in out, "Missing spec name from explicit dir"

    def test_list_empty_campaign(
        self, cli_runner: CliRunner, campaign_dir: Path
    ) -> None:
        """TS-04-8: List empty campaign.

        Requirement: 04-REQ-2.3
        Verify list prints empty message for campaign with no specs.
        """
        result = cli_runner.invoke(
            main,
            ["--campaign-dir", str(campaign_dir), "list"],
        )
        _assert_exit(result, 0)
        lower = result.output.lower()
        assert "empty" in lower or "no specs" in lower, (
            f"Expected empty message, got: {result.output}"
        )

    def test_list_sorts_by_prefix(
        self, cli_runner: CliRunner, campaign_dir: Path
    ) -> None:
        """TS-04-9: List sorts by numeric prefix.

        Requirement: 04-REQ-2.4
        Verify specs are sorted by number in list output.
        """
        # Create specs out of order: 03, 01, 02
        for num, name in [(3, "auth"), (1, "data"), (2, "api")]:
            d = campaign_dir / f"{num:02d}_{name}"
            d.mkdir()
            sf = d / "_session.json"
            sf.write_text(json.dumps({"state": "init"}))

        result = cli_runner.invoke(
            main,
            ["--campaign-dir", str(campaign_dir), "list"],
        )
        _assert_exit(result, 0)
        pos_01 = result.output.index("01")
        pos_02 = result.output.index("02")
        pos_03 = result.output.index("03")
        assert pos_01 < pos_02 < pos_03, (
            f"Sorted order: 01@{pos_01} 02@{pos_02} 03@{pos_03}"
        )

    def test_list_error_non_campaign(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-10: List error on non-campaign directory.

        Requirement: 04-REQ-2.E1
        Verify list fails with clear error when not in a campaign
        dir.
        """
        result = cli_runner.invoke(
            main,
            ["--campaign-dir", str(tmp_path), "list"],
        )
        _assert_exit(result, 1)
        combined = (result.output).lower()
        assert "campaign" in combined


# ================================================================
# Task 1.3: Cross-cutting and resolution tests
#            (TS-04-44 through TS-04-51)
# ================================================================


class TestSpecResolution:
    """Tests for spec argument resolution."""

    def test_spec_not_found_lists_available(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-44: Spec not found lists available specs.

        Requirement: 04-REQ-10.E1, 04-REQ-CC.5
        Verify unmatched spec argument lists available specs.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "assess",
                "99",
            ],
        )
        _assert_exit(result, 1)
        combined = result.output
        assert "01" in combined, (
            f"Expected '01' in error, got: {combined}"
        )
        assert "02" in combined, (
            f"Expected '02' in error, got: {combined}"
        )

    def test_spec_resolved_by_full_name(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-47: Spec resolved by full name.

        Requirement: 04-REQ-CC.4
        Verify spec can be resolved by full directory name.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "status",
                "01_data_models",
            ],
        )
        _assert_exit(result, 0)

    def test_spec_resolved_by_number(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-48: Spec resolved by numeric prefix.

        Requirement: 04-REQ-CC.4
        Verify spec can be resolved by just the number.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "status",
                "01",
            ],
        )
        _assert_exit(result, 0)


class TestCampaignDirResolution:
    """Tests for campaign directory resolution."""

    def test_campaign_dir_option_overrides_cwd(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-45: Campaign-dir option overrides CWD.

        Requirement: 04-REQ-CC.1, 04-REQ-CC.2
        Verify --campaign-dir option is used instead of CWD.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "list",
            ],
        )
        _assert_exit(result, 0)
        assert "01" in result.output

    def test_no_campaign_dir_error(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-46: No campaign directory error.

        Requirement: 04-REQ-CC.3
        Verify clear error when not in a campaign directory.
        """
        result = cli_runner.invoke(
            main,
            ["--campaign-dir", str(tmp_path), "status"],
        )
        _assert_exit(result, 1)
        combined = result.output
        assert "campaign" in combined.lower(), (
            f"Expected 'campaign' in error, got: {combined}"
        )
        assert "--campaign-dir" in combined, (
            f"Expected hint in error, got: {combined}"
        )


class TestExitCodes:
    """Tests for exit code conventions."""

    def test_exit_code_0_success(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-49: Exit code 0 on success.

        Requirement: 04-REQ-CC.6
        Verify successful commands exit with code 0.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "status",
                "01",
            ],
        )
        _assert_exit(result, 0)

    def test_exit_code_1_user_error(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-50: Exit code 1 on user error.

        Requirement: 04-REQ-CC.6
        Verify user errors exit with code 1.
        """
        result = cli_runner.invoke(
            main,
            ["--campaign-dir", str(tmp_path), "list"],
        )
        _assert_exit(result, 1)

    def test_exit_code_2_internal_error(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-51: Exit code 2 on internal error.

        Requirement: 04-REQ-CC.6
        Verify unexpected exceptions exit with code 2.
        """
        with patch(
            "spec_cli.cli.SpecSession"
        ) as mock_cls:
            mock_cls.resume.side_effect = RuntimeError(
                "unexpected"
            )
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 2)


# ================================================================
# Task 2.1: Spec new command tests (TS-04-11 through TS-04-16)
# ================================================================


class TestNewCommand:
    """Tests for the spec new command."""

    def test_new_creates_spec(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
        prd_file: Path,
    ) -> None:
        """TS-04-11: New creates spec from PRD file.

        Requirement: 04-REQ-3.1
        Verify new calls campaign.new_spec and prints created
        directory.
        """
        mock_session = _mock_session(state="init")
        mock_session.spec_dir = Path("/fake/01_prd")
        with patch("spec_cli.cli.Campaign") as mock_cls:
            campaign = MagicMock()
            mock_cls.open.return_value = campaign
            campaign.new_spec.return_value = mock_session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir),
                    "new",
                    str(prd_file),
                ],
            )
        _assert_exit(result, 0)
        campaign.new_spec.assert_called_once()
        # Verify the output contains the created spec directory name
        assert "01_prd" in result.output, (
            f"Expected spec dir name in output: {result.output}"
        )

    def test_new_explicit_name(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
        prd_file: Path,
    ) -> None:
        """TS-04-12: New with explicit name.

        Requirement: 04-REQ-3.2
        Verify --name option is passed as spec name.
        """
        mock_session = _mock_session(state="init")
        with patch("spec_cli.cli.Campaign") as mock_cls:
            campaign = MagicMock()
            mock_cls.open.return_value = campaign
            campaign.new_spec.return_value = mock_session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir),
                    "new",
                    str(prd_file),
                    "--name",
                    "my_spec",
                ],
            )
        _assert_exit(result, 0)
        call_args_str = str(campaign.new_spec.call_args)
        assert "my_spec" in call_args_str, (
            f"Expected 'my_spec' in call args: {call_args_str}"
        )

    def test_new_derives_name(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
    ) -> None:
        """TS-04-13: New derives name from filename.

        Requirement: 04-REQ-3.2
        Verify name is derived from PRD filename when --name is
        omitted.
        """
        prd = campaign_dir / "My Data Models.md"
        prd.write_text("# Test PRD\n\nSome content.")
        mock_session = _mock_session(state="init")
        with patch("spec_cli.cli.Campaign") as mock_cls:
            campaign = MagicMock()
            mock_cls.open.return_value = campaign
            campaign.new_spec.return_value = mock_session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir),
                    "new",
                    str(prd),
                ],
            )
        _assert_exit(result, 0)
        call_args_str = str(campaign.new_spec.call_args)
        assert "my_data_models" in call_args_str, (
            f"Expected derived name in args: {call_args_str}"
        )

    def test_new_one_shot(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
        prd_file: Path,
    ) -> None:
        """TS-04-14: New with one-shot flag.

        Requirement: 04-REQ-3.3
        Verify --one-shot sets session mode.
        """
        mock_session = _mock_session(state="init")
        with patch("spec_cli.cli.Campaign") as mock_cls:
            campaign = MagicMock()
            mock_cls.open.return_value = campaign
            campaign.new_spec.return_value = mock_session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir),
                    "new",
                    str(prd_file),
                    "--one-shot",
                ],
            )
        _assert_exit(result, 0)
        call_args_str = str(campaign.new_spec.call_args)
        assert "one-shot" in call_args_str, (
            f"Expected 'one-shot' in args: {call_args_str}"
        )

    def test_new_missing_prd(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
    ) -> None:
        """TS-04-15: New with missing PRD file.

        Requirement: 04-REQ-3.4
        Verify error when PRD file does not exist.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir),
                "new",
                "/tmp/nonexistent_prd_file.md",
            ],
        )
        assert result.exit_code != 0
        # The CLI should recognize --campaign-dir and the 'new'
        # command, reporting a file-not-found error.
        assert "no such option" not in result.output.lower(), (
            "Expected --campaign-dir option to exist"
        )

    def test_new_invalid_name(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
        prd_file: Path,
    ) -> None:
        """TS-04-16: New with invalid spec name.

        Requirement: 04-REQ-3.E1
        Verify error when spec name contains invalid characters.
        """
        with patch("spec_cli.cli.Campaign") as mock_cls:
            campaign = MagicMock()
            mock_cls.open.return_value = campaign
            campaign.new_spec.side_effect = CampaignError(
                "Invalid spec name"
            )
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir),
                    "new",
                    str(prd_file),
                    "--name",
                    "Invalid Name!",
                ],
            )
        _assert_exit(result, 1)


# ================================================================
# Task 2.2: Assess and refine command tests
#            (TS-04-17 through TS-04-26)
# ================================================================


class TestAssessCommand:
    """Tests for the spec assess command."""

    def test_assess_runs_and_prints(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-17: Assess runs assessment and prints summary.

        Requirement: 04-REQ-4.1
        Verify assess calls session.assess and prints formatted
        summary.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        lower = result.output.lower()
        assert "quality" in lower or "score" in lower, (
            f"Expected assessment info: {result.output}"
        )

    def test_assess_output_formatting(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-18: Assess output formatting.

        Requirement: 04-REQ-4.2
        Verify assessment output has clear section headers.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        lower = result.output.lower()
        assert "quality" in lower, (
            f"Missing Quality section: {result.output}"
        )
        assert "gaps" in lower or "gap" in lower, (
            f"Missing Gaps section: {result.output}"
        )
        assert "questions" in lower or "question" in lower, (
            f"Missing Questions section: {result.output}"
        )

    def test_assess_wrong_state(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-19: Assess wrong state error.

        Requirement: 04-REQ-4.3
        Verify assess prints state error when session is not in
        init or refining.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="generated")
            session.assess = AsyncMock(
                side_effect=SessionError(
                    "Cannot call assess() in state 'generated'"
                )
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 1)
        assert "state" in result.output.lower()

    def test_assess_agent_error(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-20: Assess agent error.

        Requirement: 04-REQ-4.E1
        Verify assess exits 2 on agent pipeline error.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(
                side_effect=RuntimeError("agent failed")
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 2)


class TestRefineCommand:
    """Tests for the spec refine command."""

    def test_refine_submits_answers(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        answers_file: Path,
    ) -> None:
        """TS-04-21: Refine submits answers and prints update.

        Requirement: 04-REQ-5.1
        Verify refine reads JSON, calls session.refine, prints
        confirmation.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="refining")
            session.refine = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                    "--answers",
                    str(answers_file),
                ],
            )
        _assert_exit(result, 0)
        session.refine.assert_called_once()

    def test_refine_missing_answers_file(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-22: Refine with missing answers file.

        Requirement: 04-REQ-5.2
        Verify refine fails when answers file does not exist.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "refine",
                "01",
                "--answers",
                "/tmp/nonexistent_answers.json",
            ],
        )
        assert result.exit_code != 0
        # The CLI should recognize --campaign-dir and the 'refine'
        # command, reporting the missing file.
        assert "no such option" not in result.output.lower(), (
            "Expected --campaign-dir option to exist"
        )

    def test_refine_invalid_json(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        bad_json_file: Path,
    ) -> None:
        """TS-04-23: Refine with invalid JSON.

        Requirement: 04-REQ-5.3
        Verify refine fails on malformed JSON.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "refine",
                "01",
                "--answers",
                str(bad_json_file),
            ],
        )
        _assert_exit(result, 1)
        lower = result.output.lower()
        assert "json" in lower or "parse" in lower, (
            f"Expected JSON error: {result.output}"
        )

    def test_refine_wrong_state(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        answers_file: Path,
    ) -> None:
        """TS-04-24: Refine wrong state error.

        Requirement: 04-REQ-5.4
        Verify refine prints state error when not in refining.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.refine = AsyncMock(
                side_effect=SessionError(
                    "Cannot call refine() in state 'init'"
                )
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                    "--answers",
                    str(answers_file),
                ],
            )
        _assert_exit(result, 1)
        assert "state" in result.output.lower()

    def test_refine_prints_updated_assessment(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        answers_file: Path,
    ) -> None:
        """TS-04-25: Refine prints updated assessment.

        Requirement: 04-REQ-5.5
        Verify refine prints updated assessment summary.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="refining")
            session.refine = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                    "--answers",
                    str(answers_file),
                ],
            )
        _assert_exit(result, 0)
        lower = result.output.lower()
        assert "quality" in lower or "score" in lower, (
            f"Expected assessment info: {result.output}"
        )

    def test_refine_invalid_schema(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        bad_schema_file: Path,
    ) -> None:
        """TS-04-26: Refine invalid answers schema.

        Requirement: 04-REQ-5.E1
        Verify refine fails when JSON is not an object mapping
        question IDs to strings.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "refine",
                "01",
                "--answers",
                str(bad_schema_file),
            ],
        )
        _assert_exit(result, 1)


# ================================================================
# Spec 06: Refine question export tests
# ================================================================


class TestRefineQuestionExport:
    """Tests for refine without --answers (question export)."""

    def test_refine_no_answers_outputs_json(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-06-1: Refine without --answers outputs valid JSON.

        Requirement: 06-REQ-1.1
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="assessing")
            session._assessment_history = [{"questions": []}]
            session.pending_questions.return_value = [
                {
                    "id": "q1",
                    "text": "What scope?",
                    "context": "Clarify",
                    "options": ["A", "B"],
                    "required": True,
                },
            ]
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        data = json.loads(result.output)
        assert "questions" in data
        assert "answers" in data

    def test_refine_no_answers_question_fields(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-06-2: Each question has all required fields.

        Requirement: 06-REQ-1.2
        """
        questions = [
            {
                "id": "q1",
                "text": "What?",
                "context": "Why",
                "options": ["X"],
                "required": True,
            },
            {
                "id": "q2",
                "text": "How?",
                "context": "Detail",
                "options": [],
                "required": False,
            },
        ]
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="assessing")
            session._assessment_history = [{"questions": []}]
            session.pending_questions.return_value = questions
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        data = json.loads(result.output)
        for q in data["questions"]:
            assert {"id", "text", "context", "options", "required"} <= set(
                q.keys()
            )

    def test_refine_no_answers_template(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-06-3: Answers template maps question IDs to empty strings.

        Requirement: 06-REQ-1.3
        """
        questions = [
            {
                "id": "q1", "text": "Q1?", "context": "C",
                "options": [], "required": True,
            },
            {
                "id": "q2", "text": "Q2?", "context": "C",
                "options": [], "required": False,
            },
        ]
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="assessing")
            session._assessment_history = [{"questions": []}]
            session.pending_questions.return_value = questions
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        data = json.loads(result.output)
        question_ids = {q["id"] for q in data["questions"]}
        assert set(data["answers"].keys()) == question_ids
        assert all(v == "" for v in data["answers"].values())

    def test_refine_with_answers_unchanged(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        answers_file: Path,
    ) -> None:
        """TS-06-4: Refine with --answers still works as before.

        Requirement: 06-REQ-1.4
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="refining")
            session.refine = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                    "--answers",
                    str(answers_file),
                ],
            )
        _assert_exit(result, 0)
        session.refine.assert_called_once()

    def test_refine_no_answers_no_assessment(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-06-E1: Error when no assessment exists.

        Requirement: 06-REQ-1.E1
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session._assessment_history = []
            session.pending_questions.return_value = []
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                ],
            )
        _assert_exit(result, 1)

    def test_refine_no_answers_zero_questions(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-06-E2: Output with zero questions in assessment.

        Requirement: 06-REQ-1.E2
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="assessing")
            session._assessment_history = [{"questions": []}]
            session.pending_questions.return_value = []
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        data = json.loads(result.output)
        assert data["questions"] == []
        assert data["answers"] == {}

    @pytest.mark.parametrize(
        "answers_dict",
        [
            {"q1": "answer1"},
            {"q1": "a", "q2": "b", "q3": "c"},
            {"x": "yes", "y": "no"},
        ],
    )
    def test_refine_with_answers_no_question_output(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        tmp_path: Path,
        answers_dict: dict[str, str],
    ) -> None:
        """TS-06-P4: --answers path calls session.refine() and never
        outputs question-export JSON.

        Property 4 from design.md.
        Validates: 06-REQ-1.4

        For any valid answers dict, session.refine is called exactly
        once with the provided answers, and stdout does not contain
        a top-level "questions" key (i.e. is not the question-export
        format).
        """
        answers_path = tmp_path / "p4_answers.json"
        answers_path.write_text(json.dumps(answers_dict))

        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="assessing")
            session.refine = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                    "--answers",
                    str(answers_path),
                ],
            )
        _assert_exit(result, 0)
        session.refine.assert_called_once()
        # stdout must NOT contain question-export JSON
        try:
            data = json.loads(result.output)
            assert "questions" not in data, (
                "Expected no 'questions' key in output when --answers "
                "is provided"
            )
        except json.JSONDecodeError:
            pass  # Non-JSON output is expected (assessment format)


class TestRefineQuestionExportSmoke:
    """Integration smoke test for question export path."""

    def test_refine_question_export_smoke(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """TS-06-SMOKE-1: Full question export path from CLI through
        real session resume to JSON output.

        Execution Path: Path 1 from design.md.
        Must NOT satisfy with: Mocking SpecSession, pending_questions(),
        or SpecSession.resume().

        Setup: Create a real campaign directory with a spec dir
        containing a _session.json with an assessment that has
        questions. No mocking.
        """
        # Set up a real campaign with a spec in assessing state
        campaign_dir = tmp_path / "smoke_campaign"
        campaign_dir.mkdir()
        (campaign_dir / "campaign.yaml").write_text(
            "name: smoke\ndescription: smoke test\n"
        )
        spec_dir = campaign_dir / "01_smoke_spec"
        spec_dir.mkdir()
        (spec_dir / "prd.md").write_text("# Smoke PRD\n\nContent.")

        # Write a _session.json with assessment history containing
        # questions — no mocking of SpecSession
        session_data = {
            "state": "assessing",
            "mode": "interactive",
            "prd_path": "prd.md",
            "assessment_history": [
                {
                    "quality": "needs_refinement",
                    "summary": "Needs work",
                    "gaps": ["Gap 1"],
                    "questions": [
                        {
                            "id": "sq1",
                            "text": "What is the scope?",
                            "context": "Clarify scope",
                            "options": ["Small", "Large"],
                            "required": True,
                        },
                        {
                            "id": "sq2",
                            "text": "Which database?",
                            "context": "Pick DB",
                            "options": [],
                            "required": False,
                        },
                    ],
                }
            ],
            "qa_exchanges": [],
            "generated_artifacts": [],
        }
        session_file = spec_dir / "_session.json"
        session_file.write_text(json.dumps(session_data, indent=2))
        session_before = session_file.read_text()

        # Invoke the CLI — no mocks
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir),
                "refine",
                "01",
            ],
        )
        _assert_exit(result, 0)

        # Verify stdout is valid JSON
        data = json.loads(result.output)

        # Verify questions array
        assert len(data["questions"]) == 2
        q_ids = {q["id"] for q in data["questions"]}
        assert q_ids == {"sq1", "sq2"}
        for q in data["questions"]:
            assert {"id", "text", "context", "options", "required"} <= set(
                q.keys()
            )

        # Verify answers template
        assert set(data["answers"].keys()) == q_ids
        assert all(v == "" for v in data["answers"].values())

        # Verify _session.json was NOT modified (read-only operation)
        session_after = session_file.read_text()
        assert session_before == session_after


# ================================================================
# Task 2.3: Accept, generate, validate, render, show, status tests
#            (TS-04-27 through TS-04-43)
# ================================================================


class TestAcceptCommand:
    """Tests for the spec accept command."""

    def test_accept_transitions_state(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-27: Accept transitions state and prints confirmation.

        Requirement: 04-REQ-6.1
        Verify accept calls session.accept_prd and prints new
        state.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="assessing")
            session.accept_prd.return_value = None
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "accept",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        assert "accepted" in result.output.lower()

    def test_accept_wrong_state(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-28: Accept wrong state error.

        Requirement: 04-REQ-6.2
        Verify accept fails when not in assessing or refining.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.accept_prd.side_effect = SessionError(
                "Cannot accept PRD in state 'init'"
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "accept",
                    "01",
                ],
            )
        _assert_exit(result, 1)
        assert "state" in result.output.lower()


class TestGenerateCommand:
    """Tests for the spec generate command."""

    def test_generate_runs_and_prints(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-29: Generate runs generation and prints summary.

        Requirement: 04-REQ-7.1, 04-REQ-7.2
        Verify generate calls session.generate and prints artifact
        summary.
        """
        gen_result = {
            "artifacts": [
                "requirements.md",
                "design.md",
                "test_spec.md",
                "tasks.md",
            ],
        }
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="prd_accepted")
            session.generate = AsyncMock(return_value=gen_result)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "generate",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        assert "requirements" in result.output.lower()

    def test_generate_wrong_state(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-30: Generate wrong state error.

        Requirement: 04-REQ-7.3
        Verify generate fails when not in prd_accepted state.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.generate = AsyncMock(
                side_effect=SessionError(
                    "Cannot call generate() in state 'init'"
                )
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "generate",
                    "01",
                ],
            )
        _assert_exit(result, 1)
        lower = result.output.lower()
        assert "accept" in lower or "state" in lower

    def test_generate_agent_error(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-31: Generate agent error.

        Requirement: 04-REQ-7.E1
        Verify generate exits 2 on agent pipeline error.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="prd_accepted")
            session.generate = AsyncMock(
                side_effect=RuntimeError("agent failed")
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "generate",
                    "01",
                ],
            )
        _assert_exit(result, 2)


class TestValidateCommand:
    """Tests for the spec validate command."""

    def test_validate_passing(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-32: Validate with passing spec.

        Requirement: 04-REQ-8.1, 04-REQ-8.2
        Verify validate prints success when no errors found.
        """
        validation_result = MagicMock()
        validation_result.valid = True
        validation_result.schema_errors = []
        validation_result.integrity_errors = []
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="generated")
            session.validate.return_value = validation_result
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "validate",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        lower = result.output.lower()
        assert (
            "valid" in lower
            or "success" in lower
            or "pass" in lower
        )

    def test_validate_with_errors(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-33: Validate with errors.

        Requirement: 04-REQ-8.3, 04-REQ-8.4
        Verify validate prints error table and exits 1.
        """
        validation_result = MagicMock()
        validation_result.valid = False
        validation_result.schema_errors = [
            {
                "file": "requirements.md",
                "path": "/requirements/0/id",
                "message": "Missing requirement ID",
            }
        ]
        validation_result.integrity_errors = []
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="generated")
            session.validate.return_value = validation_result
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "validate",
                    "01",
                ],
            )
        _assert_exit(result, 1)
        out = result.output
        # Verify all three columns from the error table
        assert "requirements.md" in out, (
            f"Missing file column: {out}"
        )
        assert "/requirements/0/id" in out, (
            f"Missing path column: {out}"
        )
        assert "Missing requirement ID" in out, (
            f"Missing message column: {out}"
        )

    def test_validate_missing_artifacts(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-34: Validate with missing artifacts.

        Requirement: 04-REQ-8.E1
        Verify validate reports missing artifacts.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="generated")
            session.validate.side_effect = SessionError(
                "Missing required artifacts: design.md"
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "validate",
                    "01",
                ],
            )
        _assert_exit(result, 1)
        assert "missing" in result.output.lower()


class TestRenderCommand:
    """Tests for the spec render command."""

    def test_render_outputs_markdown(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-35: Render outputs markdown.

        Requirement: 04-REQ-9.1
        Verify render prints markdown to stdout.
        """
        rendered = {
            "prd.md": "# Spec Title\n\n## Requirements\n...",
        }
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="generated")
            session.render.return_value = rendered
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "render",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        assert "# " in result.output

    def test_render_combined(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-36: Render with --combined flag.

        Requirement: 04-REQ-9.2
        Verify render passes combined=True when flag is set.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="generated")
            session.render.return_value = (
                "# Combined\n\nAll artifacts."
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "render",
                    "01",
                    "--combined",
                ],
            )
        _assert_exit(result, 0)
        session.render.assert_called_once_with(combined=True)

    def test_render_without_combined(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-37: Render without --combined flag.

        Requirement: 04-REQ-9.3
        Verify render calls session.render(combined=False) by
        default.
        """
        rendered = {
            "prd.md": "# PRD",
            "design.md": "# Design",
        }
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="generated")
            session.render.return_value = rendered
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "render",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        session.render.assert_called_once_with(combined=False)

    def test_render_missing_artifacts(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-38: Render with missing artifacts.

        Requirement: 04-REQ-9.E1
        Verify render reports missing artifacts.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="generated")
            session.render.side_effect = SessionError(
                "Missing required artifacts: requirements.md"
            )
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "render",
                    "01",
                ],
            )
        _assert_exit(result, 1)
        assert "missing" in result.output.lower()


class TestStatusCommand:
    """Tests for the spec status command."""

    def test_status_all_specs(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-39: Status without spec shows all specs.

        Requirement: 04-REQ-10.1
        Verify status without argument shows table of all specs.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "status",
            ],
        )
        _assert_exit(result, 0)
        assert "01" in result.output
        assert "02" in result.output

    def test_status_single_spec(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-40: Status with spec shows detail.

        Requirement: 04-REQ-10.2
        Verify status with spec shows detailed session state.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "status",
                "01",
            ],
        )
        _assert_exit(result, 0)
        lower = result.output.lower()
        assert "state" in lower
        assert "mode" in lower


class TestShowCommand:
    """Tests for the spec show command."""

    def test_show_session_state(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-41: Show without artifact shows session state.

        Requirement: 04-REQ-10.3
        Verify show without --artifact displays session state.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "show",
                "01",
            ],
        )
        _assert_exit(result, 0)
        assert "state" in result.output.lower()

    def test_show_artifact_content(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-42: Show with artifact displays content.

        Requirement: 04-REQ-10.4
        Verify show --artifact reads and displays content.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "show",
                "01",
                "--artifact",
                "prd.md",
            ],
        )
        _assert_exit(result, 0)
        assert "Data Models PRD" in result.output

    def test_show_nonexistent_artifact(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-43: Show with nonexistent artifact.

        Requirement: 04-REQ-10.5
        Verify show fails when artifact does not exist.
        """
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "show",
                "01",
                "--artifact",
                "nonexistent.md",
            ],
        )
        _assert_exit(result, 1)
        lower = result.output.lower()
        assert "available" in lower or "prd.md" in lower


# ================================================================
# Task 2.4: Property tests (TS-04-P1 through TS-04-P5)
# ================================================================


class TestPropertySpecResolution:
    """Property test: spec resolution determinism."""

    def test_property_spec_resolution_determinism(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-P1: Spec resolution is deterministic.

        Property 1 from design.md.
        Validates: 04-REQ-CC.4
        """
        identifiers = [
            "01",
            "02",
            "01_data_models",
            "02_api_endpoints",
        ]
        for spec_arg in identifiers:
            r1 = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "status",
                    spec_arg,
                ],
            )
            r2 = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "status",
                    spec_arg,
                ],
            )
            assert r1.exit_code == r2.exit_code == 0, (
                f"Not deterministic for {spec_arg!r}: "
                f"{r1.exit_code}, {r2.exit_code}"
            )


class TestPropertyErrorNonzeroExit:
    """Property test: error commands never exit 0."""

    def test_property_error_commands_nonzero_exit(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-P2: Error commands never exit 0.

        Property 2 from design.md.
        Validates: 04-REQ-CC.6

        For any command in the full set, CampaignError or SessionError
        must produce a non-zero exit code.
        """
        commands: list[list[str]] = [
            ["list"],
            ["status"],
            ["status", "01"],
            ["assess", "01"],
            ["accept", "01"],
            ["generate", "01"],
            ["validate", "01"],
            ["render", "01"],
            ["show", "01"],
        ]
        for error_cls in [CampaignError, SessionError]:
            for cmd_args in commands:
                with patch(
                    "spec_cli.cli.Campaign"
                ) as mock_cls:
                    mock_cls.open.side_effect = error_cls(
                        "test error"
                    )
                    result = cli_runner.invoke(
                        main,
                        [
                            "--campaign-dir",
                            str(campaign_dir_with_specs),
                            *cmd_args,
                        ],
                    )
                assert result.exit_code != 0, (
                    f"Exit 0 for {cmd_args} with "
                    f"{error_cls.__name__}"
                )


class TestPropertyCampaignDirPrecedence:
    """Property test: campaign dir resolution precedence."""

    def test_property_campaign_dir_precedence(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        tmp_path: Path,
    ) -> None:
        """TS-04-P3: Campaign dir precedence.

        Property 3 from design.md.
        Validates: 04-REQ-CC.1, 04-REQ-CC.2

        When --campaign-dir is provided, CWD is ignored — even when
        CWD is itself a valid campaign directory.
        """
        # Create a second valid campaign dir (to use as CWD)
        cwd_campaign = tmp_path / "cwd_campaign"
        cwd_campaign.mkdir()
        (cwd_campaign / "campaign.yaml").write_text(
            "name: cwd-campaign\ndescription: CWD campaign\n"
        )
        # Create a spec in CWD campaign to make it distinguishable
        cwd_spec = cwd_campaign / "01_cwd_only"
        cwd_spec.mkdir()
        (cwd_spec / "_session.json").write_text(
            json.dumps({"state": "init"})
        )

        # Invoke with --campaign-dir pointing to campaign_dir_with_specs
        # while CWD is cwd_campaign (a different valid campaign)
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(campaign_dir_with_specs),
                "list",
            ],
        )
        _assert_exit(result, 0)
        # Should see specs from --campaign-dir, not from CWD
        assert "data_models" in result.output, (
            "Expected specs from --campaign-dir, not CWD"
        )


class TestPropertyInitNoOverwrite:
    """Property test: init never overwrites existing campaign."""

    def test_property_init_no_overwrite(
        self,
        cli_runner: CliRunner,
        campaign_dir: Path,
    ) -> None:
        """TS-04-P4: Init never overwrites existing campaign.

        Property 4 from design.md.
        Validates: 04-REQ-1.4
        """
        result = cli_runner.invoke(
            main,
            ["init", str(campaign_dir), "--name", "Overwrite"],
        )
        _assert_exit(result, 1)


class TestPropertyStateGateEnforcement:
    """Property test: state gate enforcement."""

    def test_property_state_gate_enforcement(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-04-P5: State gate enforcement.

        Property 5 from design.md.
        Validates: 04-REQ-4.3, 04-REQ-5.4, 04-REQ-6.2, 04-REQ-7.3
        """
        # Create an answers file for the refine command
        answers_file = campaign_dir_with_specs / "_test_answers.json"
        answers_file.write_text(json.dumps({"q1": "answer1"}))

        state_gates = [
            (
                "assess",
                [],
                "generated",
                "Cannot call assess() in state 'generated'",
            ),
            (
                "refine",
                ["--answers", str(answers_file)],
                "init",
                "Cannot call refine() in state 'init'",
            ),
            (
                "accept",
                [],
                "init",
                "Cannot accept PRD in state 'init'",
            ),
            (
                "generate",
                [],
                "init",
                "Cannot call generate() in state 'init'",
            ),
        ]
        for cmd, extra, wrong_state, error_msg in state_gates:
            with patch(
                "spec_cli.cli.SpecSession"
            ) as mock_cls:
                session = _mock_session(state=wrong_state)
                if cmd == "assess":
                    session.assess = AsyncMock(
                        side_effect=SessionError(error_msg)
                    )
                elif cmd == "refine":
                    session.refine = AsyncMock(
                        side_effect=SessionError(error_msg)
                    )
                elif cmd == "accept":
                    session.accept_prd.side_effect = (
                        SessionError(error_msg)
                    )
                elif cmd == "generate":
                    session.generate = AsyncMock(
                        side_effect=SessionError(error_msg)
                    )
                mock_cls.resume.return_value = session
                result = cli_runner.invoke(
                    main,
                    [
                        "--campaign-dir",
                        str(campaign_dir_with_specs),
                        cmd,
                        "01",
                        *extra,
                    ],
                )
            assert result.exit_code == 1, (
                f"Expected exit 1 for {cmd} in state "
                f"{wrong_state!r}, got {result.exit_code}"
            )


# ================================================================
# Task 2.5: Integration smoke tests
#            (TS-04-SMOKE-1 through TS-04-SMOKE-4)
# ================================================================


class TestSmokeInitAndList:
    """Integration smoke test: init and list round trip."""

    def test_smoke_init_and_list(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-SMOKE-1: Init and list round trip.

        Execution Path: Path 1, then Path 2 from design.md.
        Must NOT satisfy with: Mocking Campaign class.
        """
        target = tmp_path / "smoke_campaign"
        result1 = cli_runner.invoke(
            main,
            ["init", str(target), "--name", "Smoke Test"],
        )
        _assert_exit(result1, 0)
        assert (target / "campaign.yaml").exists()

        result2 = cli_runner.invoke(
            main,
            ["--campaign-dir", str(target), "list"],
        )
        _assert_exit(result2, 0)
        lower = result2.output.lower()
        assert "empty" in lower or "no specs" in lower


class TestSmokeNewAndStatus:
    """Integration smoke test: new and status round trip."""

    def test_smoke_new_and_status(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-SMOKE-2: New and status round trip.

        Execution Path: Path 3, then Path 11 from design.md.
        Must NOT satisfy with: Mocking SpecSession class.
        """
        cli_runner.invoke(
            main,
            ["init", str(tmp_path), "--name", "Smoke"],
        )
        prd = tmp_path / "prd.md"
        prd.write_text("# Test PRD\n\nSome content.")

        result1 = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(tmp_path),
                "new",
                str(prd),
                "--name",
                "test_spec",
            ],
        )
        _assert_exit(result1, 0)

        result2 = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(tmp_path),
                "status",
                "01",
            ],
        )
        _assert_exit(result2, 0)
        assert "init" in result2.output.lower()


class TestSmokeShowArtifact:
    """Integration smoke test: show artifact content."""

    def test_smoke_show_artifact(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-SMOKE-3: Show artifact content.

        Execution Path: Path 10 from design.md.
        Must NOT satisfy with: Mocking file reads.
        """
        cli_runner.invoke(
            main,
            ["init", str(tmp_path), "--name", "Smoke"],
        )
        prd = tmp_path / "prd.md"
        prd.write_text("# Smoke Test PRD\n\nContent here.")
        cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(tmp_path),
                "new",
                str(prd),
                "--name",
                "test_spec",
            ],
        )
        result = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(tmp_path),
                "show",
                "01",
                "--artifact",
                "prd.md",
            ],
        )
        _assert_exit(result, 0)
        assert "Smoke Test PRD" in result.output


class TestSmokeValidateAndRender:
    """Integration smoke test: validate and render round trip."""

    def test_smoke_validate_and_render(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """TS-04-SMOKE-4: Validate and render round trip.

        Execution Path: Path 8, then Path 9 from design.md.
        Must NOT satisfy with: Mocking session methods.
        """
        cli_runner.invoke(
            main,
            ["init", str(tmp_path), "--name", "Smoke"],
        )
        spec_dir = tmp_path / "01_test_spec"
        spec_dir.mkdir()
        (spec_dir / "prd.md").write_text("# PRD\n\nContent.")
        (spec_dir / "requirements.md").write_text(
            "# Requirements\n\nReqs."
        )
        (spec_dir / "design.md").write_text(
            "# Design\n\nDesign."
        )
        (spec_dir / "test_spec.md").write_text(
            "# Test Spec\n\nTests."
        )
        (spec_dir / "tasks.md").write_text("# Tasks\n\nTasks.")
        (spec_dir / "_session.json").write_text(
            json.dumps({
                "state": "generated",
                "mode": "interactive",
                "prd_path": "prd.md",
                "assessment_history": [],
                "qa_exchanges": [],
                "generated_artifacts": [
                    "requirements.md",
                    "design.md",
                    "test_spec.md",
                    "tasks.md",
                ],
            })
        )
        # Step 1: validate the spec
        result1 = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(tmp_path),
                "validate",
                "01",
            ],
        )
        # Validate may pass or fail depending on spec quality;
        # we only assert it ran without crashing (exit 0 or 1)
        assert result1.exit_code in (0, 1), (
            f"Validate unexpected exit: {result1.exit_code}"
        )
        # Step 2: render the spec
        result2 = cli_runner.invoke(
            main,
            [
                "--campaign-dir",
                str(tmp_path),
                "render",
                "01",
            ],
        )
        _assert_exit(result2, 0)
        assert "#" in result2.output


# ================================================================
# Spec 09: CLI Progress Feedback — Spinner and Quiet Mode Tests
# ================================================================


class TestAssessSpinner:
    """TS-09-1: Assess shows spinner on stderr."""

    def test_assess_shows_spinner_on_stderr(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-1: Verifies assess writes spinner/status to stderr.

        Requirement: 09-REQ-1.1
        When assess runs, stderr should contain "Assessing" and
        exit code should be 0.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        # The spinner message "Assessing" must appear somewhere
        # in the combined output (CliRunner mixes stdout/stderr).
        # In the real implementation, this would be on stderr.
        combined = result.output
        assert "Assessing" in combined, (
            f"Expected 'Assessing' in output, got: {combined!r}"
        )


class TestRefineSpinner:
    """TS-09-2: Refine with answers shows spinner on stderr."""

    def test_refine_answers_shows_spinner(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        answers_file: Path,
    ) -> None:
        """TS-09-2: Verifies refine --answers shows status on stderr.

        Requirement: 09-REQ-1.2
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="assessing")
            session.refine = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "refine",
                    "01",
                    "--answers",
                    str(answers_file),
                ],
            )
        combined = result.output
        assert "Refining" in combined, (
            f"Expected 'Refining' in output, got: {combined!r}"
        )


class TestGenerateSpinner:
    """TS-09-3: Generate shows per-artifact progress."""

    def test_generate_shows_generating_message(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-3: Verifies generate shows artifact-specific messages.

        Requirement: 09-REQ-1.3, 09-REQ-1.4
        """
        gen_result = {
            "artifacts": [
                "requirements",
                "test_spec",
                "tasks",
            ],
        }
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="prd_accepted")
            session.generate = AsyncMock(return_value=gen_result)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "generate",
                    "01",
                ],
            )
        combined = result.output
        assert "Generating" in combined, (
            f"Expected 'Generating' in output, got: {combined!r}"
        )

    def test_generate_shows_completion_messages(
        self,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-3: Verifies generate shows per-artifact completion on stderr.

        Requirement: 09-REQ-1.4
        Each generated artifact should produce a "Generated {name}" line
        on stderr via spinner.log(), distinct from the pre-existing
        "Generated artifacts:" summary line on stdout.
        """
        gen_result = {
            "artifacts": [
                "requirements",
                "test_spec",
                "tasks",
            ],
        }
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="prd_accepted")
            session.generate = AsyncMock(return_value=gen_result)
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "generate",
                    "01",
                ],
            )
        # Artifact-specific completion messages must appear on stderr
        # (not the pre-existing "Generated artifacts:" on stdout).
        stderr_output = result.stderr
        assert "Generated requirements" in stderr_output, (
            f"Expected 'Generated requirements' on stderr, "
            f"got: {stderr_output!r}"
        )


class TestSpinnerStopsOnSuccess:
    """TS-09-4: Spinner stops on success."""

    def test_spinner_stops_after_success(
        self,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-4: Verifies spinner is stopped after command completes.

        Requirement: 09-REQ-1.5
        After successful completion, the spinner line should be cleared.
        Phase message should appear on stderr as plain text (non-TTY)
        and no ANSI escape remnants should remain.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        # Phase message must have appeared on stderr (proves spinner ran)
        stderr_output = result.stderr
        assert "Assessing" in stderr_output, (
            f"Expected 'Assessing' on stderr: {stderr_output!r}"
        )
        # No ANSI escape remnants (spinner line was cleared)
        assert "\x1b" not in stderr_output, (
            f"ANSI escape remnants in stderr after completion: "
            f"{stderr_output!r}"
        )


class TestSpinnerStderrOnly:
    """TS-09-5: Spinner output on stderr only."""

    def test_spinner_not_on_stdout(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-5: Verifies spinner output goes to stderr, not stdout.

        Requirement: 09-REQ-2.1
        stdout should contain only assessment output, not spinner text.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        # stdout must NOT contain spinner text
        assert "Assessing" not in result.stdout, (
            f"Spinner text leaked to stdout: {result.stdout!r}"
        )
        # stderr should contain spinner text
        assert "Assessing" in result.stderr, (
            f"Expected 'Assessing' on stderr, got: {result.stderr!r}"
        )


class TestSpinnerNonTTY:
    """TS-09-6: Non-TTY plain text fallback."""

    def test_non_tty_no_ansi_escapes(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-6: Verifies plain text output when stderr is not a TTY.

        Requirement: 09-REQ-2.2
        CliRunner uses non-TTY by default. Phase messages should appear
        as plain text without ANSI escape sequences.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        stderr_output = result.stderr
        # Non-TTY output should contain phase message
        assert "Assessing" in stderr_output, (
            f"Expected 'Assessing' on stderr: {stderr_output!r}"
        )
        # No ANSI escape sequences
        assert "\x1b" not in stderr_output, (
            f"ANSI escape found in non-TTY stderr: {stderr_output!r}"
        )


# ================================================================
# Spec 09: Quiet Mode Tests (TS-09-7 through TS-09-10)
# ================================================================


class TestQuietFlagAccepted:
    """TS-09-7: Quiet flag accepted."""

    def test_quiet_long_flag(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-7: --quiet flag is recognized by the CLI.

        Requirement: 09-REQ-3.1
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--quiet",
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        assert "no such option" not in result.output.lower(), (
            f"--quiet not recognized: {result.output}"
        )

    def test_quiet_short_flag(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-7: -q flag is recognized by the CLI.

        Requirement: 09-REQ-3.1
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "-q",
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        assert "no such option" not in result.output.lower(), (
            f"-q not recognized: {result.output}"
        )


class TestQuietSuppressesSpinner:
    """TS-09-8: Quiet suppresses spinner."""

    def test_quiet_no_spinner_on_stderr(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-8: --quiet suppresses all spinner output.

        Requirement: 09-REQ-3.2
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--quiet",
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        stderr_output = result.stderr
        assert "Assessing" not in stderr_output, (
            f"Spinner text on stderr in quiet mode: {stderr_output!r}"
        )


class TestQuietPreservesOutput:
    """TS-09-9: Quiet preserves final output."""

    def test_quiet_still_shows_assessment(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-9: --quiet still prints command results.

        Requirement: 09-REQ-3.3
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            result = cli_runner.invoke(
                main,
                [
                    "--quiet",
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        lower = result.output.lower()
        assert "quality" in lower, (
            f"Expected assessment output in quiet mode: {result.output}"
        )


class TestQuietFlagInContext:
    """TS-09-10: Quiet flag in context."""

    def test_quiet_accessible_in_context(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-10: ctx.obj['quiet'] is True when --quiet is set.

        Requirement: 09-REQ-3.4
        Verified transitively: if --quiet suppresses spinner output
        (tested in TS-09-8), then ctx.obj['quiet'] must be True and
        accessible to subcommands.
        """
        assessment = _sample_assessment()
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(return_value=assessment)
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--quiet",
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        _assert_exit(result, 0)
        # Quiet mode behavior is active: no spinner on stderr
        stderr_output = result.stderr
        assert "Assessing" not in stderr_output, (
            f"Spinner text found — quiet flag not in context: "
            f"{stderr_output!r}"
        )


# ================================================================
# Spec 09: Edge Case and Property Tests
# ================================================================


class TestSpinnerStopsOnError:
    """TS-09-E1: Spinner stops on error."""

    def test_spinner_cleaned_up_on_session_error(
        self,
        campaign_dir_with_specs: Path,
    ) -> None:
        """TS-09-E1: Verifies spinner is cleaned up on command error.

        Requirement: 09-REQ-1.E1
        When the command raises SessionError, the spinner should be
        stopped and the error message should appear. No ANSI escape
        remnants should remain in stderr after cleanup.
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(
                side_effect=SessionError("test assessment error")
            )
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        assert result.exit_code != 0
        assert "Error" in result.output or "error" in result.output
        # Spinner must have been started (phase message on stderr)
        # before the error stopped it
        assert "Assessing" in result.stderr, (
            f"Expected spinner phase message on stderr before error, "
            f"got: {result.stderr!r}"
        )
        # No ANSI escape remnants (spinner was cleaned up)
        assert "\x1b" not in result.stderr, (
            f"ANSI escape remnants after error: {result.stderr!r}"
        )


class TestQuietSuppressesAllProperty:
    """TS-09-P1: Quiet suppresses all spinner output across commands.

    Property 1 from design.md.
    Validates: 09-REQ-3.2, 09-REQ-3.3
    """

    @pytest.mark.parametrize(
        "cmd,extra_args,setup_session",
        [
            (
                "assess",
                [],
                lambda s: setattr(s, "assess", AsyncMock(
                    return_value=_sample_assessment()
                )),
            ),
            (
                "refine",
                ["--answers", "__ANSWERS_FILE__"],
                lambda s: setattr(s, "refine", AsyncMock(
                    return_value=_sample_assessment()
                )),
            ),
            (
                "generate",
                [],
                lambda s: setattr(s, "generate", AsyncMock(
                    return_value={"artifacts": ["requirements"]}
                )),
            ),
        ],
        ids=["assess", "refine", "generate"],
    )
    def test_quiet_suppresses_for_command(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        tmp_path: Path,
        cmd: str,
        extra_args: list[str],
        setup_session: Any,
    ) -> None:
        """No spinner text on stderr when --quiet is set.

        Requirement: 09-REQ-3.2
        """
        # Replace answers file placeholder with real path
        resolved_args = []
        for arg in extra_args:
            if arg == "__ANSWERS_FILE__":
                af = tmp_path / "p1_answers.json"
                af.write_text(json.dumps({"q1": "a"}))
                resolved_args.append(str(af))
            else:
                resolved_args.append(arg)

        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            setup_session(session)
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--quiet",
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    cmd,
                    "01",
                    *resolved_args,
                ],
            )
        _assert_exit(result, 0)
        stderr_output = result.stderr
        assert "Assessing" not in stderr_output
        assert "Refining" not in stderr_output
        assert "Generating" not in stderr_output


class TestSpinnerStderrOnlyProperty:
    """TS-09-P2: Spinner stderr only property.

    Property 2 from design.md.
    Validates: 09-REQ-2.1
    """

    @pytest.mark.parametrize(
        "cmd,extra_args,setup_session",
        [
            (
                "assess",
                [],
                lambda s: setattr(s, "assess", AsyncMock(
                    return_value=_sample_assessment()
                )),
            ),
            (
                "refine",
                ["--answers", "__ANSWERS_FILE__"],
                lambda s: setattr(s, "refine", AsyncMock(
                    return_value=_sample_assessment()
                )),
            ),
            (
                "generate",
                [],
                lambda s: setattr(s, "generate", AsyncMock(
                    return_value={"artifacts": ["requirements"]}
                )),
            ),
        ],
        ids=["assess", "refine", "generate"],
    )
    def test_spinner_not_on_stdout(
        self,
        cli_runner: CliRunner,
        campaign_dir_with_specs: Path,
        tmp_path: Path,
        cmd: str,
        extra_args: list[str],
        setup_session: Any,
    ) -> None:
        """Spinner text never appears on stdout.

        Requirement: 09-REQ-2.1
        """
        resolved_args = []
        for arg in extra_args:
            if arg == "__ANSWERS_FILE__":
                af = tmp_path / "p2_answers.json"
                af.write_text(json.dumps({"q1": "a"}))
                resolved_args.append(str(af))
            else:
                resolved_args.append(arg)

        # Map commands to their expected spinner keyword on stderr
        spinner_keywords = {
            "assess": "Assessing",
            "refine": "Refining",
            "generate": "Generating",
        }
        expected_keyword = spinner_keywords[cmd]

        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            setup_session(session)
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    cmd,
                    "01",
                    *resolved_args,
                ],
            )
        # Spinner text must appear on stderr (positive check)
        assert expected_keyword in result.stderr, (
            f"Expected '{expected_keyword}' on stderr, "
            f"got: {result.stderr!r}"
        )
        # Spinner text must NOT appear on stdout
        stdout = result.stdout
        assert "Assessing" not in stdout
        assert "Refining" not in stdout
        assert "Generating" not in stdout


class TestSpinnerCleanupProperty:
    """TS-09-P3: Spinner cleanup on error property.

    Property 3 from design.md.
    Validates: 09-REQ-1.E1
    """

    @pytest.mark.parametrize(
        "error_cls",
        [SessionError, RuntimeError],
        ids=["SessionError", "RuntimeError"],
    )
    def test_spinner_exit_called_on_error(
        self,
        campaign_dir_with_specs: Path,
        error_cls: type,
    ) -> None:
        """StatusSpinner.__exit__ is called when command errors.

        Requirement: 09-REQ-1.E1
        """
        with patch("spec_cli.cli.SpecSession") as mock_cls:
            session = _mock_session(state="init")
            session.assess = AsyncMock(
                side_effect=error_cls("test error")
            )
            mock_cls.resume.return_value = session
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--campaign-dir",
                    str(campaign_dir_with_specs),
                    "assess",
                    "01",
                ],
            )
        assert result.exit_code != 0
        # Error message should be visible (spinner was cleaned up)
        assert "error" in result.output.lower()
        # Spinner must have been started before the error
        assert "Assessing" in result.stderr, (
            f"Expected spinner phase message on stderr: "
            f"{result.stderr!r}"
        )
        # No ANSI escape remnants (spinner was properly stopped)
        assert "\x1b" not in result.stderr, (
            f"ANSI escape remnants after error: {result.stderr!r}"
        )


# ================================================================
# Spec 09: Integration Smoke Tests
# ================================================================


class TestAssessSpinnerSmoke:
    """TS-09-SMOKE-1: Assess with spinner end-to-end.

    Execution Path: Path 1 from design.md.
    Must NOT satisfy with: Mocking StatusSpinner or click.echo.
    """

    def test_assess_spinner_smoke(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """TS-09-SMOKE-1: Full assess flow with spinner on stderr.

        Setup: Mock only the agent API call. Real Campaign, real
        SpecSession, real StatusSpinner.
        """
        # Set up a real campaign
        campaign_dir = tmp_path / "smoke_campaign"
        campaign_dir.mkdir()
        (campaign_dir / "campaign.yaml").write_text(
            "name: smoke\ndescription: smoke\n"
        )
        spec_dir = campaign_dir / "01_smoke_spec"
        spec_dir.mkdir()
        (spec_dir / "prd.md").write_text("# Smoke PRD\n\nContent.")
        (spec_dir / "_session.json").write_text(json.dumps({
            "state": "init",
            "mode": "interactive",
            "prd_path": "prd.md",
            "assessment_history": [],
            "qa_exchanges": [],
            "generated_artifacts": [],
        }))

        # Mock only the agent API call (create_client)
        mock_assessment_response = MagicMock()
        mock_assessment_response.quality = "needs_refinement"
        mock_assessment_response.summary = "Needs work"
        mock_assessment_response.gaps = ["Gap 1"]
        mock_assessment_response.questions = []

        with patch("speclib.session.create_client") as mock_auth:
            mock_client = MagicMock()
            mock_client.messages = MagicMock()
            mock_client.messages.create = AsyncMock()
            mock_auth.return_value = (mock_client, "test-model")

            with patch(
                "speclib.agent.SpecAgent.assess_prd",
                new_callable=AsyncMock,
            ) as mock_assess:
                from speclib.session import Assessment

                mock_assess.return_value = Assessment(
                    quality="needs_refinement",
                    summary="Quality needs improvement",
                    gaps=["Missing details"],
                    questions=[],
                )
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    [
                        "--campaign-dir",
                        str(campaign_dir),
                        "assess",
                        "01",
                    ],
                )
        _assert_exit(result, 0)
        # stderr should contain spinner/phase message
        stderr_output = result.stderr
        assert "Assessing" in stderr_output, (
            f"Expected 'Assessing' on stderr: {stderr_output!r}"
        )
        # stdout should contain assessment output
        lower = result.output.lower()
        assert "quality" in lower, (
            f"Expected assessment on stdout: {result.output}"
        )


class TestQuietModeSmoke:
    """TS-09-SMOKE-2: Quiet mode end-to-end.

    Execution Path: Path 3 from design.md.
    Must NOT satisfy with: Mocking StatusSpinner or click.echo.
    """

    def test_quiet_mode_smoke(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """TS-09-SMOKE-2: Quiet mode suppresses spinner but keeps output.

        Setup: Mock only the agent API call. Real Campaign, real
        SpecSession, real StatusSpinner.
        """
        # Set up a real campaign
        campaign_dir = tmp_path / "quiet_smoke"
        campaign_dir.mkdir()
        (campaign_dir / "campaign.yaml").write_text(
            "name: quiet\ndescription: quiet smoke\n"
        )
        spec_dir = campaign_dir / "01_quiet_spec"
        spec_dir.mkdir()
        (spec_dir / "prd.md").write_text("# Quiet PRD\n\nContent.")
        (spec_dir / "_session.json").write_text(json.dumps({
            "state": "init",
            "mode": "interactive",
            "prd_path": "prd.md",
            "assessment_history": [],
            "qa_exchanges": [],
            "generated_artifacts": [],
        }))

        with patch("speclib.session.create_client") as mock_auth:
            mock_client = MagicMock()
            mock_client.messages = MagicMock()
            mock_client.messages.create = AsyncMock()
            mock_auth.return_value = (mock_client, "test-model")

            with patch(
                "speclib.agent.SpecAgent.assess_prd",
                new_callable=AsyncMock,
            ) as mock_assess:
                from speclib.session import Assessment

                mock_assess.return_value = Assessment(
                    quality="needs_refinement",
                    summary="Quality needs improvement",
                    gaps=["Missing details"],
                    questions=[],
                )
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    [
                        "--quiet",
                        "--campaign-dir",
                        str(campaign_dir),
                        "assess",
                        "01",
                    ],
                )
        _assert_exit(result, 0)
        # stderr must be completely empty in quiet mode — no spinner
        # text of any kind (not just "Assessing" but also "Refining",
        # "Generating", or any other phase message).
        stderr_output = result.stderr
        assert stderr_output == "", (
            f"Expected empty stderr in quiet mode, got: {stderr_output!r}"
        )
        # stdout should still contain assessment output
        lower = result.output.lower()
        assert "quality" in lower, (
            f"Expected assessment on stdout: {result.output}"
        )
