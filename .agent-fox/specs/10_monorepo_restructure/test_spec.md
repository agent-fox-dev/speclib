# Test Specification: Monorepo Restructure

## Overview

This test specification verifies the structural correctness of the
monorepo restructure. Tests fall into three categories: structural tests
(file/directory existence and content), import tests (dependency
isolation), and functional tests (CLI equivalence). Since this is a
restructure rather than a feature addition, most tests verify that
nothing was broken during the move.

## Test Cases

### TS-10-1: Library Package Directory Structure

**Requirement:** 10-REQ-1.3
**Type:** unit
**Description:** Verify that all required library modules exist at their
new locations under `packages/speclib/speclib/`.

**Preconditions:**
- Restructure has been applied to the repository.

**Input:**
- List of expected modules: `__init__.py`, `agent.py`, `auth.py`,
  `campaign.py`, `config.py`, `errors.py`, `prompts.py`, `session.py`,
  `tools.py`.

**Expected:**
- Each file exists at `packages/speclib/speclib/<module>`.

**Assertion pseudocode:**
```
FOR EACH module IN expected_modules:
    path = repo_root / "packages/speclib/speclib" / module
    ASSERT path.exists()
```

### TS-10-2: Library pyproject.toml Dependencies

**Requirement:** 10-REQ-1.2
**Type:** unit
**Description:** Verify that the speclib pyproject.toml declares only
library dependencies and does not include click or rich.

**Preconditions:**
- `packages/speclib/pyproject.toml` exists.

**Input:**
- Parse `packages/speclib/pyproject.toml`.

**Expected:**
- `dependencies` list includes `afspec`, `anthropic`, `pyyaml`.
- `dependencies` list does not include `click` or `rich`.

**Assertion pseudocode:**
```
config = parse_toml("packages/speclib/pyproject.toml")
deps = config["project"]["dependencies"]
ASSERT any("afspec" in d for d in deps)
ASSERT any("anthropic" in d for d in deps)
ASSERT any("pyyaml" in d.lower() for d in deps)
ASSERT NOT any("click" in d.lower() for d in deps)
ASSERT NOT any("rich" in d.lower() for d in deps)
```

### TS-10-3: CLI Package Entry Point

**Requirement:** 10-REQ-2.1
**Type:** unit
**Description:** Verify that the spec-cli pyproject.toml declares the
`spec` console script pointing to `spec_cli.cli:main`.

**Preconditions:**
- `packages/spec-cli/pyproject.toml` exists.

**Input:**
- Parse `packages/spec-cli/pyproject.toml`.

**Expected:**
- `[project.scripts]` contains `spec = "spec_cli.cli:main"`.

**Assertion pseudocode:**
```
config = parse_toml("packages/spec-cli/pyproject.toml")
scripts = config["project"]["scripts"]
ASSERT scripts["spec"] == "spec_cli.cli:main"
```

### TS-10-4: CLI Package Dependencies

**Requirement:** 10-REQ-2.2, 10-REQ-2.3
**Type:** unit
**Description:** Verify that the spec-cli pyproject.toml depends on
speclib, click, and rich.

**Preconditions:**
- `packages/spec-cli/pyproject.toml` exists.

**Input:**
- Parse `packages/spec-cli/pyproject.toml`.

**Expected:**
- `dependencies` includes `speclib`, `click`, and `rich`.

**Assertion pseudocode:**
```
config = parse_toml("packages/spec-cli/pyproject.toml")
deps = config["project"]["dependencies"]
ASSERT any("speclib" in d for d in deps)
ASSERT any("click" in d.lower() for d in deps)
ASSERT any("rich" in d.lower() for d in deps)
```

### TS-10-5: CLI Subcommands Present

**Requirement:** 10-REQ-2.4
**Type:** unit
**Description:** Verify that all expected subcommands are registered on
the CLI group.

**Preconditions:**
- `spec_cli` package is importable.

