# Implementation Plan: Campaign Management and Spec Authoring Session Model

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

This plan implements the campaign directory management and spec authoring
session model. Groups 1-2 write all failing tests. Groups 3-5 implement the
production code to make those tests pass. Group 6 verifies wiring
end-to-end. This spec depends on spec 01 (group 2) for the package
structure and error hierarchy (`SpeclibError`).

## Test Commands

- Spec tests: `uv run pytest -q tests/test_campaign.py tests/test_session.py`
- Unit tests: `uv run pytest -q tests/`
- Property tests: `uv run pytest -q tests/ -k property`
- Smoke tests: `uv run pytest -q tests/ -k smoke`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check && uv run mypy speclib/`

## Tasks

- [x] 1. Write failing spec tests — campaign and acceptance criteria
  - [x] 1.1 Create test files and fixtures
    - Create `tests/test_campaign.py` for campaign tests (TS-02-1 through TS-02-9, TS-02-E1 through TS-02-E6)
    - Create `tests/test_session.py` for session tests (TS-02-10 through TS-02-19, TS-02-E7 through TS-02-E11)
    - Add fixtures to `tests/conftest.py`: `tmp_campaign_dir`, `campaign`, `session`, `session_with_artifacts`
    - _Test Spec: TS-02-1 through TS-02-19_

  - [x] 1.2 Translate campaign acceptance-criterion tests
    - One test function per TS-02-{1..9}
    - _Test Spec: TS-02-1 through TS-02-9_

  - [x] 1.3 Translate session acceptance-criterion tests
    - One test function per TS-02-{10..19}
    - _Test Spec: TS-02-10 through TS-02-19_

  - [x] 1.4 Translate edge-case tests
    - One test function per TS-02-E{1..11}
    - _Test Spec: TS-02-E1 through TS-02-E11_

  - [x] 1.V Verify task group 1
    - [x] All acceptance and edge-case tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings introduced: `uv run ruff check tests/`

- [x] 2. Write failing spec tests — properties and smoke tests
  - [x] 2.1 Translate property tests
    - `test_property_state_machine_total` (TS-02-P1) — hypothesis over states and methods
    - `test_property_persistence_idempotent` (TS-02-P2)
    - `test_property_numbering_monotonic` (TS-02-P3)
    - `test_property_create_atomic` (TS-02-P4)
    - `test_property_artifacts_required` (TS-02-P5)
    - `test_property_accept_prd_states` (TS-02-P6)
    - _Test Spec: TS-02-P1 through TS-02-P6_

  - [x] 2.2 Write integration smoke tests
    - `test_smoke_campaign_to_spec_creation` (TS-02-SMOKE-1)
    - `test_smoke_open_and_list_specs` (TS-02-SMOKE-2)
    - `test_smoke_session_lifecycle` (TS-02-SMOKE-3)
    - `test_smoke_session_resume` (TS-02-SMOKE-4)
    - `test_smoke_validate_and_render` (TS-02-SMOKE-5)
    - _Test Spec: TS-02-SMOKE-1 through TS-02-SMOKE-5_

  - [x] 2.V Verify task group 2
    - [x] All property and smoke tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings introduced: `uv run ruff check tests/`

- [x] 3. Implement error types and data models
  - [x] 3.1 Add CampaignError and SessionError to speclib/errors.py
    - `CampaignError(SpeclibError)` — campaign directory operation failures
    - `SessionError(SpeclibError)` — session state machine or persistence failures
    - _Requirements: 02-REQ-4.3, 02-REQ-1.2, 02-REQ-2.E1_

  - [x] 3.2 Create speclib/session.py — data models only
    - `SessionState` enum with six values
    - `Question` dataclass
    - `Assessment` dataclass
    - `RepairSuggestion` dataclass
    - `ValidationResult` dataclass
    - `GenerateResult` dataclass
    - _Requirements: 02-REQ-4.1, 02-REQ-5.3_

  - [x] 3.3 Create speclib/campaign.py — CampaignMetadata only
    - `CampaignMetadata` dataclass with name, description, created_at, updated_at
    - _Requirements: 02-REQ-1.3_

  - [x] 3.4 Update speclib/__init__.py with new exports
    - Export: `CampaignError`, `SessionError`, `SessionState`, `Campaign`, `SpecSession`
    - Export data types: `CampaignMetadata`, `Assessment`, `Question`, `ValidationResult`, `GenerateResult`, `RepairSuggestion`
    - _Requirements: all_

  - [x] 3.V Verify task group 3
    - [x] SessionState enum test passes (TS-02-10)
    - [x] Error type tests pass (import and isinstance checks)
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check`

