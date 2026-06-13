# Implementation Plan: Spec Analysis & Execution Planning

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

This spec adds the planning layer to the coder package. It reuses afspec
discovery and models, adding only the orchestration logic (parse, validate,
sort) and the ExecutionPlan data model. Implementation is 4 groups: tests,
data models, spec parsing, and the planner entry point.

## Test Commands

- Spec tests: `uv run pytest -q packages/coder/tests/test_planner.py packages/coder/tests/test_spec_parser.py packages/coder/tests/test_models.py -v`
- Unit tests: `uv run pytest -q packages/coder/tests/ -v -k "not smoke"`
- Property tests: `uv run pytest -q packages/coder/tests/ -v -k "property"`
- All tests: `uv run pytest -q packages/coder/tests/ -v`
- Linter: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Create test file structure
    - Create `packages/coder/tests/test_spec_parser.py`
    - Create `packages/coder/tests/test_planner.py`
    - Create `packages/coder/tests/test_models.py`
    - Add fixtures for test spec pack directories in conftest.py
    - _Test Spec: TS-13-1 through TS-13-10_

  - [x] 1.2 Translate acceptance-criterion tests
    - TS-13-1: Discover specs in campaign dir
    - TS-13-2: Specs sorted by numeric prefix
    - TS-13-3: Parse spec pack loads all artifacts
    - TS-13-4: Only active specs in plan
    - TS-13-5: Non-active spec logs warning
    - TS-13-6: Dependency ordering respected
    - TS-13-7: Cycle detection raises error
    - TS-13-8: Execution plan serializable
    - TS-13-9: Spec filter restricts plan
    - TS-13-10: Build plan logs steps
    - _Test Spec: TS-13-1 through TS-13-10_

  - [x] 1.3 Translate edge-case tests
    - TS-13-E1: Empty campaign directory
    - TS-13-E2: Non-spec folders ignored
    - TS-13-E3: Missing JSON artifact
    - TS-13-E4: Invalid JSON
    - TS-13-E5: Missing prd.md
    - TS-13-E6: External dependency treated as satisfied
    - TS-13-E7: Campaign directory does not exist
    - TS-13-E8: Missing status field treated as draft
    - _Test Spec: TS-13-E1 through TS-13-E8_

  - [x] 1.4 Translate property tests
    - TS-13-P1: Topological order respects all dependencies
    - TS-13-P2: Active-only filtering
    - TS-13-P3: Stable sort by numeric prefix
    - TS-13-P4: Cycle detection is reliable
    - _Test Spec: TS-13-P1 through TS-13-P4_

  - [x] 1.5 Translate integration smoke test
    - TS-13-SMOKE-1: Build plan from example specs
    - _Test Spec: TS-13-SMOKE-1_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings: `uv run ruff check packages/coder/tests/`

- [x] 2. Data models & custom exceptions
  - [x] 2.1 Implement data models
    - Create/update `packages/coder/coder/models.py`
    - Implement `ParsedSpec` frozen pydantic model
    - Implement `ExecutionPlan` frozen pydantic model with
      `model_dump_json()` support
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 2.2 Add planning-related exceptions
    - Add `SpecParseError` and `DependencyCycleError` to
      `packages/coder/coder/errors.py`
    - _Requirements: 2.E1, 2.E2, 4.3_

  - [x] 2.V Verify task group 2
    - [x] Spec tests pass: TS-13-8
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [x] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [x] Requirements 5.1-5.3 met

- [x] 3. Spec parser & planner
  - [x] 3.1 Implement SpecParser
    - Create `packages/coder/coder/spec_parser.py`
    - Implement `parse(meta)` method that loads all JSON artifacts
      using afspec I/O
    - Handle missing `prd.md` gracefully
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.2 Implement build_execution_plan
    - Create `packages/coder/coder/planner.py`
    - Implement discovery → parse → validate → sort → plan pipeline
    - Use `afspec.discovery.discover_specs()` for discovery
    - Use `afspec.discovery.build_dependency_graph()` for deps
    - Implement topological sort with stable numeric prefix ordering
    - Implement `spec_filter` parameter
    - Add logging at each step
    - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.E1, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2_

  - [x] 3.V Verify task group 3
    - [x] Spec tests pass: TS-13-1 through TS-13-10
    - [x] Edge case tests pass: TS-13-E1 through TS-13-E8
    - [x] Property tests pass: TS-13-P1 through TS-13-P4
    - [x] Smoke test pass: TS-13-SMOKE-1
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [x] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [x] Requirements 1.1-6.2 met