**Input:**
- Import `spec_cli.cli:main` and inspect its registered commands.

**Expected:**
- Commands include: `init`, `list`, `new`, `assess`, `refine`, `accept`,
  `generate`, `validate`, `render`, `show`, `status`, `install-skill`.

**Assertion pseudocode:**
```
from spec_cli.cli import main
expected = {"init", "list", "new", "assess", "refine", "accept",
            "generate", "validate", "render", "show", "status",
            "install-skill"}
ASSERT expected == set(main.commands.keys())
```

### TS-10-6: CLI Module Imports From speclib

**Requirement:** 10-REQ-6.3
**Type:** unit
**Description:** Verify that cli.py imports business logic from
`speclib`, not from local/relative paths.

**Preconditions:**
- `packages/spec-cli/spec_cli/cli.py` exists.

**Input:**
- Read the source of `spec_cli/cli.py`.

**Expected:**
- Contains `from speclib.campaign import Campaign`.
- Contains `from speclib.session import SpecSession`.
- Contains `from speclib.errors import`.

**Assertion pseudocode:**
```
source = read("packages/spec-cli/spec_cli/cli.py")
ASSERT "from speclib.campaign import Campaign" in source
ASSERT "from speclib.session import SpecSession" in source
ASSERT "from speclib.errors import" in source
```

### TS-10-7: UI Import From spec_cli

**Requirement:** 10-REQ-6.4
**Type:** unit
**Description:** Verify that cli.py imports StatusSpinner from the
co-located ui module.

**Preconditions:**
- `packages/spec-cli/spec_cli/cli.py` exists.

**Input:**
- Read the source of `spec_cli/cli.py`.

**Expected:**
- Contains `from spec_cli.ui import StatusSpinner`.

**Assertion pseudocode:**
```
source = read("packages/spec-cli/spec_cli/cli.py")
ASSERT "from spec_cli.ui import StatusSpinner" in source
```

### TS-10-8: Skill Files Present in CLI Package

**Requirement:** 10-REQ-2.6
**Type:** unit
**Description:** Verify that the skill directory and files are in the
CLI package.

**Preconditions:**
- Restructure has been applied.

**Input:**
- Check for files under `packages/spec-cli/spec_cli/skill/`.

**Expected:**
- `packages/spec-cli/spec_cli/skill/__init__.py` exists.
- `packages/spec-cli/spec_cli/skill/spec.md` exists.

**Assertion pseudocode:**
```
ASSERT (repo_root / "packages/spec-cli/spec_cli/skill/__init__.py").exists()
ASSERT (repo_root / "packages/spec-cli/spec_cli/skill/spec.md").exists()
```

### TS-10-9: Root pyproject.toml Has No Scripts

**Requirement:** 10-REQ-3.2
**Type:** unit
**Description:** Verify that the root pyproject.toml does not define any
console scripts.

**Preconditions:**
- Root `pyproject.toml` exists.

**Input:**
- Parse root `pyproject.toml`.

**Expected:**
- No `[project.scripts]` section exists.

**Assertion pseudocode:**
```
config = parse_toml("pyproject.toml")
ASSERT "scripts" not in config.get("project", {})
```

### TS-10-10: Root pyproject.toml UV Sources

**Requirement:** 10-REQ-3.1
**Type:** unit
**Description:** Verify that the root pyproject.toml declares uv sources
for all three packages.

**Preconditions:**
- Root `pyproject.toml` exists.

**Input:**
- Parse root `pyproject.toml`.

**Expected:**
- `[tool.uv.sources]` contains entries for `afspec`, `speclib`, and
  `spec-cli`.

**Assertion pseudocode:**
```
config = parse_toml("pyproject.toml")
sources = config["tool"]["uv"]["sources"]
ASSERT "afspec" in sources
ASSERT "speclib" in sources
ASSERT "spec-cli" in sources
```

