# Implementation Plan: Monorepo Restructure

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

This restructure moves files from the current flat layout into a
monorepo under `packages/`. The approach is:

1. Write structural tests first (task group 1)
2. Create the library package (task group 2)
3. Create the spec-cli package skeleton and pyproject.toml (task group 3)
4. Move CLI source modules (task group 4)
5. Update CLI imports and program name (task group 5)
6. Move CLI tests and update test imports (task group 6)
7. Checkpoint — spec-cli package complete (task group 7)
8. Rewrite root pyproject.toml and regenerate lock file (task group 8)
9. Update root Makefile (task group 9)
10. Remove old directories and update documentation (task group 10)
11. Wiring verification (task group 11)

The restructure preserves all business logic and only changes file
locations, import paths, and configuration files.

## Test Commands

- Spec tests: `uv run pytest -q packages/speclib/tests/ packages/spec-cli/tests/`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check && uv run mypy packages/speclib/speclib/ packages/spec-cli/spec_cli/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Create test file for structural checks
    - Create `packages/speclib/tests/test_structure.py`
    - Create `packages/spec-cli/tests/test_structure.py`
    - Add tests for file existence (TS-10-1), pyproject.toml content
      (TS-10-2, TS-10-3, TS-10-4, TS-10-9, TS-10-10, TS-10-13,
      TS-10-14, TS-10-15), CLI subcommands (TS-10-5), import sources
      (TS-10-6, TS-10-7), skill files (TS-10-8), old directory removal
      (TS-10-12), Makefile targets (TS-10-11)
    - Add edge case tests: uv sync installs all (TS-10-E6), cross-package
      test isolation (TS-10-E7), Makefile failure propagation (TS-10-E8),
      automatic speclib install via spec-cli (TS-10-E9)
    - _Test Spec: TS-10-1 through TS-10-15, TS-10-E6, TS-10-E7, TS-10-E8, TS-10-E9_

  - [x] 1.2 Create test file for import/property tests
    - Create `packages/speclib/tests/test_import_isolation.py`
    - Add import independence test (TS-10-P1)
    - Add module placement uniqueness test (TS-10-P4)
    - Add internal import resolution test (TS-10-E3)
    - Add patch target resolution test (TS-10-E10)
    - _Test Spec: TS-10-P1, TS-10-P4, TS-10-E3, TS-10-E10_

  - [x] 1.3 Create test file for CLI tests
    - Create `packages/spec-cli/tests/test_cli_equivalence.py`
    - Add CLI help name test (TS-10-E2)
    - Add CLI subcommand help test (TS-10-P3)
    - _Test Spec: TS-10-P3, TS-10-E2_

  - [x] 1.4 Create integration smoke test file
    - Create `packages/spec-cli/tests/test_smoke.py`
    - Add `spec new` end-to-end test (TS-10-SMOKE-1)
    - Add library-only usage test (TS-10-SMOKE-2)
    - _Test Spec: TS-10-SMOKE-1, TS-10-SMOKE-2_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings introduced: `uv run ruff check`

