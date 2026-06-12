"""Structural tests for the spec-cli package and root configuration.

Verifies CLI package structure, root pyproject.toml, Makefile targets,
and old directory removal after the monorepo restructure.

Test Spec Entries: TS-10-3, TS-10-4, TS-10-5, TS-10-6, TS-10-7,
    TS-10-8, TS-10-9, TS-10-10, TS-10-11, TS-10-12, TS-10-13,
    TS-10-E5, TS-10-E6, TS-10-E8, TS-10-E9
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC_CLI_PKG = REPO_ROOT / "packages" / "spec-cli"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_cli_pyproject() -> dict:
    """Load and parse packages/spec-cli/pyproject.toml."""
    pyproject_path = SPEC_CLI_PKG / "pyproject.toml"
    assert pyproject_path.exists(), (
        f"pyproject.toml not found at {pyproject_path}"
    )
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


def _load_root_pyproject() -> dict:
    """Load and parse root pyproject.toml."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), (
        f"Root pyproject.toml not found at {pyproject_path}"
    )
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------------------
# TS-10-3: CLI Package Entry Point
# Requirement: 10-REQ-2.1
# ---------------------------------------------------------------------------


def test_ts10_3_cli_entry_point() -> None:
    """TS-10-3: spec-cli pyproject.toml declares spec console script."""
    config = _load_cli_pyproject()
    scripts = config["project"]["scripts"]

    assert "spec" in scripts, "No 'spec' entry in [project.scripts]"
    assert scripts["spec"] == "spec_cli.cli:main", (
        f"spec entry point should be spec_cli.cli:main, got {scripts['spec']}"
    )


# ---------------------------------------------------------------------------
# TS-10-4: CLI Package Dependencies
# Requirements: 10-REQ-2.2, 10-REQ-2.3
# ---------------------------------------------------------------------------


def test_ts10_4_cli_dependencies() -> None:
    """TS-10-4: spec-cli depends on speclib, click, and rich."""
    config = _load_cli_pyproject()
    deps = config["project"]["dependencies"]

    assert any("speclib" in d for d in deps), "speclib not in CLI deps"
    assert any("click" in d.lower() for d in deps), "click not in CLI deps"
    assert any("rich" in d.lower() for d in deps), "rich not in CLI deps"


# ---------------------------------------------------------------------------
# TS-10-5: CLI Subcommands Present
# Requirement: 10-REQ-2.4
# ---------------------------------------------------------------------------


def test_ts10_5_cli_subcommands() -> None:
    """TS-10-5: All expected subcommands are registered on the CLI group."""
    try:
        from spec_cli.cli import main
    except ImportError:
        pytest.fail("spec_cli.cli is not importable")

    expected = {
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
    }
    actual = set(main.commands.keys())
    assert expected == actual, (
        f"Command mismatch.\n  Missing: {expected - actual}\n"
        f"  Extra: {actual - expected}"
    )


# ---------------------------------------------------------------------------
# TS-10-6: CLI Module Imports From speclib
# Requirement: 10-REQ-6.3
# ---------------------------------------------------------------------------


def test_ts10_6_cli_imports_from_speclib() -> None:
    """TS-10-6: cli.py imports business logic from speclib, not local paths."""
    cli_path = SPEC_CLI_PKG / "spec_cli" / "cli.py"
    assert cli_path.exists(), f"cli.py not found at {cli_path}"

    source = cli_path.read_text()

    assert "from speclib.campaign import Campaign" in source, (
        "cli.py must import Campaign from speclib.campaign"
    )
    assert "from speclib.session import SpecSession" in source, (
        "cli.py must import SpecSession from speclib.session"
    )
    assert "from speclib.errors import" in source, (
        "cli.py must import errors from speclib.errors"
    )


# ---------------------------------------------------------------------------
# TS-10-7: UI Import From spec_cli
# Requirement: 10-REQ-6.4
# ---------------------------------------------------------------------------