### TS-10-11: Root Makefile Targets

**Requirement:** 10-REQ-5.1, 10-REQ-5.2, 10-REQ-5.3, 10-REQ-5.4
**Type:** unit
**Description:** Verify that the root Makefile defines the required
targets.

**Preconditions:**
- Root `Makefile` exists.

**Input:**
- Read the Makefile content.

**Expected:**
- Contains targets: `check`, `lint`, `test`, `clean`.
- `check` depends on `lint` and `test`.

**Assertion pseudocode:**
```
content = read("Makefile")
ASSERT "check:" in content
ASSERT "lint:" in content
ASSERT "test:" in content
ASSERT "clean:" in content
ASSERT "check: lint test" in content or "check: lint test" matches
```

### TS-10-12: Old Directories Removed

**Requirement:** 10-REQ-6.1, 10-REQ-6.2
**Type:** unit
**Description:** Verify that the old top-level speclib/ and tests/
directories no longer exist.

**Preconditions:**
- Restructure is complete.

**Input:**
- Check for existence of top-level directories.

**Expected:**
- `speclib/` does not exist at the repo root.
- `tests/` does not exist at the repo root.

**Assertion pseudocode:**
```
ASSERT NOT (repo_root / "speclib").exists()
ASSERT NOT (repo_root / "tests").exists()
```

### TS-10-13: Root Pytest Config Testpaths

**Requirement:** 10-REQ-3.4
**Type:** unit
**Description:** Verify that the root pyproject.toml pytest config
points to all package test directories.

**Preconditions:**
- Root `pyproject.toml` exists.

**Input:**
- Parse root `pyproject.toml`.

**Expected:**
- `[tool.pytest.ini_options]` testpaths includes paths to all three
  package test directories.

**Assertion pseudocode:**
```
config = parse_toml("pyproject.toml")
testpaths = config["tool"]["pytest"]["ini_options"]["testpaths"]
ASSERT "packages/afspec/tests" in testpaths
ASSERT "packages/speclib/tests" in testpaths
ASSERT "packages/spec-cli/tests" in testpaths
```

### TS-10-14: Library Package Has afspec Path Dependency

**Requirement:** 10-REQ-1.4
**Type:** unit
**Description:** Verify that speclib's pyproject.toml declares afspec as
a path dependency.

**Preconditions:**
- `packages/speclib/pyproject.toml` exists.

**Input:**
- Parse `packages/speclib/pyproject.toml`.

**Expected:**
- `[tool.uv.sources]` contains an `afspec` entry with a path to
  `../afspec`.

**Assertion pseudocode:**
```
config = parse_toml("packages/speclib/pyproject.toml")
sources = config["tool"]["uv"]["sources"]
ASSERT sources["afspec"]["path"] == "../afspec"
```

### TS-10-15: Library Dev Dependencies

**Requirement:** 10-REQ-1.5
**Type:** unit
**Description:** Verify that the speclib pyproject.toml includes dev
dependencies.

**Preconditions:**
- `packages/speclib/pyproject.toml` exists.

**Input:**
- Parse `packages/speclib/pyproject.toml`.

**Expected:**
- `[project.optional-dependencies] dev` includes pytest, pytest-asyncio,
  hypothesis, ruff, mypy.

**Assertion pseudocode:**
```
config = parse_toml("packages/speclib/pyproject.toml")
dev_deps = config["project"]["optional-dependencies"]["dev"]
ASSERT any("pytest" in d for d in dev_deps)
ASSERT any("ruff" in d for d in dev_deps)
ASSERT any("mypy" in d for d in dev_deps)
```

## Property Test Cases

### TS-10-P1: Import Independence

**Property:** Property 1 from design.md
**Validates:** 10-REQ-1.1, 10-REQ-1.E1
**Type:** property
**Description:** Importing speclib never triggers import of click or
rich.