- [x] 2. Create speclib library package
  - [x] 2.1 Create `packages/speclib/` directory structure
    - Create `packages/speclib/speclib/` directory
    - Create `packages/speclib/tests/` directory
    - _Requirements: 10-REQ-1.3_

  - [x] 2.2 Move library modules via git mv
    - `git mv speclib/__init__.py packages/speclib/speclib/__init__.py`
    - `git mv speclib/agent.py packages/speclib/speclib/agent.py`
    - `git mv speclib/auth.py packages/speclib/speclib/auth.py`
    - `git mv speclib/campaign.py packages/speclib/speclib/campaign.py`
    - `git mv speclib/config.py packages/speclib/speclib/config.py`
    - `git mv speclib/errors.py packages/speclib/speclib/errors.py`
    - `git mv speclib/prompts.py packages/speclib/speclib/prompts.py`
    - `git mv speclib/session.py packages/speclib/speclib/session.py`
    - `git mv speclib/tools.py packages/speclib/speclib/tools.py`
    - _Requirements: 10-REQ-1.3, 10-REQ-6.1_

  - [x] 2.3 Create `packages/speclib/pyproject.toml`
    - Set name to `speclib`, version `0.1.0`
    - Set `requires-python = ">=3.14"`
    - Declare dependencies: `afspec`, `anthropic[vertex,bedrock]`, `pyyaml`
    - Do NOT include `click` or `rich`
    - Add `[tool.uv.sources]` with `afspec` path dependency
    - Add `[project.optional-dependencies] dev` with test/lint tools
    - Add `[build-system]` with hatchling
    - Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]`
    - _Requirements: 10-REQ-1.2, 10-REQ-1.4, 10-REQ-1.5_

  - [x] 2.4 Move library tests
    - Move test files for library modules from `tests/` to
      `packages/speclib/tests/`: `test_agent.py`, `test_auth.py`,
      `test_campaign.py`, `test_config.py`, `test_prompts.py`,
      `test_session.py`, `test_session_agent.py`, `test_tools.py`,
      `test_scaffold.py`
    - Move `tests/conftest.py` and `tests/conftest_agent.py` to
      `packages/speclib/tests/`
    - Move `tests/__init__.py` to `packages/speclib/tests/`
    - _Requirements: 10-REQ-4.1_

  - [x] 2.V Verify task group 2
    - [x] Library modules exist at `packages/speclib/speclib/`
    - [x] `packages/speclib/pyproject.toml` is valid
    - [x] Library tests exist at `packages/speclib/tests/`
    - [x] Spec tests TS-10-1, TS-10-2, TS-10-14, TS-10-15 pass
    - [x] No linter warnings: `uv run ruff check packages/speclib/`

- [x] 3. Create spec-cli package skeleton
  - [x] 3.1 Create `packages/spec-cli/spec_cli/` directory
    - Create `packages/spec-cli/spec_cli/` source directory
    - Create `packages/spec-cli/spec_cli/__init__.py`
    - _Requirements: 10-REQ-2.5_

  - [x] 3.2 Create `packages/spec-cli/pyproject.toml`
    - Set name to `spec-cli`, version `0.1.0`
    - Set `requires-python = ">=3.14"`
    - Declare dependencies: `speclib`, `click`, `rich`
    - Add `[project.scripts]` with `spec = "spec_cli.cli:main"`
    - Add `[tool.uv.sources]` with `speclib` path dependency
    - Add `[project.optional-dependencies] dev` with test tools
    - Add `[build-system]` with hatchling
    - Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]`
    - _Requirements: 10-REQ-2.1, 10-REQ-2.2, 10-REQ-2.3_

  - [x] 3.V Verify task group 3
    - [x] `packages/spec-cli/spec_cli/__init__.py` exists
    - [x] `packages/spec-cli/pyproject.toml` is valid TOML
    - [x] Spec tests TS-10-3, TS-10-4 pass
    - [x] No linter warnings: `uv run ruff check packages/spec-cli/`

- [x] 4. Move CLI source modules
  - [x] 4.1 Move cli.py and ui.py via git mv
    - `git mv speclib/cli.py packages/spec-cli/spec_cli/cli.py`
    - `git mv speclib/ui.py packages/spec-cli/spec_cli/ui.py`
    - _Requirements: 10-REQ-2.5_

  - [x] 4.2 Move skill/ directory via git mv
    - `git mv speclib/skill/ packages/spec-cli/spec_cli/skill/`
    - _Requirements: 10-REQ-2.6_

  - [x] 4.V Verify task group 4
    - [x] `packages/spec-cli/spec_cli/cli.py` exists
    - [x] `packages/spec-cli/spec_cli/ui.py` exists
    - [x] `packages/spec-cli/spec_cli/skill/__init__.py` exists
    - [x] `packages/spec-cli/spec_cli/skill/spec.md` exists
    - [x] Spec tests TS-10-6, TS-10-8 pass
    - [x] No linter warnings: `uv run ruff check packages/spec-cli/`

