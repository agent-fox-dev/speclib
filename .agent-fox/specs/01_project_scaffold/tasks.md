# Implementation Plan: Project Scaffold and Configuration

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

This plan establishes the speclib project from scratch: package structure,
build configuration, configuration loading, and Anthropic client factory.
Groups are ordered so the scaffold exists before tests can import anything.

## Test Commands

- Spec tests: `uv run pytest -q tests/test_config.py tests/test_auth.py tests/test_scaffold.py`
- Unit tests: `uv run pytest -q tests/`
- Property tests: `uv run pytest -q tests/ -k property`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check && uv run mypy speclib/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Set up test file structure
    - Create `tests/` directory with `__init__.py`
    - Create `tests/test_scaffold.py` for project structure tests (TS-01-1 through TS-01-6)
    - Create `tests/test_config.py` for configuration tests (TS-01-7 through TS-01-10, TS-01-P1, TS-01-P2)
    - Create `tests/test_auth.py` for auth client tests (TS-01-11 through TS-01-15, TS-01-P3)
    - Create `tests/conftest.py` with fixtures for temp dirs and env var patching
    - _Test Spec: TS-01-1 through TS-01-17_

  - [x] 1.2 Translate acceptance-criterion tests
    - One test function per TS-01-{N} entry
    - Tests MUST fail (modules don't exist yet)
    - _Test Spec: TS-01-1 through TS-01-17_

  - [x] 1.3 Translate edge-case tests
    - One test function per TS-01-E{N} entry
    - _Test Spec: TS-01-E1 through TS-01-E6_

  - [x] 1.4 Translate property tests
    - One property test per TS-01-P{N} entry using hypothesis
    - _Test Spec: TS-01-P1 through TS-01-P3_

  - [x] 1.5 Write integration smoke tests
    - TS-01-SMOKE-1 (config load end-to-end)
    - TS-01-SMOKE-2 (client creation end-to-end)
    - _Test Spec: TS-01-SMOKE-1, TS-01-SMOKE-2_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings introduced: `uv run ruff check tests/`

- [x] 2. Create project scaffold
  - [x] 2.1 Create pyproject.toml
    - Package name: speclib
    - requires-python: ">=3.14"
    - Dependencies: afspec, anthropic[vertex,bedrock], click, pyyaml
    - Dev dependencies: pytest, hypothesis, ruff, mypy
    - Build backend: hatchling
    - CLI entry point: spec = speclib.cli:main
    - Ruff and mypy configuration
    - _Requirements: 01-REQ-1.1, 01-REQ-1.2, 01-REQ-1.3, 01-REQ-1.4_

  - [x] 2.2 Create Makefile
    - `check` target: lint + test
    - `test` target: `uv run pytest -q`
    - `lint` target: `uv run ruff check && uv run mypy speclib/`
    - _Requirements: 01-REQ-1.5, 01-REQ-1.6_

  - [x] 2.3 Create package directory structure
    - `speclib/__init__.py` — package root with version and key re-exports
    - `speclib/errors.py` — SpeclibError, ConfigError
    - `speclib/config.py` — placeholder (implemented in group 3)
    - `speclib/auth.py` — placeholder (implemented in group 3)
    - `speclib/cli.py` — minimal Click group for entry point (expanded in spec 04)
    - _Requirements: 01-REQ-4.1, 01-REQ-4.2_

  - [x] 2.4 Run uv sync to install dependencies
    - Verify `uv sync` succeeds
    - Verify `uv run spec --help` works
    - _Requirements: 01-REQ-1.1_

  - [x] 2.V Verify task group 2
    - [x] Scaffold tests pass (TS-01-1 through TS-01-6): `uv run pytest -q tests/test_scaffold.py`
    - [x] Exception hierarchy tests pass (TS-01-16, TS-01-17)
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check`

- [x] 3. Implement configuration and auth modules
  - [x] 3.1 Implement speclib/config.py
    - `SpecToolConfig` dataclass with defaults
    - `load_config()` function: read YAML, parse spec_tool, apply env var overrides
    - Support for nested `auth` section in YAML
    - _Requirements: 01-REQ-2.1, 01-REQ-2.2, 01-REQ-2.3, 01-REQ-2.4_

  - [x] 3.2 Implement speclib/auth.py
    - `create_client()` function: resolve auth method, create appropriate client
    - `_create_api_key_client()`, `_create_bedrock_client()`, `_create_vertex_client()` helpers
    - Return (client, model_name) tuple
    - _Requirements: 01-REQ-3.1, 01-REQ-3.2, 01-REQ-3.3, 01-REQ-3.4, 01-REQ-3.5_

  - [x] 3.3 Handle all error conditions
    - Invalid YAML → ConfigError
    - Missing spec_tool → defaults
    - Unknown keys → ignore
    - Bad auth method → ConfigError with valid list
    - Missing API key → ConfigError
    - Missing Vertex project → ConfigError
    - _Requirements: 01-REQ-2.E1, 01-REQ-2.E2, 01-REQ-2.E3, 01-REQ-3.E1, 01-REQ-3.E2, 01-REQ-3.E3_

  - [x] 3.V Verify task group 3
    - [x] Config tests pass: `uv run pytest -q tests/test_config.py`
    - [x] Auth tests pass: `uv run pytest -q tests/test_auth.py`
    - [x] Property tests pass: `uv run pytest -q tests/ -k property`
    - [x] Smoke tests pass: `uv run pytest -q tests/ -k smoke`
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check && uv run mypy speclib/`

- [x] 4. Checkpoint - Scaffold Complete
  - Ensure all tests pass
  - Update `speclib/__init__.py` to export `SpecToolConfig`, `load_config`, `create_client`, `SpeclibError`, `ConfigError`
  - Update `README.md` with installation instructions (uv-only) and configuration docs

- [x] 5. Wiring verification

  - [x] 5.1 Trace every execution path from design.md end-to-end
    - Path 1: `load_config` reads YAML → applies env overrides → returns SpecToolConfig
    - Path 2: `create_client` → `load_config` (if no config) → selects auth method → creates client → returns tuple
    - Verify each function in the chain is actually called by the previous one
    - _Requirements: all_

  - [x] 5.2 Verify return values propagate correctly
    - `load_config()` returns SpecToolConfig consumed by `create_client()`
    - `create_client()` returns (client, model) tuple consumed by callers
    - _Requirements: all_

  - [x] 5.3 Run the integration smoke tests
    - All TS-01-SMOKE-* tests pass with real components
    - _Test Spec: TS-01-SMOKE-1, TS-01-SMOKE-2_

  - [x] 5.4 Stub / dead-code audit
    - Search speclib/ for `return []`, `return None` on non-Optional returns, `pass`, `# TODO`, `NotImplementedError`
    - Each hit must be justified or replaced
    - CLI placeholder (`speclib/cli.py`) is expected to be minimal — document as intentional

  - [x] 5.5 Cross-spec entry point verification
    - No cross-spec entry points in this foundational spec
    - Verify `create_client` and `load_config` are importable from `speclib`
    - _Requirements: all_

  - [x] 5.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain in speclib/
    - [x] All execution paths from design.md are live
    - [x] All existing tests still pass: `uv run pytest -q`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 01-REQ-1.1 | TS-01-1 | 2.1, 2.4 | tests/test_scaffold.py::test_installable |
| 01-REQ-1.2 | TS-01-2 | 2.1 | tests/test_scaffold.py::test_runtime_deps |
| 01-REQ-1.3 | TS-01-3 | 2.1 | tests/test_scaffold.py::test_dev_deps |
| 01-REQ-1.4 | TS-01-4 | 2.1 | tests/test_scaffold.py::test_python_version |
| 01-REQ-1.5 | TS-01-5 | 2.2 | tests/test_scaffold.py::test_make_check |
| 01-REQ-1.6 | TS-01-6 | 2.2 | tests/test_scaffold.py::test_make_test |
| 01-REQ-2.1 | TS-01-7 | 3.1 | tests/test_config.py::test_load_from_yaml |
| 01-REQ-2.2 | TS-01-8 | 3.1 | tests/test_config.py::test_env_overrides_yaml |
| 01-REQ-2.3 | TS-01-9 | 3.1 | tests/test_config.py::test_config_fields |
| 01-REQ-2.4 | TS-01-10 | 3.1 | tests/test_config.py::test_defaults |
| 01-REQ-3.1 | TS-01-11 | 3.2 | tests/test_auth.py::test_api_key_client |
| 01-REQ-3.2 | TS-01-12 | 3.2 | tests/test_auth.py::test_bedrock_client |
| 01-REQ-3.3 | TS-01-13 | 3.2 | tests/test_auth.py::test_vertex_client |
| 01-REQ-3.4 | TS-01-14 | 3.2 | tests/test_auth.py::test_config_fallback |
| 01-REQ-3.5 | TS-01-15 | 3.2 | tests/test_auth.py::test_yaml_auth_method |
| 01-REQ-4.1 | TS-01-16 | 2.3 | tests/test_scaffold.py::test_speclib_error |
| 01-REQ-4.2 | TS-01-17 | 2.3 | tests/test_scaffold.py::test_config_error |
| 01-REQ-2.E1 | TS-01-E1 | 3.3 | tests/test_config.py::test_invalid_yaml |
| 01-REQ-2.E2 | TS-01-E2 | 3.3 | tests/test_config.py::test_missing_section |
| 01-REQ-2.E3 | TS-01-E3 | 3.3 | tests/test_config.py::test_unknown_keys |
| 01-REQ-3.E1 | TS-01-E4 | 3.3 | tests/test_auth.py::test_invalid_auth_method |
| 01-REQ-3.E2 | TS-01-E5 | 3.3 | tests/test_auth.py::test_missing_api_key |
| 01-REQ-3.E3 | TS-01-E6 | 3.3 | tests/test_auth.py::test_missing_vertex_project |
| Property 1 | TS-01-P1 | 3.1 | tests/test_config.py::test_property_env_overrides |
| Property 2 | TS-01-P2 | 3.1 | tests/test_config.py::test_property_defaults |
| Property 3 | TS-01-P3 | 3.2 | tests/test_auth.py::test_property_client_type |
| Path 1 | TS-01-SMOKE-1 | 3.1 | tests/test_config.py::test_smoke_config_load |
| Path 2 | TS-01-SMOKE-2 | 3.2 | tests/test_auth.py::test_smoke_client_creation |
| 01-REQ-1.E1 | TS-01-E7 | 2.1 | tests/test_scaffold.py::test_uv_required |

## Notes

- Auth client tests mock the `anthropic.Anthropic`, `AnthropicBedrock`, and
  `AnthropicVertex` constructors to avoid real API calls.
- Config tests use `tmp_path` fixtures with patched `Path.home()` to isolate
  settings file access.
- The CLI entry point (`spec`) is a minimal stub in this spec — spec 04
  implements the full command set.