**For any:** public symbol exported by `speclib.__init__.__all__`
**Invariant:** Importing the symbol does not cause `click` or `rich` to
appear in `sys.modules`.

**Assertion pseudocode:**
```
import sys
# Clear click/rich from sys.modules if present
sys.modules.pop("click", None)
sys.modules.pop("rich", None)
import speclib
ASSERT "click" not in sys.modules
ASSERT "rich" not in sys.modules
```

### TS-10-P2: Dependency Completeness

**Property:** Property 2 from design.md
**Validates:** 10-REQ-7.1, 10-REQ-7.2, 10-REQ-7.3
**Type:** property
**Description:** Each package's declared dependencies are sufficient for
importing its public API.

**For any:** package P in {afspec, speclib, spec-cli}
**Invariant:** After installing only P (with transitive deps resolved),
all modules in P are importable.

**Assertion pseudocode:**
```
FOR EACH package IN ["afspec", "speclib", "spec-cli"]:
    # This is verified by the import tests in the CI pipeline
    result = subprocess.run(["uv", "run", "--isolated",
                             "python", "-c", f"import {package_module}"])
    ASSERT result.returncode == 0
```

### TS-10-P3: CLI Functional Equivalence

**Property:** Property 3 from design.md
**Validates:** 10-REQ-6.5, 10-REQ-2.4
**Type:** property
**Description:** The spec CLI produces the same output as the
pre-restructure CLI for all subcommands.

**For any:** subcommand S in the CLI command set
**Invariant:** `spec S --help` produces the same help text as the
pre-restructure CLI (modulo program name).

**Assertion pseudocode:**
```
from click.testing import CliRunner
from spec_cli.cli import main
runner = CliRunner()
FOR EACH cmd IN main.commands:
    result = runner.invoke(main, [cmd, "--help"])
    ASSERT result.exit_code == 0
    ASSERT "spec" in result.output or cmd in result.output
```

### TS-10-P4: Module Placement Correctness

**Property:** Property 4 from design.md
**Validates:** 10-REQ-1.3, 10-REQ-6.1, 10-REQ-6.2
**Type:** property
**Description:** Every Python module exists in exactly one package.

**For any:** .py file under `packages/`
**Invariant:** The file's module name is unique across all packages (no
duplicate module names in different packages).

**Assertion pseudocode:**
```
modules = {}
FOR EACH package_dir IN packages/:
    FOR EACH py_file IN package_dir/**/*.py:
        module_name = derive_module_name(py_file)
        ASSERT module_name not in modules
        modules[module_name] = package_dir
```

### TS-10-P5: Test Isolation

**Property:** Property 5 from design.md
**Validates:** 10-REQ-4.4
**Type:** property
**Description:** Running pytest from within a package directory executes
only that package's tests.

**For any:** package P with tests
**Invariant:** `pytest --collect-only` from `packages/P/` collects only
tests from `packages/P/tests/`.

**Assertion pseudocode:**
```
FOR EACH package IN ["afspec", "speclib", "spec-cli"]:
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"],
        cwd=f"packages/{package}")
    FOR EACH line IN result.stdout:
        ASSERT f"packages/{package}/tests" in line
```

### TS-10-P6: Cross-Package Quality Gate

**Property:** Property 6 from design.md
**Validates:** 10-REQ-5.1, 10-REQ-5.E1
**Type:** property
**Description:** `make check` propagates failures from any package.

**For any:** package P where a test or lint check fails
**Invariant:** `make check` returns non-zero exit code.

**Assertion pseudocode:**
```
# Introduce a deliberate failure in one package
# Run make check
result = subprocess.run(["make", "check"])
ASSERT result.returncode != 0
```

## Edge Case Tests

### TS-10-E1: speclib Without click/rich

**Requirement:** 10-REQ-1.E1
**Type:** unit
**Description:** Importing speclib does not fail when click and rich are
not installed.

**Preconditions:**
- speclib installed; click and rich NOT installed.