- [x] 5. Update CLI imports and program name
  - [x] 5.1 Update imports in cli.py
    - Keep `from speclib.campaign import Campaign` (unchanged)
    - Keep `from speclib.errors import ...` (unchanged)
    - Keep `from speclib.session import SpecSession` (unchanged)
    - Change `from speclib.ui import StatusSpinner` to
      `from spec_cli.ui import StatusSpinner`
    - Change `from speclib.skill import ...` to
      `from spec_cli.skill import ...`
    - _Requirements: 10-REQ-6.3, 10-REQ-6.4_

  - [x] 5.2 Update CLI group help text
    - Verify CLI group help text displays "spec"
    - _Requirements: 10-REQ-2.E1_

  - [x] 5.V Verify task group 5
    - [x] `cli.py` imports business logic from `speclib`
    - [x] `cli.py` imports `StatusSpinner` from `spec_cli.ui`
    - [x] `cli.py` imports skill from `spec_cli.skill`
    - [x] Spec tests TS-10-5, TS-10-6, TS-10-7 pass
    - [x] No linter warnings: `uv run ruff check packages/spec-cli/`

- [x] 6. Move CLI tests and update test imports
  - [x] 6.1 Move test files to `packages/spec-cli/tests/`
    - `git mv tests/test_cli.py packages/spec-cli/tests/test_cli.py`
    - `git mv tests/test_ui.py packages/spec-cli/tests/test_ui.py`
    - `git mv tests/test_skill.py packages/spec-cli/tests/test_skill.py`
    - `git mv tests/test_install_skill.py packages/spec-cli/tests/test_install_skill.py`
    - _Requirements: 10-REQ-4.2_

  - [x] 6.2 Create test infrastructure files
    - Create `packages/spec-cli/tests/__init__.py`
    - Create `packages/spec-cli/tests/conftest.py` if needed
    - _Requirements: 10-REQ-4.2_

  - [x] 6.3 Update import paths in moved test files
    - Change `from speclib.cli` → `from spec_cli.cli`
    - Change `from speclib.ui` → `from spec_cli.ui`
    - Change `from speclib.skill` → `from spec_cli.skill`
    - Update any patch targets that reference `speclib.cli` or
      `speclib.ui` to use `spec_cli.cli` / `spec_cli.ui`
    - _Requirements: 10-REQ-4.2, 10-REQ-4.E1_

  - [x] 6.V Verify task group 6
    - [x] CLI tests exist at `packages/spec-cli/tests/`
    - [x] No test in `packages/speclib/tests/` imports from `spec_cli`
    - [x] Spec tests TS-10-E2, TS-10-P3 pass
    - [x] No linter warnings: `uv run ruff check packages/spec-cli/`

- [x] 7. Checkpoint - spec-cli Package Complete
  - Ensure all spec-cli spec tests pass
  - Verify `spec_cli` package is importable
  - Verify all CLI subcommands are registered
  - _Test Spec: TS-10-3 through TS-10-8, TS-10-E2, TS-10-P3_

- [x] 8. Rewrite root pyproject.toml and regenerate lock file
  - [x] 8.1 Rewrite root `pyproject.toml`
    - Change project name to `speclib-workspace`
    - Remove `[project.scripts]` section
    - Update dependencies to reference `spec-cli` (which pulls in
      `speclib` transitively)
    - Update `[tool.uv.sources]` with all three package paths
    - Update `[tool.pytest.ini_options]` testpaths to point to all
      package test directories
    - Keep shared `[tool.ruff]` and `[tool.mypy]` configuration
    - _Requirements: 10-REQ-3.1, 10-REQ-3.2, 10-REQ-3.3, 10-REQ-3.4_

  - [x] 8.2 Run `uv sync` to regenerate lock file
    - Run `uv sync` from repo root to resolve all path dependencies
    - Verify all packages are installed in the virtual environment
    - _Requirements: 10-REQ-3.E1_

  - [x] 8.V Verify task group 8
    - [x] Root `pyproject.toml` has no `[project.scripts]`
    - [x] Root `pyproject.toml` has all UV sources
    - [x] `uv sync` succeeds
    - [x] Spec tests TS-10-9, TS-10-10, TS-10-13 pass

