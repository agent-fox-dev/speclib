# Requirements Document

## Introduction

This document specifies the requirements for restructuring the speclib
repository from a single-package layout into a monorepo with three
independent packages under `packages/`: the existing `afspec` format
library, the `speclib` core library, and the `spec-cli` command-line
tool.

## Glossary

- **monorepo**: A single git repository containing multiple independently
  installable packages.
- **workspace root**: The top-level directory of the monorepo. Contains a
  `pyproject.toml` that is not itself installable but defines shared
  tooling configuration and path-dependency sources.
- **path dependency**: A `uv`/pip mechanism where one package references
  another by filesystem path rather than by version from a registry.
- **console script**: A Python entry point declared in `pyproject.toml`
  under `[project.scripts]` that creates a shell command.
- **speclib**: The core library package providing the agent pipeline,
  session state machine, campaign management, configuration, and
  authentication.
- **spec-cli**: The CLI package providing the `spec` command. Depends on
  `speclib`.
- **afspec**: The existing spec-format library under `packages/afspec/`.

## Requirements

### Requirement 1: Library Package Extraction

**User Story:** As a developer, I want the speclib library to be a
standalone package under `packages/speclib/`, so that I can import and
use the agent pipeline, session management, and campaign logic from any
Python code without installing CLI dependencies.

#### Acceptance Criteria

1. [10-REQ-1.1] WHEN a user installs `packages/speclib/` via
   `uv pip install ./packages/speclib`, THE system SHALL provide the
   `speclib` package importable as `import speclib` with all public
   symbols from `speclib.__init__` available.

2. [10-REQ-1.2] THE `packages/speclib/pyproject.toml` SHALL declare
   dependencies only on libraries needed by the core library
   (`anthropic`, `pyyaml`, `afspec`) and SHALL NOT depend on `click` or
   `rich`.

3. [10-REQ-1.3] THE `packages/speclib/` directory SHALL contain the
   following modules from the current `speclib/` package: `__init__.py`,
   `agent.py`, `auth.py`, `campaign.py`, `config.py`, `errors.py`,
   `prompts.py`, `session.py`, `tools.py`.

4. [10-REQ-1.4] THE `packages/speclib/pyproject.toml` SHALL declare
   `afspec` as a path dependency pointing to `../afspec`.

5. [10-REQ-1.5] THE `packages/speclib/pyproject.toml` SHALL define a
   `[project.optional-dependencies] dev` section with test and lint
   tooling (`pytest`, `pytest-asyncio`, `hypothesis`, `ruff`, `mypy`).

#### Edge Cases

1. [10-REQ-1.E1] IF the `speclib` package is installed without
   `spec-cli`, THEN importing `speclib` SHALL NOT raise `ImportError`
   for missing `click` or `rich` dependencies.

2. [10-REQ-1.E2] IF the `speclib` package is installed and `afspec` is
   not installed, THEN importing `speclib` SHALL raise `ImportError`
   with a clear message indicating the missing `afspec` dependency.

### Requirement 2: CLI Package Creation

**User Story:** As a user, I want to install and run the spec CLI
independently via a `spec` command, so that I can use the tool from the
command line without needing to know about the library internals.

#### Acceptance Criteria

1. [10-REQ-2.1] WHEN a user installs `packages/spec-cli/` via
   `uv pip install ./packages/spec-cli`, THE system SHALL provide a
   `spec` console script entry point that invokes the CLI.

2. [10-REQ-2.2] THE `packages/spec-cli/pyproject.toml` SHALL declare a
   dependency on `speclib` as a path dependency pointing to
   `../speclib`.

3. [10-REQ-2.3] THE `packages/spec-cli/pyproject.toml` SHALL declare
   dependencies on `click` and `rich` (the CLI-specific dependencies).

4. [10-REQ-2.4] THE `spec` CLI SHALL provide the same subcommands as
   the current `spec` CLI: `init`, `list`, `new`, `assess`, `refine`,
   `accept`, `generate`, `validate`, `render`, `show`, `status`, and
   `install-skill`.

5. [10-REQ-2.5] THE CLI module SHALL live at
   `packages/spec-cli/spec_cli/cli.py` and import all business logic
   from the `speclib` package.

6. [10-REQ-2.6] THE `packages/spec-cli/` directory SHALL contain the
   `skill/` subdirectory with `__init__.py` and `spec.md`.

#### Edge Cases

1. [10-REQ-2.E1] IF a user runs `spec --help`, THEN THE CLI SHALL
   display help text with the program name `spec`.

2. [10-REQ-2.E2] IF the `speclib` dependency is not installed, THEN
   running `spec` SHALL raise an `ImportError` with a message indicating
   the missing `speclib` package.

### Requirement 3: Workspace Root Configuration

**User Story:** As a developer, I want the root `pyproject.toml` to
serve as a workspace configuration file, so that `uv` can resolve all
inter-package dependencies and shared tooling runs from the repo root.

#### Acceptance Criteria

1. [10-REQ-3.1] THE root `pyproject.toml` SHALL define `uv` source
   entries for all packages under `packages/` (`afspec`, `speclib`,
   `spec-cli`) as editable path dependencies.

2. [10-REQ-3.2] THE root `pyproject.toml` SHALL NOT define a
   `[project.scripts]` section (no console scripts at the root level).

3. [10-REQ-3.3] THE root `pyproject.toml` SHALL define shared tool
   configuration for `ruff` and `mypy` that applies when running from
   the repo root.