**Input:**
- `import speclib`

**Expected:**
- No ImportError raised.

**Assertion pseudocode:**
```
# In an environment with only speclib installed:
import speclib
ASSERT speclib.SpecSession is not None
```

### TS-10-E2: CLI Help Shows "spec"

**Requirement:** 10-REQ-2.E1
**Type:** unit
**Description:** The CLI help text uses "spec" as the program name.

**Preconditions:**
- spec-cli is installed.

**Input:**
- Run `spec --help`.

**Expected:**
- Output contains "spec" as the program name.

**Assertion pseudocode:**
```
from click.testing import CliRunner
from spec_cli.cli import main
runner = CliRunner()
result = runner.invoke(main, ["--help"])
ASSERT "spec" in result.output
```

### TS-10-E3: Relative Imports Within speclib Still Work

**Requirement:** 10-REQ-6.E1
**Type:** unit
**Description:** Internal imports within speclib resolve correctly after
the move.

**Preconditions:**
- speclib is installed.

**Input:**
- Import `speclib.agent` (which imports from `speclib.prompts`,
  `speclib.tools`, `speclib.errors`).

**Expected:**
- No ImportError.

**Assertion pseudocode:**
```
from speclib.agent import SpecAgent
ASSERT SpecAgent is not None
```

### TS-10-E4: speclib Import Without afspec

**Requirement:** 10-REQ-1.E2
**Type:** unit
**Description:** Importing speclib without afspec installed raises a
clear ImportError.

**Preconditions:**
- speclib installed; afspec NOT installed.

**Input:**
- `import speclib`

**Expected:**
- `ImportError` is raised.

**Assertion pseudocode:**
```
# In an environment without afspec:
TRY:
    import speclib
    FAIL("Expected ImportError")
EXCEPT ImportError:
    PASS
```

### TS-10-E5: spec CLI Without speclib

**Requirement:** 10-REQ-2.E2
**Type:** unit
**Description:** Running the spec CLI without speclib installed raises
ImportError.

**Preconditions:**
- spec-cli installed; speclib NOT installed.

**Input:**
- `import spec_cli.cli`

**Expected:**
- `ImportError` is raised.

**Assertion pseudocode:**
```
# In an environment without speclib:
TRY:
    import spec_cli.cli
    FAIL("Expected ImportError")
EXCEPT ImportError:
    PASS
```

### TS-10-E6: uv sync Installs All Packages

**Requirement:** 10-REQ-3.E1
**Type:** integration
**Description:** Running `uv sync` from the repo root installs all
three packages in editable mode.

**Preconditions:**
- Clean virtual environment.

**Input:**
- Run `uv sync` from repo root.

**Expected:**
- `afspec`, `speclib`, and `spec-cli` are all importable.

**Assertion pseudocode:**
```
result = subprocess.run(["uv", "sync"], cwd=repo_root)
ASSERT result.returncode == 0
for mod in ["afspec", "speclib", "spec_cli"]:
    result = subprocess.run(["uv", "run", "python", "-c", f"import {mod}"])
    ASSERT result.returncode == 0
```

### TS-10-E7: CLI Test in Correct Package

**Requirement:** 10-REQ-4.E1
**Type:** unit
**Description:** Test files that import from both speclib and spec_cli
are placed in the spec-cli test directory.

**Preconditions:**
- Restructure is complete.

**Input:**
- Scan test files in `packages/speclib/tests/` for imports of `spec_cli`.

**Expected:**
- No test file in `packages/speclib/tests/` imports from `spec_cli`.

**Assertion pseudocode:**
```
FOR EACH test_file IN packages/speclib/tests/*.py:
    source = read(test_file)
    ASSERT "from spec_cli" not in source
    ASSERT "import spec_cli" not in source
```

### TS-10-E8: Makefile Reports Failure on Lint Error

**Requirement:** 10-REQ-5.E1
**Type:** integration
**Description:** When a lint or test failure occurs in one package,
`make check` exits non-zero.