- [x] 9. Update root Makefile
  - [x] 9.1 Update Makefile targets
    - Update `lint` target to run ruff and mypy across all package
      source directories
    - Update `test` target to run pytest across all packages
    - Keep `clean` target, extend to clean all package directories
    - Ensure all targets are `.PHONY`
    - _Requirements: 10-REQ-5.1, 10-REQ-5.2, 10-REQ-5.3, 10-REQ-5.4,
      10-REQ-5.5_

  - [x] 9.V Verify task group 9
    - [x] Root Makefile has check, lint, test, clean targets
    - [x] Spec test TS-10-11 passes
    - [x] `make check` passes

- [x] 10. Remove old directories and update documentation
  - [x] 10.1 Remove old top-level directories
    - Remove `speclib/` directory (should be empty after git mv)
    - Remove `tests/` directory (should be empty after git mv)
    - Verify no stray files remain
    - _Requirements: 10-REQ-6.1, 10-REQ-6.2_

  - [x] 10.2 Update CLAUDE.md and README.md
    - Update project structure description in CLAUDE.md
    - Update installation and usage instructions in README.md
    - Update test command references
    - _Requirements: documentation_

  - [x] 10.3 Run full verification
    - Run `make check` from repo root
    - Run `uv run pytest` from `packages/speclib/` (isolation check)
    - Run `uv run pytest` from `packages/spec-cli/` (isolation check)
    - Run `uv run pytest` from `packages/afspec/` (isolation check)
    - Verify all existing tests still pass

  - [x] 10.V Verify task group 10
    - [x] Old `speclib/` and `tests/` directories removed
    - [x] Spec tests TS-10-12 pass
    - [x] All existing tests pass: `make check`
    - [x] `uv run pytest` works from each package directory

- [x] 11. Wiring verification

  - [x] 11.1 Trace every execution path from design.md end-to-end
    - For Path 1 (`spec new`): verify `spec_cli.cli:new_cmd` calls
      `speclib.campaign:Campaign.open` and `Campaign.new_spec`
    - For Path 2 (`spec assess`): verify `spec_cli.cli:assess_cmd`
      calls `speclib.session:SpecSession.resume` and `SpecSession.assess`
    - For Path 3 (library import): verify `speclib` is importable and
      `Campaign`, `SpecSession` are accessible
    - Confirm no function in the chain is a stub
    - Every path must be live in production code
    - _Requirements: all_

  - [x] 11.2 Verify return values propagate correctly
    - For every function in this spec that returns data consumed by a
      caller, confirm the caller receives and uses the return value
    - Grep for callers of `Campaign.open`, `Campaign.new_spec`,
      `SpecSession.resume`; confirm none discards the return value
    - _Requirements: all_

  - [x] 11.3 Run the integration smoke tests
    - All `TS-10-SMOKE-*` tests pass using real components
    - `spec new` creates spec directory through full chain
    - Library can be used without CLI
    - `make check` passes
    - _Test Spec: TS-10-SMOKE-1, TS-10-SMOKE-2, TS-10-SMOKE-3_

  - [x] 11.4 Stub / dead-code audit
    - Search all files touched by this spec for: `return []`,
      `return None` on non-Optional returns, `pass` in non-abstract
      methods, `# TODO`, `# stub`, `NotImplementedError`
    - Each hit must be justified or replaced
    - Document any intentional stubs

  - [x] 11.5 Cross-spec entry point verification
    - Verify that `spec_cli.cli:main` (the console script entry point)
      is reachable from the installed `spec` command
    - Verify that `speclib.__init__` re-exports all public symbols
    - _Requirements: all_

  - [x] 11.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain in touched files
    - [x] All execution paths from design.md are live (traceable in code)
    - [x] All cross-spec entry points are called from production code
    - [x] All existing tests still pass: `make check`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 10-REQ-1.1 | TS-10-P1 | 2.2, 2.3 | test_import_isolation.py |
