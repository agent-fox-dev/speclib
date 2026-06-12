# Implementation Plan: Refine Question Export

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

This feature adds question-export mode to `spec refine`. Implementation is
split into three groups: failing tests, library method, and CLI wiring. The
change is small and self-contained — two files modified (`session.py`, `cli.py`)
plus one test file.

## Test Commands

- Spec tests: `uv run pytest -q tests/test_cli.py tests/test_session.py -k "refine or pending_questions"`
- Unit tests: `uv run pytest -q tests/`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check speclib/ tests/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Add `pending_questions()` unit tests to `tests/test_session.py`
    - Test returning questions from a session with assessment history
    - Test returning empty list when no assessment exists
    - Test default values for missing optional fields
    - _Test Spec: TS-06-P2, TS-06-P3, TS-06-E3_

  - [x] 1.2 Add CLI question-export tests to `tests/test_cli.py`
    - Test `refine` without `--answers` outputs JSON with questions and answers
    - Test each question has all required fields
    - Test answer template maps IDs to empty strings
    - Test error when no assessment exists
    - Test output with zero questions
    - _Test Spec: TS-06-1, TS-06-2, TS-06-3, TS-06-E1, TS-06-E2_

  - [x] 1.3 Add existing-behavior preservation tests
    - Test `refine` with `--answers` still calls `session.refine()`
    - Property test that `--answers` path never outputs question JSON
    - _Test Spec: TS-06-4, TS-06-P4_

  - [x] 1.4 Add answer template key parity property test
    - _Test Spec: TS-06-P1_

  - [x] 1.5 Add integration smoke test
    - Full path from CLI through real session resume to JSON output
    - Verify `_session.json` is unchanged after question export
    - _Test Spec: TS-06-SMOKE-1_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests PASS (implementation already existed)
    - [x] No linter warnings introduced: `uv run ruff check tests/`

- [x] 2. Implement `pending_questions()` and CLI question export
  - [x] 2.1 Add `pending_questions()` method to `SpecSession`
    - Read-only method, no state transition
    - Returns `list[dict[str, Any]]` from latest assessment
    - Returns empty list when no assessment history
    - Uses defaults for missing optional fields (matches `assessment` property)
    - _Requirements: 06-REQ-2.1, 06-REQ-2.2, 06-REQ-2.3, 06-REQ-2.E1_

  - [x] 2.2 Modify `refine_cmd` CLI handler
    - Change `--answers` from `required=True` to `required=False`
    - When `answers is None`: call `pending_questions()`, build JSON output,
      print to stdout
    - When `answers is not None`: existing flow unchanged
    - Handle no-assessment error case
    - _Requirements: 06-REQ-1.1, 06-REQ-1.2, 06-REQ-1.3, 06-REQ-1.4,
      06-REQ-1.E1, 06-REQ-1.E2_

  - [x] 2.V Verify task group 2
    - [x] Spec tests for this group pass: `uv run pytest -q tests/test_cli.py tests/test_session.py -k "refine or pending_questions"`
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check speclib/ tests/`
    - [x] Requirements 06-REQ-1.*, 06-REQ-2.* acceptance criteria met

- [x] 3. Wiring verification
  - [x] 3.1 Trace every execution path from design.md end-to-end
    - Path 1 (question export): verify `refine_cmd` → `SpecSession.resume` →
      `pending_questions()` → JSON output is live
    - Path 2 (answer submission): verify existing flow still works unchanged
    - _Requirements: all_

  - [x] 3.2 Verify return values propagate correctly
    - `pending_questions()` returns `list[dict]` → consumed by `refine_cmd`
      to build JSON output
    - _Requirements: all_

  - [x] 3.3 Run the integration smoke tests
    - `TS-06-SMOKE-1` passes with real session, no mocks
    - _Test Spec: TS-06-SMOKE-1_

  - [x] 3.4 Stub / dead-code audit
    - Search `session.py` and `cli.py` for stubs, TODOs, NotImplementedError
    - _Requirements: all_

  - [x] 3.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain in touched files
    - [x] All execution paths from design.md are live (traceable in code)
    - [x] All existing tests still pass: `uv run pytest -q`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 06-REQ-1.1 | TS-06-1 | 2.2 | test_refine_no_answers_outputs_json |
| 06-REQ-1.2 | TS-06-2 | 2.2 | test_refine_no_answers_question_fields |
| 06-REQ-1.3 | TS-06-3 | 2.2 | test_refine_no_answers_template |
| 06-REQ-1.4 | TS-06-4 | 2.2 | test_refine_with_answers_unchanged |
| 06-REQ-1.E1 | TS-06-E1 | 2.2 | test_refine_no_answers_no_assessment |
| 06-REQ-1.E2 | TS-06-E2 | 2.2 | test_refine_no_answers_zero_questions |
| 06-REQ-2.1 | TS-06-P2 | 2.1 | test_pending_questions_returns_dicts |
| 06-REQ-2.2 | TS-06-P2 | 2.1 | test_pending_questions_empty_history |
| 06-REQ-2.3 | TS-06-P3 | 2.1 | test_pending_questions_read_only |
| 06-REQ-2.E1 | TS-06-E3 | 2.1 | test_pending_questions_defaults |
| Property 1 | TS-06-P1 | 2.2 | test_answer_template_key_parity |
| Property 2 | TS-06-P2 | 2.1 | test_pending_questions_fidelity |
| Property 3 | TS-06-P3 | 2.1 | test_pending_questions_read_only |
| Property 4 | TS-06-P4 | 2.2 | test_refine_with_answers_no_question_output |
| Path 1 | TS-06-SMOKE-1 | 3.3 | test_refine_question_export_smoke |

## Notes

- This is a small, focused change — two source files modified.
- Task group 1 and 2 can be done in a single coding session if desired.
- No changes to `agent.py` or prompts; this is purely a CLI/session feature.