**Preconditions:**
- Repository with all packages.
- A deliberate syntax error introduced in one package.

**Input:**
- Introduce an error, then run `make check`.

**Expected:**
- `make check` returns non-zero exit code.

**Assertion pseudocode:**
```
# Introduce deliberate error
write("packages/speclib/speclib/_deliberate_error.py", "def f( = 1")
result = subprocess.run(["make", "check"], cwd=repo_root)
ASSERT result.returncode != 0
# Clean up
remove("packages/speclib/speclib/_deliberate_error.py")
```

### TS-10-E9: Automatic speclib Installation via spec-cli

**Requirement:** 10-REQ-7.E1
**Type:** integration
**Description:** Installing spec-cli automatically installs speclib via
path dependency.

**Preconditions:**
- Clean environment with no packages pre-installed.

**Input:**
- `uv pip install ./packages/spec-cli`

**Expected:**
- Both `spec_cli` and `speclib` are importable afterward.

**Assertion pseudocode:**
```
result = subprocess.run(["uv", "pip", "install", "./packages/spec-cli"])
ASSERT result.returncode == 0
result = subprocess.run(["uv", "run", "python", "-c", "import speclib"])
ASSERT result.returncode == 0
```

### TS-10-E10: Patch Targets Still Valid

**Requirement:** 10-REQ-6.E2
**Type:** unit
**Description:** Module patch paths used in tests still resolve after
the restructure.

**Preconditions:**
- speclib and spec-cli are installed.

**Input:**
- Common patch targets: `speclib.session._utcnow`,
  `speclib.auth.create_client`.

**Expected:**
- `unittest.mock.patch` can resolve these paths.

**Assertion pseudocode:**
```
from unittest.mock import patch
with patch("speclib.session._utcnow") as mock:
    ASSERT mock is not None
with patch("speclib.auth.create_client") as mock:
    ASSERT mock is not None
```

## Integration Smoke Tests

### TS-10-SMOKE-1: spec new Creates Spec Directory

**Execution Path:** Path 1 from design.md
**Description:** End-to-end test that `spec new` creates a spec
directory via the full CLI → speclib → afspec chain.

**Setup:** Create a temporary campaign directory with `campaign.yaml`.
Create a temporary PRD file.

**Trigger:** `spec new prd.md --name test_spec`

**Expected side effects:**
- A spec directory `01_test_spec/` created in the campaign directory.
- `01_test_spec/prd.md` contains the PRD content.
- `01_test_spec/_session.json` exists with state `init`.

**Must NOT satisfy with:** Do not mock `Campaign`, `SpecSession`, or
filesystem operations — the full path must be live.

**Assertion pseudocode:**
```
runner = CliRunner()
with runner.isolated_filesystem():
    Campaign.create(Path("."), "test", "")
    Path("prd.md").write_text("# Test PRD")
    result = runner.invoke(main, ["new", "prd.md", "--name", "test_spec"])
    ASSERT result.exit_code == 0
    ASSERT Path("01_test_spec/prd.md").exists()
    ASSERT Path("01_test_spec/_session.json").exists()
```

### TS-10-SMOKE-2: Library Used Without CLI

**Execution Path:** Path 3 from design.md
**Description:** End-to-end test that the library can be used
programmatically without the CLI.

**Setup:** Create a temporary campaign directory.

**Trigger:** Use `Campaign.create()` and `campaign.new_spec()`
programmatically.

**Expected side effects:**
- Spec directory created with `prd.md` and `_session.json`.
- No CLI or Rich imports triggered.

**Must NOT satisfy with:** Do not import `spec_cli` anywhere in this
test.

**Assertion pseudocode:**
```
from speclib import Campaign
campaign = Campaign.create(tmp_path, "test", "test campaign")
session = campaign.new_spec("my_spec", "# Test PRD")
ASSERT session.spec_dir.exists()
ASSERT (session.spec_dir / "prd.md").exists()
ASSERT "click" not in sys.modules
```