4. [10-REQ-3.4] THE root `pyproject.toml` SHALL define
   `[tool.pytest.ini_options]` with `testpaths` pointing to all package
   test directories.

#### Edge Cases

1. [10-REQ-3.E1] IF `uv sync` is run from the repo root, THEN all
   three packages (`afspec`, `speclib`, `spec-cli`) SHALL be installed
   in editable mode in the virtual environment.

### Requirement 4: Test Organization

**User Story:** As a developer, I want each package's tests to live
alongside the package, so that I can run tests for a single package in
isolation.

#### Acceptance Criteria

1. [10-REQ-4.1] THE library tests SHALL be located at
   `packages/speclib/tests/` and SHALL test `speclib` modules
   (`agent`, `auth`, `campaign`, `config`, `errors`, `prompts`,
   `session`, `tools`).

2. [10-REQ-4.2] THE CLI tests SHALL be located at
   `packages/spec-cli/tests/` and SHALL test `spec_cli` modules
   (`cli`, `ui`, `skill`).

3. [10-REQ-4.3] WHEN `make test` is run from the repo root, THE system
   SHALL execute tests across all packages and return a combined pass/fail
   result.

4. [10-REQ-4.4] WHEN `uv run pytest` is run from within a package
   directory (e.g., `packages/speclib/`), THE system SHALL execute only
   that package's tests.

#### Edge Cases

1. [10-REQ-4.E1] IF a test file imports from both `speclib` and
   `spec_cli`, THEN it SHALL be placed in the `spec-cli` test directory
   since it tests the higher-level package.

### Requirement 5: Root Makefile Orchestration

**User Story:** As a developer, I want `make check` at the repo root to
run lint and tests across all packages, so that I have a single command
to verify the entire monorepo.

#### Acceptance Criteria

1. [10-REQ-5.1] THE root Makefile SHALL define a `check` target that
   runs `lint` and `test` targets in sequence.

2. [10-REQ-5.2] THE root Makefile `lint` target SHALL run `ruff check`
   and `mypy` across all package source directories.

3. [10-REQ-5.3] THE root Makefile `test` target SHALL run `pytest`
   across all package test directories.

4. [10-REQ-5.4] THE root Makefile SHALL retain the `clean` target that
   removes temporary artifacts from all packages.

5. [10-REQ-5.5] THE root Makefile SHALL define all targets as `.PHONY`.

#### Edge Cases

1. [10-REQ-5.E1] IF a lint or test failure occurs in one package, THEN
   THE Makefile SHALL report the failure and exit with a non-zero status
   code.

### Requirement 6: File Migration Integrity

**User Story:** As a developer, I want all existing source files and
tests to be moved to their correct new locations without modification to
their content (except import path adjustments), so that no functionality
is lost during the restructure.

#### Acceptance Criteria

1. [10-REQ-6.1] WHEN the restructure is complete, THE system SHALL have
   no Python source files remaining in the top-level `speclib/`
   directory (it SHALL be removed).

2. [10-REQ-6.2] WHEN the restructure is complete, THE system SHALL have
   no test files remaining in the top-level `tests/` directory (it SHALL
   be removed).

3. [10-REQ-6.3] THE CLI module at `packages/spec-cli/spec_cli/cli.py`
   SHALL import from `speclib` (not from a relative path or from
   `spec_cli`) for all business logic classes: `Campaign`, `SpecSession`,
   `CampaignError`, `SessionError`, `SpeclibError`.

4. [10-REQ-6.4] THE CLI module SHALL import `StatusSpinner` from
   `spec_cli.ui` (the co-located UI module within the CLI package).

5. [10-REQ-6.5] WHEN the restructure is complete, THE `spec` CLI SHALL
   produce identical output for all subcommands as the pre-restructure
   CLI (except for the program name in help text).

#### Edge Cases

1. [10-REQ-6.E1] IF any source file contains a relative import within
   `speclib`, THEN the import SHALL still resolve correctly after the
   file is moved to `packages/speclib/speclib/`.

2. [10-REQ-6.E2] IF any test file patches a module path (e.g.,
   `@patch("speclib.session._utcnow")`), THEN the patch target SHALL
   remain valid after the restructure.

### Requirement 7: Individual Package Installation

**User Story:** As a developer, I want to be able to install each
package independently using `uv`, so that I can use just the library
or just one CLI tool without installing everything.

#### Acceptance Criteria

1. [10-REQ-7.1] WHEN a user runs `uv pip install ./packages/speclib`,
   THE system SHALL install only the `speclib` package and its
   dependencies (`afspec`, `anthropic`, `pyyaml`), without installing
   `click` or `rich`.

2. [10-REQ-7.2] WHEN a user runs `uv pip install ./packages/spec-cli`,
   THE system SHALL install the `spec-cli` package along with `speclib`
   (via path dependency) and CLI dependencies (`click`, `rich`), AND
   SHALL make the `spec` command available.

3. [10-REQ-7.3] WHEN a user runs `uv pip install ./packages/afspec`,
   THE system SHALL install only the `afspec` package and its
   dependencies, independent of `speclib` or `spec-cli`.

#### Edge Cases

1. [10-REQ-7.E1] IF a user installs `spec-cli` without first manually
   installing `speclib`, THEN `uv` SHALL resolve and install `speclib`
   automatically via the path dependency declaration.