- [x] 4. Implement Campaign class
  - [x] 4.1 Implement Campaign.create()
    - Validate path: parent must exist, target must be empty or non-existent
    - Create directory if needed
    - Write campaign.yaml with CampaignMetadata
    - Return Campaign instance
    - _Requirements: 02-REQ-1.1, 02-REQ-1.2, 02-REQ-1.E1, 02-REQ-1.E2_

  - [x] 4.2 Implement Campaign.open()
    - Check campaign.yaml exists
    - Parse YAML into CampaignMetadata
    - Handle invalid YAML with CampaignError
    - Return Campaign instance
    - _Requirements: 02-REQ-2.1, 02-REQ-2.E1, 02-REQ-2.E2_

  - [x] 4.3 Implement campaign.specs()
    - Scan directory for `{NN}_{snake_case}` pattern
    - Sort by numeric prefix
    - Exclude `archive/`, `_session.json`, non-matching entries
    - Return list of Path objects
    - _Requirements: 02-REQ-2.2_

  - [x] 4.4 Implement campaign.new_spec()
    - Validate spec_name against `[a-z][a-z0-9_]*`
    - Compute next numeric prefix
    - Create spec directory
    - Write prd.md (from string with frontmatter, or copy from Path)
    - Write initial _session.json
    - Update campaign.yaml updated_at
    - Return SpecSession instance
    - _Requirements: 02-REQ-3.1, 02-REQ-3.2, 02-REQ-3.3, 02-REQ-3.4, 02-REQ-3.E1, 02-REQ-3.E2_

  - [x] 4.5 Implement campaign.path and campaign.metadata properties
    - _Requirements: 02-REQ-1.1, 02-REQ-2.1_

  - [x] 4.V Verify task group 4
    - [x] Campaign tests pass: `uv run pytest -q tests/test_campaign.py`
    - [x] Campaign edge case tests pass (TS-02-E1 through TS-02-E6)
    - [x] Campaign property tests pass (TS-02-P3, TS-02-P4)
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check && uv run mypy speclib/`

- [x] 5. Implement SpecSession class
  - [x] 5.1 Implement session state machine core
    - Define legal transitions as a dict/set
    - Implement `_transition(target_state)` method that checks legality and persists
    - Raise SessionError with current and required state on illegal transitions
    - _Requirements: 02-REQ-4.2, 02-REQ-4.3_

  - [x] 5.2 Implement session persistence
    - `_persist()` method: atomically write _session.json
    - Include state, prd_path, assessment_history, qa_exchanges, generated_artifacts, mode
    - Call _persist() on every state transition
    - _Requirements: 02-REQ-5.1, 02-REQ-5.3_

  - [x] 5.3 Implement SpecSession.resume()
    - Read _session.json
    - Deserialize state, history, exchanges
    - Handle missing file (SessionError)
    - Handle invalid JSON (SessionError with parse detail)
    - Return SpecSession in persisted state
    - _Requirements: 02-REQ-5.2, 02-REQ-5.E1, 02-REQ-5.E2_

  - [x] 5.4 Implement session methods (stubs and non-stubs)
    - `assess()`: check state allows transition init->assessing, then raise NotImplementedError
    - `refine(answers)`: check state allows transition assessing->refining, then raise NotImplementedError
    - `accept_prd()`: check state is init, assessing, or refining, transition to prd_accepted
    - `generate()`: check state is prd_accepted, transition to generating, then raise NotImplementedError
    - `validate()`: check all four artifacts exist, delegate to afspec
    - `render(combined)`: check all four artifacts exist, delegate to afspec
    - _Requirements: 02-REQ-4.4, 02-REQ-4.E1, 02-REQ-4.E2, 02-REQ-6.1, 02-REQ-6.2, 02-REQ-6.3, 02-REQ-6.E1_

  - [x] 5.5 Implement session properties
    - `state` -> SessionState
    - `spec_dir` -> Path
    - `assessment` -> Assessment | None (from assessment_history)
    - _Requirements: 02-REQ-4.1_

  - [x] 5.V Verify task group 5
    - [x] Session tests pass: `uv run pytest -q tests/test_session.py`
    - [x] Session edge case tests pass (TS-02-E7 through TS-02-E11)
    - [x] Session property tests pass (TS-02-P1, TS-02-P2, TS-02-P5, TS-02-P6)
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check && uv run mypy speclib/`