### TS-10-SMOKE-3: make check Runs Successfully

**Execution Path:** Path from design.md covering root Makefile
**Description:** Verify that `make check` from the repo root runs lint
and tests across all packages.

**Setup:** Clean repository checkout with all dependencies installed.

**Trigger:** `make check` from repo root.

**Expected side effects:**
- Exit code 0.
- Both lint and test phases run.

**Must NOT satisfy with:** Do not mock the make command or any test
framework.

**Assertion pseudocode:**
```
result = subprocess.run(["make", "check"], cwd=repo_root)
ASSERT result.returncode == 0
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 10-REQ-1.1 | TS-10-P1 | property |
| 10-REQ-1.2 | TS-10-2 | unit |
| 10-REQ-1.3 | TS-10-1 | unit |
| 10-REQ-1.4 | TS-10-14 | unit |
| 10-REQ-1.5 | TS-10-15 | unit |
| 10-REQ-1.E1 | TS-10-E1, TS-10-P1 | unit, property |
| 10-REQ-1.E2 | TS-10-E4 | unit |
| 10-REQ-2.1 | TS-10-3 | unit |
| 10-REQ-2.2 | TS-10-4 | unit |
| 10-REQ-2.3 | TS-10-4 | unit |
| 10-REQ-2.4 | TS-10-5, TS-10-P3 | unit, property |
| 10-REQ-2.5 | TS-10-6 | unit |
| 10-REQ-2.6 | TS-10-8 | unit |
| 10-REQ-2.E1 | TS-10-E2 | unit |
| 10-REQ-2.E2 | TS-10-E5 | unit |
| 10-REQ-3.1 | TS-10-10 | unit |
| 10-REQ-3.2 | TS-10-9 | unit |
| 10-REQ-3.3 | TS-10-11 | unit |
| 10-REQ-3.4 | TS-10-13 | unit |
| 10-REQ-3.E1 | TS-10-E6, TS-10-P2 | integration, property |
| 10-REQ-4.1 | TS-10-1 | unit |
| 10-REQ-4.2 | TS-10-12 | unit |
| 10-REQ-4.3 | TS-10-11, TS-10-SMOKE-3 | unit, integration |
| 10-REQ-4.4 | TS-10-P5 | property |
| 10-REQ-4.E1 | TS-10-E7 | unit |
| 10-REQ-5.1 | TS-10-11 | unit |
| 10-REQ-5.2 | TS-10-11 | unit |
| 10-REQ-5.3 | TS-10-11 | unit |
| 10-REQ-5.4 | TS-10-11 | unit |
| 10-REQ-5.5 | TS-10-11 | unit |
| 10-REQ-5.E1 | TS-10-E8, TS-10-P6 | integration, property |
| 10-REQ-6.1 | TS-10-12 | unit |
| 10-REQ-6.2 | TS-10-12 | unit |
| 10-REQ-6.3 | TS-10-6 | unit |
| 10-REQ-6.4 | TS-10-7 | unit |
| 10-REQ-6.5 | TS-10-P3 | property |
| 10-REQ-6.E1 | TS-10-E3 | unit |
| 10-REQ-6.E2 | TS-10-E10 | unit |
| 10-REQ-7.1 | TS-10-P2 | property |
| 10-REQ-7.2 | TS-10-P2 | property |
| 10-REQ-7.3 | TS-10-P2 | property |
| 10-REQ-7.E1 | TS-10-E9, TS-10-P2 | integration, property |
| Property 1 | TS-10-P1 | property |
| Property 2 | TS-10-P2 | property |
| Property 3 | TS-10-P3 | property |
| Property 4 | TS-10-P4 | property |
| Property 5 | TS-10-P5 | property |
| Property 6 | TS-10-P6 | property |