| 10-REQ-1.2 | TS-10-2 | 2.3 | test_structure.py |
| 10-REQ-1.3 | TS-10-1 | 2.2 | test_structure.py |
| 10-REQ-1.4 | TS-10-14 | 2.3 | test_structure.py |
| 10-REQ-1.5 | TS-10-15 | 2.3 | test_structure.py |
| 10-REQ-1.E1 | TS-10-E1, TS-10-P1 | 2.3 | test_import_isolation.py |
| 10-REQ-1.E2 | TS-10-E4 | 2.2 | test_import_isolation.py |
| 10-REQ-2.1 | TS-10-3 | 3.2 | test_structure.py |
| 10-REQ-2.2 | TS-10-4 | 3.2 | test_structure.py |
| 10-REQ-2.3 | TS-10-4 | 3.2 | test_structure.py |
| 10-REQ-2.4 | TS-10-5, TS-10-P3 | 4.1, 5.1 | test_cli_equivalence.py |
| 10-REQ-2.5 | TS-10-6 | 3.1, 4.1 | test_structure.py |
| 10-REQ-2.6 | TS-10-8 | 4.2 | test_structure.py |
| 10-REQ-2.E1 | TS-10-E2 | 5.2 | test_cli_equivalence.py |
| 10-REQ-2.E2 | TS-10-E5 | 3.2 | test_structure.py |
| 10-REQ-3.1 | TS-10-10 | 8.1 | test_structure.py |
| 10-REQ-3.2 | TS-10-9 | 8.1 | test_structure.py |
| 10-REQ-3.3 | TS-10-11 | 8.1 | test_structure.py |
| 10-REQ-3.4 | TS-10-13 | 8.1 | test_structure.py |
| 10-REQ-3.E1 | TS-10-P2 | 8.2 | manual / CI |
| 10-REQ-4.1 | TS-10-1 | 2.4 | test_structure.py |
| 10-REQ-4.2 | TS-10-12 | 6.1 | test_structure.py |
| 10-REQ-4.3 | TS-10-11, TS-10-SMOKE-3 | 9.1 | test_structure.py |
| 10-REQ-4.E1 | TS-10-E7 | 6.3 | test_structure.py |
| 10-REQ-4.4 | TS-10-P5 | 2.3, 3.2 | manual / CI |
| 10-REQ-5.1 | TS-10-11 | 9.1 | test_structure.py |
| 10-REQ-5.2 | TS-10-11 | 9.1 | test_structure.py |
| 10-REQ-5.3 | TS-10-11 | 9.1 | test_structure.py |
| 10-REQ-5.4 | TS-10-11 | 9.1 | test_structure.py |
| 10-REQ-5.5 | TS-10-11 | 9.1 | test_structure.py |
| 10-REQ-5.E1 | TS-10-P6 | 9.1 | manual / CI |
| 10-REQ-6.1 | TS-10-12 | 10.1 | test_structure.py |
| 10-REQ-6.2 | TS-10-12 | 10.1 | test_structure.py |
| 10-REQ-6.3 | TS-10-6 | 5.1 | test_structure.py |
| 10-REQ-6.4 | TS-10-7 | 5.1 | test_structure.py |
| 10-REQ-6.5 | TS-10-P3 | 5.1, 5.2 | test_cli_equivalence.py |
| 10-REQ-6.E1 | TS-10-E3 | 2.2 | test_import_isolation.py |
| 10-REQ-6.E2 | TS-10-E10 | 2.4 | test_import_isolation.py |
| 10-REQ-7.1 | TS-10-P2 | 2.3 | manual / CI |
| 10-REQ-7.2 | TS-10-P2 | 3.2 | manual / CI |
| 10-REQ-7.3 | TS-10-P2 | (afspec unchanged) | manual / CI |
| 10-REQ-7.E1 | TS-10-P2 | 3.2 | manual / CI |

## Notes

- Use `git mv` for all file moves to preserve history.
- Run `uv sync` after updating pyproject.toml files to regenerate the
  lock file.
- The `test_afspec_validation.py` test belongs with the speclib library
  tests (it tests speclib's use of afspec, not afspec itself).
- Some property tests (P2, P5, P6) require subprocess-level verification
  and are better suited to CI integration tests than unit tests. They
  can be implemented as pytest tests using `subprocess.run` or verified
  manually during the restructure.