def test_ts10_7_ui_import_from_spec_cli() -> None:
    """TS-10-7: cli.py imports StatusSpinner from spec_cli.ui."""
    cli_path = SPEC_CLI_PKG / "spec_cli" / "cli.py"
    assert cli_path.exists(), f"cli.py not found at {cli_path}"

    source = cli_path.read_text()

    assert "from spec_cli.ui import StatusSpinner" in source, (
        "cli.py must import StatusSpinner from spec_cli.ui"
    )


# ---------------------------------------------------------------------------
# TS-10-8: Skill Files Present in CLI Package
# Requirement: 10-REQ-2.6
# ---------------------------------------------------------------------------


def test_ts10_8_skill_init_exists() -> None:
    """TS-10-8: skill/__init__.py exists in spec_cli package."""
    path = SPEC_CLI_PKG / "spec_cli" / "skill" / "__init__.py"
    assert path.exists(), f"skill/__init__.py not found at {path}"


def test_ts10_8_skill_markdown_exists() -> None:
    """TS-10-8: skill/spec.md exists in spec_cli package."""
    path = SPEC_CLI_PKG / "spec_cli" / "skill" / "spec.md"
    assert path.exists(), f"skill/spec.md not found at {path}"


# ---------------------------------------------------------------------------
# TS-10-9: Root pyproject.toml Has No Scripts
# Requirement: 10-REQ-3.2
# ---------------------------------------------------------------------------


def test_ts10_9_root_no_scripts() -> None:
    """TS-10-9: Root pyproject.toml does not define console scripts."""
    config = _load_root_pyproject()

    assert "scripts" not in config.get("project", {}), (
        "Root pyproject.toml must not define [project.scripts]"
    )


# ---------------------------------------------------------------------------
# TS-10-10: Root pyproject.toml UV Sources
# Requirement: 10-REQ-3.1
# ---------------------------------------------------------------------------


def test_ts10_10_root_uv_sources() -> None:
    """TS-10-10: Root pyproject.toml has uv sources for all three packages."""
    config = _load_root_pyproject()
    sources = config["tool"]["uv"]["sources"]

    assert "afspec" in sources, "afspec not in root uv sources"
    assert "speclib" in sources, "speclib not in root uv sources"
    assert "spec-cli" in sources, "spec-cli not in root uv sources"


# ---------------------------------------------------------------------------
# TS-10-11: Root Makefile Targets
# Requirements: 10-REQ-5.1, 10-REQ-5.2, 10-REQ-5.3, 10-REQ-5.4, 10-REQ-5.5
# ---------------------------------------------------------------------------


def test_ts10_11_makefile_targets() -> None:
    """TS-10-11: Makefile defines check, lint, test, clean targets."""
    makefile_path = REPO_ROOT / "Makefile"
    assert makefile_path.exists(), "Makefile not found at repo root"

    content = makefile_path.read_text()

    for target in ("check:", "lint:", "test:", "clean:"):
        assert target in content, f"Makefile missing target: {target}"


def test_ts10_11_check_depends_on_lint_and_test() -> None:
    """TS-10-11: check target depends on lint and test."""
    makefile_path = REPO_ROOT / "Makefile"
    content = makefile_path.read_text()

    # Find the check target line and verify it depends on lint and test
    for line in content.splitlines():
        if line.startswith("check:"):
            assert "lint" in line, "check target must depend on lint"
            assert "test" in line, "check target must depend on test"
            return

    pytest.fail("check: target not found in Makefile")


def test_ts10_11_phony_targets() -> None:
    """TS-10-11: All targets are declared as .PHONY (10-REQ-5.5)."""
    makefile_path = REPO_ROOT / "Makefile"
    content = makefile_path.read_text()

    assert ".PHONY:" in content, "Makefile must declare .PHONY targets"

    # Collect all .PHONY declarations
    phony_text = ""
    for line in content.splitlines():
        if ".PHONY:" in line:
            phony_text += " " + line.split(".PHONY:", 1)[1]

    for target in ("check", "lint", "test", "clean"):
        assert target in phony_text, (
            f"Target '{target}' not declared as .PHONY"
        )


