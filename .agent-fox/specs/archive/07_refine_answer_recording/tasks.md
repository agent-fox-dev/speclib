# Implementation Plan: Refine Answer Recording

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

This feature populates the existing `qa_exchanges` field in `_session.json`
during `SpecSession.refine()`. The change is confined to `speclib/session.py`
(adding ~10 lines of production code) plus tests. No CLI or agent changes.

## Test Commands

- Spec tests: `uv run pytest -q tests/test_session.py -k "qa_exchange"`
- Unit tests: `uv run pytest -q tests/`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check speclib/ tests/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Add QA exchange recording tests to `tests/test_session.py`
    - Test refine appends entry with correct keys (TS-07-1)
    - Test entry persisted to disk (TS-07-2)
    - Test assessment_index is correct (TS-07-3)
    - Test entry schema (TS-07-4)
    - Test timestamp uses patchable `_utcnow` (TS-07-5)
    - _Test Spec: TS-07-1 through TS-07-5_

  - [x] 1.2 Add no-side-effect tests
    - Test question export unchanged (TS-07-6)
    - Test pending_questions unaffected (TS-07-7)
    - _Test Spec: TS-07-6, TS-07-7_

  - [x] 1.3 Add edge case tests
    - Test failed refine does not record exchange (TS-07-E1)
    - Test existing empty qa_exchanges loads fine (TS-07-E2)
    - _Test Spec: TS-07-E1, TS-07-E2_

  - [x] 1.4 Add property tests
    - Exchange count matches refine count (TS-07-P1)
    - Assessment index consistency (TS-07-P2)
    - Exchange schema consistency (TS-07-P3)
    - Failed refine no-append (TS-07-P4)
    - _Test Spec: TS-07-P1 through TS-07-P4_

  - [x] 1.5 Add integration smoke test
    - Full refine through real session with mocked agent (TS-07-SMOKE-1)
    - _Test Spec: TS-07-SMOKE-1_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings introduced: `uv run ruff check tests/`

- [x] 2. Implement QA exchange recording in `SpecSession.refine()`
  - [x] 2.1 Add `_utcnow()` module-level function to `speclib/session.py`
    - Returns `datetime.now(timezone.utc).isoformat()`
    - Exists solely to be patchable in tests
    - _Requirements: 07-REQ-2.2_

  - [x] 2.2 Modify `SpecSession.refine()` to record answers
    - Capture `assessment_index = len(self._assessment_history) - 1` and
      `timestamp = _utcnow()` before the agent call
    - On success (after agent returns), append QA exchange entry to
      `self._qa_exchanges` before calling `_persist()`
    - On failure (AgentError), do NOT append — existing error path unchanged
    - _Requirements: 07-REQ-1.1, 07-REQ-1.2, 07-REQ-1.3, 07-REQ-1.E1_

  - [x] 2.V Verify task group 2
    - [x] Spec tests pass: `uv run pytest -q tests/test_session.py -k "qa_exchange"`
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check speclib/ tests/`
    - [x] Requirements 07-REQ-1.*, 07-REQ-2.*, 07-REQ-3.* met

- [x] 3. Wiring verification
  - [x] 3.1 Trace every execution path from design.md end-to-end
    - Path 1 (refine records answers): verify `refine()` → capture index →
      agent call → append qa_exchange → `_persist()` is live
    - Path 2 (failed refine): verify error path does not append
    - _Requirements: all_

  - [x] 3.2 Verify return values propagate correctly
    - `_utcnow()` return value flows into QA exchange `timestamp`
    - `assessment_index` computed correctly from `_assessment_history` length
    - _Requirements: all_

  - [x] 3.3 Run the integration smoke tests
    - TS-07-SMOKE-1 passes with real session
    - _Test Spec: TS-07-SMOKE-1_

  - [x] 3.4 Stub / dead-code audit
    - Search `session.py` for stubs, TODOs, NotImplementedError in
      touched methods
    - _Requirements: all_

  - [x] 3.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain in touched files
    - [x] All execution paths from design.md are live (traceable in code)
    - [x] All existing tests still pass: `uv run pytest -q`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 07-REQ-1.1 | TS-07-1 | 2.2 | test_refine_appends_qa_exchange |
| 07-REQ-1.2 | TS-07-2 | 2.2 | test_qa_exchange_persisted |
| 07-REQ-1.3 | TS-07-3 | 2.2 | test_assessment_index_correct |
| 07-REQ-1.E1 | TS-07-E1 | 2.2 | test_failed_refine_no_exchange |
| 07-REQ-1.E2 | TS-07-E2 | 2.2 | test_empty_qa_exchanges_loads |
| 07-REQ-2.1 | TS-07-4 | 2.2 | test_qa_exchange_schema |
| 07-REQ-2.2 | TS-07-5 | 2.1 | test_timestamp_patchable |
| 07-REQ-3.1 | TS-07-6 | — | test_question_export_unchanged |
| 07-REQ-3.2 | TS-07-7 | — | test_pending_questions_unaffected |
| Property 1 | TS-07-P1 | 2.2 | test_exchange_count_parity |
| Property 2 | TS-07-P2 | 2.2 | test_assessment_index_sequential |
| Property 3 | TS-07-P3 | 2.2 | test_exchange_schema_property |
| Property 4 | TS-07-P4 | 2.2 | test_failed_refine_no_append_property |
| Path 1 | TS-07-SMOKE-1 | 3.3 | test_refine_qa_exchange_smoke |

## Notes

- Only `speclib/session.py` needs production code changes (~10 lines).
- The `qa_exchanges` field is already persisted by `_persist()` — no
  serialization changes needed.
- Tests should use the existing `conftest_agent.py` fixtures for mocking
  the agent, and patch `_utcnow` for deterministic timestamps.