- [x] 4. Wiring verification

  - [x] 4.1 Trace every execution path from design.md end-to-end
    - Path 1: build_execution_plan → discover → parse → filter → sort → plan
    - Verify each function call is real (not stubbed)
    - _Requirements: all_

  - [x] 4.2 Verify return values propagate correctly
    - `discover_specs()` → `list[SpecMeta]` consumed by parser
    - `SpecParser.parse()` → `ParsedSpec` consumed by planner
    - `build_execution_plan()` → `ExecutionPlan` consumed by caller
    - _Requirements: all_

  - [x] 4.3 Run the integration smoke tests
    - TS-13-SMOKE-1: Build plan from example specs (real filesystem)
    - _Test Spec: TS-13-SMOKE-1_

  - [x] 4.4 Stub / dead-code audit
    - Search `packages/coder/coder/planner.py` and `spec_parser.py` for
      stubs, TODOs, or dead code
    - _Requirements: all_

  - [x] 4.5 Cross-spec entry point verification
    - Verify `build_execution_plan()` is callable from the CLI (spec 12)
    - Verify `ExecutionPlan` is importable by spec 14 code
    - _Requirements: all_

  - [x] 4.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain
    - [x] All execution paths from design.md are live
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 13-REQ-1.1 | TS-13-1 | 3.2 | test_planner.py::test_discover_specs |
| 13-REQ-1.3 | TS-13-2 | 3.2 | test_planner.py::test_sorted_by_prefix |
| 13-REQ-1.E1 | TS-13-E1 | 3.2 | test_planner.py::test_empty_campaign |
| 13-REQ-1.E2 | TS-13-E2 | 3.2 | test_planner.py::test_non_spec_ignored |
| 13-REQ-2.1 | TS-13-3 | 3.1 | test_spec_parser.py::test_parse_all |
| 13-REQ-2.2 | TS-13-3 | 3.1 | test_spec_parser.py::test_parse_all |
| 13-REQ-2.3 | TS-13-3 | 3.1 | test_spec_parser.py::test_parse_all |
| 13-REQ-2.4 | TS-13-3 | 3.1 | test_spec_parser.py::test_parse_all |
| 13-REQ-2.5 | TS-13-3 | 3.1 | test_spec_parser.py::test_parse_all |
| 13-REQ-2.E1 | TS-13-E3 | 3.1 | test_spec_parser.py::test_missing_json |
| 13-REQ-2.E2 | TS-13-E4 | 3.1 | test_spec_parser.py::test_invalid_json |
| 13-REQ-2.E3 | TS-13-E5 | 3.1 | test_spec_parser.py::test_missing_prd |
| 13-REQ-3.1 | TS-13-4 | 3.2 | test_planner.py::test_active_only |
| 13-REQ-3.2 | TS-13-5 | 3.2 | test_planner.py::test_skip_warning |
| 13-REQ-3.3 | TS-13-4 | 3.2 | test_planner.py::test_active_only |
| 13-REQ-4.2 | TS-13-6 | 3.2 | test_planner.py::test_dependency_order |
| 13-REQ-4.3 | TS-13-7 | 3.2 | test_planner.py::test_cycle_detection |
| 13-REQ-4.4 | TS-13-P3 | 3.2 | test_planner.py::test_property_stable_sort |
| 13-REQ-4.E1 | TS-13-E6 | 3.2 | test_planner.py::test_external_dep |
| 13-REQ-5.1 | TS-13-8 | 2.1 | test_models.py::test_plan_serializable |
| 13-REQ-5.3 | TS-13-8 | 2.1 | test_models.py::test_plan_serializable |
| 13-REQ-6.1 | TS-13-10 | 3.2 | test_planner.py::test_logs_steps |
| 13-REQ-6.2 | TS-13-9 | 3.2 | test_planner.py::test_spec_filter |
| 13-REQ-6.E1 | TS-13-E7 | 3.2 | test_planner.py::test_missing_dir |
| 13-REQ-1.2 | TS-13-1 | 3.2 | test_planner.py::test_discover_specs |
| 13-REQ-3.E1 | TS-13-E8 | 3.2 | test_planner.py::test_missing_status_treated_as_draft |
| 13-REQ-4.1 | TS-13-6 | 3.2 | test_planner.py::test_dependency_order |
| 13-REQ-5.2 | TS-13-3 | 3.1 | test_spec_parser.py::test_parse_all |
| 13-REQ-4.E2 | TS-13-E9 | 3.2 | test_planner.py::test_no_deps_prefix_order |
| 13-REQ-5.E1 | TS-13-E10 | 3.2 | test_planner.py::test_empty_plan_zero_count |

## Notes

- Test fixtures should create minimal valid spec pack directories with
  just enough JSON content to parse successfully.
- The example spec packs in `examples/golang_service/service_mvp/` are
  used for the smoke test — ensure they remain valid.
- Property tests for topological sort should use Hypothesis to generate
  random DAGs with `graphlib.TopologicalSorter` as the oracle.