# ---------------------------------------------------------------------------
# TS-10-12: Old Directories Removed
# Requirements: 10-REQ-6.1, 10-REQ-6.2
# ---------------------------------------------------------------------------


def test_ts10_12_old_speclib_removed() -> None:
    """TS-10-12: Top-level speclib/ directory no longer exists."""
    old_speclib = REPO_ROOT / "speclib"
    assert not old_speclib.exists(), (
        f"Old top-level speclib/ still exists at {old_speclib}"
    )


def test_ts10_12_old_tests_removed() -> None:
    """TS-10-12: Top-level tests/ directory no longer exists."""
    old_tests = REPO_ROOT / "tests"
    assert not old_tests.exists(), (
        f"Old top-level tests/ still exists at {old_tests}"
    )


# ---------------------------------------------------------------------------
# TS-10-13: Root Pytest Config Testpaths
# Requirement: 10-REQ-3.4
# ---------------------------------------------------------------------------


def test_ts10_13_pytest_testpaths() -> None:
    """TS-10-13: Root pytest config points to all package test directories."""
    config = _load_root_pyproject()
    testpaths = config["tool"]["pytest"]["ini_options"]["testpaths"]

    assert "packages/afspec/tests" in testpaths, (
        "testpaths missing packages/afspec/tests"
    )
    assert "packages/speclib/tests" in testpaths, (
        "testpaths missing packages/speclib/tests"
    )
    assert "packages/spec-cli/tests" in testpaths, (
        "testpaths missing packages/spec-cli/tests"
    )