- [x] 6. Wiring verification

  - [x] 6.1 Trace every execution path from design.md end-to-end
    - Path 1: `Campaign.create` -> validate path -> create dir -> write YAML -> return Campaign
    - Path 2: `Campaign.open` -> check YAML -> parse -> return Campaign; `specs()` -> scan -> sort -> return
    - Path 3: `campaign.new_spec` -> validate name -> compute prefix -> create dir -> write prd.md -> write _session.json -> return SpecSession
    - Path 4: SpecSession `init -> assessing -> refining -> prd_accepted -> generating -> generated` (stubs raise NotImplementedError after state check)
    - Path 5: `SpecSession.resume` -> read _session.json -> deserialize -> return SpecSession
    - Path 6: `session.validate` -> check artifacts -> afspec.load_spec -> afspec.validate -> return ValidationResult
    - Verify each function in the chain is actually called by the previous one
    - _Requirements: all_

  - [x] 6.2 Verify return values propagate correctly
    - `Campaign.create()` returns Campaign consumed by callers
    - `campaign.new_spec()` returns SpecSession consumed by callers
    - `session.validate()` returns ValidationResult
    - `session.render()` returns str or dict
    - _Requirements: all_

  - [x] 6.3 Run the integration smoke tests
    - All TS-02-SMOKE-* tests pass with real components
    - _Test Spec: TS-02-SMOKE-1 through TS-02-SMOKE-5_

  - [x] 6.4 Stub / dead-code audit
    - Search speclib/campaign.py and speclib/session.py for `return []`, `return None` on non-Optional returns, `pass`, `# TODO`, `NotImplementedError`
    - Each hit must be justified or replaced
    - `assess()`, `refine()`, `generate()` raising NotImplementedError is expected and documented — note as intentional (spec 03 provides implementation)

  - [x] 6.5 Cross-spec entry point verification
    - Verify `Campaign` and `SpecSession` are importable from `speclib`
    - Verify `CampaignError` and `SessionError` are importable from `speclib.errors`
    - Verify `CampaignMetadata`, `SessionState`, `Assessment`, `Question`, `ValidationResult`, `GenerateResult`, `RepairSuggestion` are importable
    - Confirm spec 03 can subclass or wrap `assess()` and `generate()` — verify method signatures match the interface in design.md

  - [x] 6.V Verify wiring group
    - [x] All smoke tests pass: `uv run pytest -q tests/ -k smoke`
    - [x] No unjustified stubs remain in speclib/campaign.py or speclib/session.py
    - [x] All execution paths from design.md are live
    - [x] All existing tests still pass: `uv run pytest -q`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 02-REQ-1.1 | TS-02-1 | 4.1 | tests/test_campaign.py::test_campaign_create |
