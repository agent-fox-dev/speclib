"""CLI equivalence and help text tests.

Verifies that the spec CLI produces correct help output and has
functional equivalence with the previous af-spec CLI.

Test Spec Entries: TS-10-P3, TS-10-E2
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# TS-10-E2: CLI Help Shows "spec"
# Requirement: 10-REQ-2.E1
# ---------------------------------------------------------------------------


def test_ts10_e2_help_shows_spec_name() -> None:
    """TS-10-E2: CLI help text uses 'spec' as program name, not 'af-spec'."""
    try:
        from spec_cli.cli import main
    except ImportError:
        pytest.fail("spec_cli.cli is not importable")

    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0, (
        f"spec --help failed with exit code {result.exit_code}"
    )
    assert "af-spec" not in result.output, (
        "Help text should not contain 'af-spec'"
    )


# ---------------------------------------------------------------------------
# TS-10-P3: CLI Functional Equivalence
# Property 3 from design.md
# Validates: 10-REQ-6.5, 10-REQ-2.4
# ---------------------------------------------------------------------------

_ALL_SUBCOMMANDS = [
    "init",
    "list",
    "new",
    "assess",
    "refine",
    "accept",
    "generate",
    "validate",
    "render",
    "show",
    "status",
    "install-skill",
]


@pytest.mark.parametrize("subcommand", _ALL_SUBCOMMANDS)
def test_ts10_p3_subcommand_help(subcommand: str) -> None:
    """TS-10-P3: Each subcommand produces valid help text."""
    try:
        from spec_cli.cli import main
    except ImportError:
        pytest.fail("spec_cli.cli is not importable")

    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(main, [subcommand, "--help"])

    assert result.exit_code == 0, (
        f"spec {subcommand} --help failed with exit code {result.exit_code}:\n"
        f"{result.output}"
    )
    # Verify the help text actually contains meaningful content:
    # either the program name 'spec' or the subcommand name itself
    assert "spec" in result.output or subcommand in result.output, (
        f"Help text for '{subcommand}' is missing expected content.\n"
        f"Expected 'spec' or '{subcommand}' in output:\n{result.output}"
    )