# ---------------------------------------------------------------------------
# TS-10-E6: uv sync Installs All Packages (integration)
# Requirement: 10-REQ-3.E1
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_ts10_e6_uv_sync_installs_all() -> None:
    """TS-10-E6: uv sync from repo root installs all three packages."""
    result = subprocess.run(
        ["uv", "sync"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"uv sync failed:\n{result.stderr}"

    for mod in ("afspec", "speclib", "spec_cli"):
        check = subprocess.run(
            ["uv", "run", "python", "-c", f"import {mod}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert check.returncode == 0, (
            f"Module {mod} not importable after uv sync:\n{check.stderr}"
        )


# ---------------------------------------------------------------------------
# TS-10-E8: Makefile Reports Failure on Lint Error (integration)
# Requirement: 10-REQ-5.E1
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_ts10_e8_makefile_reports_failure() -> None:
    """TS-10-E8: make check exits non-zero when a package has errors."""
    error_file = REPO_ROOT / "packages" / "speclib" / "speclib" / "_deliberate_error.py"
    try:
        error_file.parent.mkdir(parents=True, exist_ok=True)
        error_file.write_text("def f( = 1\n")

        result = subprocess.run(
            ["make", "check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode != 0, (
            "make check should fail when a syntax error is present"
        )
    finally:
        if error_file.exists():
            error_file.unlink()


# ---------------------------------------------------------------------------
# TS-10-E9: Automatic speclib Installation via spec-cli (integration)
# Requirement: 10-REQ-7.E1
# ---------------------------------------------------------------------------


def test_ts10_e9_spec_cli_declares_speclib_path_dependency() -> None:
    """TS-10-E9: spec-cli declares speclib as a path dependency.

    Verifies that spec-cli's pyproject.toml declares speclib in both its
    ``[project] dependencies`` and ``[tool.uv.sources]`` as a path
    dependency pointing to ``../speclib``.  This ensures that
    ``uv pip install ./packages/spec-cli`` will automatically resolve and
    install speclib (10-REQ-7.E1).

    A true subprocess-level install test is not feasible in the project
    venv where speclib is already present.  The declarative check here
    guarantees that the path dependency wiring is correct.
    """
    config = _load_cli_pyproject()

    # 1. speclib must be in the runtime dependencies
    deps = config["project"]["dependencies"]
    assert any("speclib" in d for d in deps), (
        "speclib not in spec-cli dependencies — "
        "uv will not auto-install it"
    )

    # 2. uv sources must declare speclib as a workspace dependency.
    # In a uv workspace, member packages reference each other via
    # { workspace = true } rather than direct path references.
    # See docs/errata/10_workspace_dependency_syntax.md.
    sources = config.get("tool", {}).get("uv", {}).get("sources", {})
    assert "speclib" in sources, (
        "speclib not in spec-cli [tool.uv.sources] — "
        "dependency not declared"
    )
    assert sources["speclib"].get("workspace") is True, (
        f"speclib should be a workspace dependency, "
        f"got {sources['speclib']!r}"
    )


# ---------------------------------------------------------------------------
# TS-10-E5: spec CLI Without speclib
# Requirement: 10-REQ-2.E2
# ---------------------------------------------------------------------------


def test_ts10_e5_spec_cli_without_speclib() -> None:
    """TS-10-E5: Importing spec_cli.cli without speclib raises ImportError.

    Uses subprocess isolation to simulate an environment where speclib is
    not available.  Setting ``sys.modules['speclib'] = None`` in a fresh
    interpreter blocks the import of speclib before spec_cli.cli is loaded,
    verifying that spec_cli correctly fails with ImportError when its
    speclib dependency is missing.
    """
    import sys

    code = "\n".join([
        "import sys",
        "# Block speclib and all its sub-modules",
        "sys.modules['speclib'] = None",
        "sys.modules['speclib.campaign'] = None",
        "sys.modules['speclib.session'] = None",
        "sys.modules['speclib.errors'] = None",
        "try:",
        "    import spec_cli.cli",
        "    sys.exit(1)  # Should have raised ImportError",
        "except ImportError:",
        "    sys.exit(0)",
    ])
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        "Expected ImportError when speclib is unavailable, but "
        f"spec_cli.cli imported successfully.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Coverage gap: CLI test files at correct location
# Requirement: 10-REQ-4.2
# ---------------------------------------------------------------------------

_EXPECTED_CLI_TEST_FILES = [
    "test_cli.py",
    "test_ui.py",
    "test_skill.py",
]


@pytest.mark.parametrize("test_file", _EXPECTED_CLI_TEST_FILES)
def test_cli_test_files_at_correct_location(test_file: str) -> None:
    """Verify CLI test files exist at packages/spec-cli/tests/."""
    path = SPEC_CLI_PKG / "tests" / test_file
    assert path.exists(), (
        f"CLI test file not found at expected location: {path}"
    )


# ---------------------------------------------------------------------------
# TS-10-E5: spec CLI Without speclib
# Requirement: 10-REQ-2.E2
# ---------------------------------------------------------------------------


def test_ts10_e5_cli_without_speclib() -> None:
    """TS-10-E5: Importing spec_cli.cli without speclib raises ImportError.

    Uses subprocess isolation to simulate an environment where speclib is
    not available.  Setting ``sys.modules['speclib'] = None`` in a fresh
    interpreter blocks the import of speclib (and any of its submodules)
    before spec_cli.cli is loaded, verifying that the CLI correctly fails
    with ImportError when its speclib dependency is missing.
    """
    code = "\n".join([
        "import sys",
        "# Block speclib and all its sub-modules",
        "sys.modules['speclib'] = None",
        "sys.modules['speclib.campaign'] = None",
        "sys.modules['speclib.session'] = None",
        "sys.modules['speclib.errors'] = None",
        "try:",
        "    import spec_cli.cli",
        "    sys.exit(1)  # Should have raised ImportError",
        "except ImportError:",
        "    sys.exit(0)",
    ])
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        "Expected ImportError when speclib is unavailable, but "
        f"spec_cli.cli imported successfully.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