| 02-REQ-1.2 | TS-02-2 | 4.1 | tests/test_campaign.py::test_campaign_create_fails_existing |
| 02-REQ-1.3 | TS-02-3 | 3.3, 4.1 | tests/test_campaign.py::test_campaign_yaml_fields |
| 02-REQ-2.1 | TS-02-4 | 4.2 | tests/test_campaign.py::test_campaign_open |
| 02-REQ-2.2 | TS-02-5 | 4.3 | tests/test_campaign.py::test_campaign_specs_sorted |
| 02-REQ-3.1 | TS-02-6 | 4.4 | tests/test_campaign.py::test_new_spec_string_prd |
| 02-REQ-3.2 | TS-02-7 | 4.4 | tests/test_campaign.py::test_new_spec_path_prd |
| 02-REQ-3.3 | TS-02-8 | 4.4 | tests/test_campaign.py::test_spec_dir_sequential_prefixes |
| 02-REQ-3.4 | TS-02-9 | 4.4 | tests/test_campaign.py::test_prd_frontmatter |
| 02-REQ-4.1 | TS-02-10 | 3.2 | tests/test_session.py::test_session_state_enum |
| 02-REQ-4.2 | TS-02-11 | 5.1 | tests/test_session.py::test_legal_state_transitions |
| 02-REQ-4.3 | TS-02-12 | 5.1 | tests/test_session.py::test_illegal_transition_error_message |
| 02-REQ-4.4 | TS-02-13 | 5.4 | tests/test_session.py::test_accept_prd_from_assessing_and_refining |
| 02-REQ-5.1 | TS-02-14 | 5.2 | tests/test_session.py::test_state_persisted_on_transition |
| 02-REQ-5.2 | TS-02-15 | 5.3 | tests/test_session.py::test_session_resume |
| 02-REQ-5.3 | TS-02-16 | 5.2 | tests/test_session.py::test_session_json_fields |
| 02-REQ-6.1 | TS-02-17 | 5.4 | tests/test_session.py::test_validate_with_artifacts |
| 02-REQ-6.2 | TS-02-18 | 5.4 | tests/test_session.py::test_render_combined |
| 02-REQ-6.3 | TS-02-19 | 5.4 | tests/test_session.py::test_render_individual |
| 02-REQ-1.E1 | TS-02-E1 | 4.1 | tests/test_campaign.py::test_create_non_empty_non_campaign |
| 02-REQ-1.E2 | TS-02-E2 | 4.1 | tests/test_campaign.py::test_create_parent_missing |
| 02-REQ-2.E1 | TS-02-E3 | 4.2 | tests/test_campaign.py::test_open_no_campaign_yaml |
| 02-REQ-2.E2 | TS-02-E4 | 4.2 | tests/test_campaign.py::test_open_invalid_yaml |
| 02-REQ-3.E1 | TS-02-E5 | 4.4 | tests/test_campaign.py::test_new_spec_invalid_name |
| 02-REQ-3.E2 | TS-02-E6 | 4.4 | tests/test_campaign.py::test_new_spec_nonexistent_prd_path |
| 02-REQ-4.E1 | TS-02-E7 | 5.1 | tests/test_session.py::test_generate_from_wrong_state |
| 02-REQ-4.E2 | TS-02-E8 | 5.1 | tests/test_session.py::test_assess_from_generated |
| 02-REQ-5.E1 | TS-02-E9 | 5.3 | tests/test_session.py::test_resume_no_session_json |
| 02-REQ-5.E2 | TS-02-E10 | 5.3 | tests/test_session.py::test_resume_invalid_json |
| 02-REQ-6.E1 | TS-02-E11 | 5.4 | tests/test_session.py::test_validate_render_missing_artifacts |
| Property 1 | TS-02-P1 | 5.1 | tests/test_session.py::test_property_state_machine_total |
| Property 2 | TS-02-P2 | 5.2, 5.3 | tests/test_session.py::test_property_persistence_idempotent |
| Property 3 | TS-02-P3 | 4.4 | tests/test_campaign.py::test_property_numbering_monotonic |
| Property 4 | TS-02-P4 | 4.1 | tests/test_campaign.py::test_property_create_atomic |
| Property 5 | TS-02-P5 | 5.4 | tests/test_session.py::test_property_artifacts_required |
| Property 6 | TS-02-P6 | 5.4 | tests/test_session.py::test_property_accept_prd_states |
| Path 1+3 | TS-02-SMOKE-1 | 4.1, 4.4 | tests/test_campaign.py::test_smoke_campaign_to_spec_creation |
| Path 2 | TS-02-SMOKE-2 | 4.2, 4.3 | tests/test_campaign.py::test_smoke_open_and_list_specs |
| Path 4 | TS-02-SMOKE-3 | 5.1, 5.4 | tests/test_session.py::test_smoke_session_lifecycle |
| Path 5 | TS-02-SMOKE-4 | 5.3 | tests/test_session.py::test_smoke_session_resume |
| Path 6 | TS-02-SMOKE-5 | 5.4 | tests/test_session.py::test_smoke_validate_and_render |

## Notes

- All campaign and session tests use `tmp_path` fixtures to avoid filesystem
  side effects.
- `assess()`, `refine()`, and `generate()` raise `NotImplementedError` in this
  spec — they are stubs for the state machine. Spec 03 provides the agent
  implementations that replace these stubs.
- Session state machine tests use Hypothesis to generate random sequences of
  method calls and verify that every outcome is either a successful transition
  or a `SessionError`.
- The `validate()` and `render()` methods delegate to `afspec.load_spec()`,
  `afspec.validate()`, and `afspec.render_*()` — tests mock these at the
  afspec boundary.
