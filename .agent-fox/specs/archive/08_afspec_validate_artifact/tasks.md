# Implementation Plan: afspec.validate_artifact

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

Implements `validate_artifact()` in the local `afspec` stub package by
bundling JSON schemas from `speclib-python` and validating artifact dicts
using the `jsonschema` library. Then removes the graceful skip in
`speclib/agent.py`.

## Test Commands

- Spec tests: `uv run pytest -q tests/test_afspec_validation.py`
- Unit tests: `uv run pytest -q tests/`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check speclib/ tests/ packages/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Create `tests/test_afspec_validation.py`
    - Test `validate_artifact` is importable (TS-08-1)
    - Test valid content passes (TS-08-2)
    - Test invalid content raises ValidationError (TS-08-3)
    - Test all three artifact names accepted (TS-08-4)
    - Test schemas are loadable (TS-08-5)
    - Test ValidationError attributes (TS-08-7)
    - _Test Spec: TS-08-1 through TS-08-5, TS-08-7_

  - [x] 1.2 Add edge case tests
    - Test unknown artifact name raises ValueError (TS-08-E1)
    - Test empty dict fails required fields (TS-08-E2)
    - _Test Spec: TS-08-E1, TS-08-E2_

  - [x] 1.3 Add property tests
    - Valid content passes (TS-08-P1)
    - Invalid content fails (TS-08-P2)
    - Name-schema bijection (TS-08-P3)
    - Error detail preservation (TS-08-P4)
    - _Test Spec: TS-08-P1 through TS-08-P4_

  - [x] 1.4 Add agent wrapper test and smoke test
    - Test agent wrapper calls afspec directly (TS-08-6)
    - End-to-end smoke test (TS-08-SMOKE-1)
    - _Test Spec: TS-08-6, TS-08-SMOKE-1_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings introduced: `uv run ruff check tests/`

- [x] 2. Bundle JSON schemas
  - [x] 2.1 Copy schema files from speclib-python
    - Copy `requirements.v1.json`, `test_spec.v1.json`, `tasks.v1.json`
      from `~/devel/workspace/speclib-python/afspec/schemas/` to
      `packages/afspec/afspec/schemas/`
    - Create `packages/afspec/afspec/schemas/__init__.py` (empty or with
      schema loading helper)
    - _Requirements: 08-REQ-2.1, 08-REQ-2.2_

  - [x] 2.2 Add `jsonschema` dependency to stub package
    - Update `packages/afspec/pyproject.toml` to add `jsonschema` dep
    - Run `uv sync` to install
    - _Requirements: 08-REQ-1.3_

  - [x] 2.V Verify task group 2
    - [x] Schema files exist and parse as valid JSON
    - [x] `jsonschema` is importable: `uv run python -c "import jsonschema"`
    - [x] No linter warnings introduced

- [x] 3. Implement validate_artifact and wire into agent
  - [x] 3.1 Create `packages/afspec/afspec/validation.py`
    - Implement `ValidationError` class with `artifact_name` and `errors`
    - Implement `validate_artifact()` with schema loading and validation
    - Implement `_load_schema()` helper using `importlib.resources`
    - _Requirements: 08-REQ-1.1 through 08-REQ-1.4, 08-REQ-4.1, 08-REQ-4.2_

  - [x] 3.2 Export from `packages/afspec/afspec/__init__.py`
    - Export `validate_artifact` and `ValidationError`
    - _Requirements: 08-REQ-1.1_

  - [x] 3.3 Remove graceful skip in `speclib/agent.py`
    - Replace `getattr(afspec, "validate_artifact", None)` with direct call
    - _Requirements: 08-REQ-3.1_

  - [x] 3.V Verify task group 3
    - [x] Spec tests pass: `uv run pytest -q tests/test_afspec_validation.py`
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings: `uv run ruff check speclib/ tests/ packages/`
    - [x] Requirements 08-REQ-1.*, 08-REQ-2.*, 08-REQ-3.*, 08-REQ-4.* met

- [x] 4. Wiring verification
  - [x] 4.1 Trace every execution path from design.md end-to-end
    - Path 1 (valid artifact): verify `agent.validate_artifact` →
      `afspec.validate_artifact` → schema load → jsonschema → return None
    - Path 2 (invalid artifact): verify raises chain through to AgentError
    - Path 3 (unknown name): verify ValueError raised
    - _Requirements: all_

  - [x] 4.2 Verify return values propagate correctly
    - `validate_artifact` returns None on success
    - `ValidationError` propagates to `AgentError` in agent.py
    - _Requirements: all_

  - [x] 4.3 Run the integration smoke tests
    - TS-08-SMOKE-1 passes with real schemas
    - _Test Spec: TS-08-SMOKE-1_

  - [x] 4.4 Stub / dead-code audit
    - Verify no `getattr` fallback remains in `speclib/agent.py`
    - Verify stub `__init__.py` has no dead exports
    - _Requirements: all_

  - [x] 4.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain in touched files
    - [x] All execution paths from design.md are live
    - [x] All existing tests still pass: `uv run pytest -q`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 08-REQ-1.1 | TS-08-1 | 3.1, 3.2 | test_validate_artifact_importable |
| 08-REQ-1.2 | TS-08-2 | 3.1 | test_valid_artifact_passes |
| 08-REQ-1.3 | TS-08-3 | 3.1 | test_invalid_artifact_raises |
| 08-REQ-1.4 | TS-08-4 | 3.1 | test_all_artifact_names |
| 08-REQ-1.E1 | TS-08-E1 | 3.1 | test_unknown_artifact_name |
| 08-REQ-1.E2 | TS-08-E2 | 3.1 | test_empty_dict_fails |
| 08-REQ-2.1 | TS-08-5 | 2.1 | test_schemas_loadable |
| 08-REQ-2.2 | TS-08-5 | 2.1 | test_schemas_loadable |
| 08-REQ-3.1 | TS-08-6 | 3.3 | test_agent_wrapper_direct_call |
| 08-REQ-4.1 | TS-08-7 | 3.1 | test_validation_error_attributes |
| 08-REQ-4.2 | TS-08-7 | 3.1 | test_validation_error_attributes |
| Property 1 | TS-08-P1 | 3.1 | test_valid_content_property |
| Property 2 | TS-08-P2 | 3.1 | test_invalid_content_property |
| Property 3 | TS-08-P3 | 3.1 | test_name_schema_bijection |
| Property 4 | TS-08-P4 | 3.1 | test_error_detail_preservation |
| Path 1 | TS-08-SMOKE-1 | 4.3 | test_validate_artifact_smoke |

## Notes

- Schema files are copied once from `speclib-python` — they are static
  assets, not generated. If upstream schemas change, manually re-copy.
- The `jsonschema` dependency is added only to the stub package
  (`packages/afspec/pyproject.toml`), not to the main `speclib` package.
- Valid artifact fixtures for testing should be derived from the JSON
  schemas' `required` and `properties` sections.
