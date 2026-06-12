# Implementation Plan: CLI Progress Feedback

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

Implements spinner feedback in three phases: failing tests, `StatusSpinner` +
`--quiet` flag, then wiring into CLI commands. The spinner module is
self-contained — it wraps Rich's `Live` + `Spinner` behind a context manager.

## Test Commands

- Spec tests: `uv run pytest -q tests/test_cli.py tests/test_ui.py -k "spinner or quiet"`
- Unit tests: `uv run pytest -q tests/`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check speclib/ tests/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Create `tests/test_ui.py` for StatusSpinner
    - Context manager works (TS-09-11)
    - Quiet mode is no-op (TS-09-12)
    - Stops on error (TS-09-E2)
    - Non-TTY fallback (TS-09-P4)
    - _Test Spec: TS-09-11, TS-09-12, TS-09-E2, TS-09-P4_

  - [x] 1.2 Add CLI spinner tests to `tests/test_cli.py`
    - Assess shows spinner on stderr (TS-09-1)
    - Refine shows spinner (TS-09-2)
    - Generate shows per-artifact progress (TS-09-3)
    - Spinner stops on success (TS-09-4)
    - Spinner output on stderr only (TS-09-5)
    - Non-TTY plain text (TS-09-6)
    - _Test Spec: TS-09-1 through TS-09-6_

  - [x] 1.3 Add quiet mode tests
    - `--quiet` flag accepted (TS-09-7)
    - Quiet suppresses spinner (TS-09-8)
    - Quiet preserves output (TS-09-9)
    - Quiet in context (TS-09-10)
    - _Test Spec: TS-09-7 through TS-09-10_

  - [x] 1.4 Add edge case and property tests
    - Spinner stops on error (TS-09-E1)
    - Property tests (TS-09-P1 through TS-09-P3)
    - _Test Spec: TS-09-E1, TS-09-P1 through TS-09-P3_

  - [x] 1.5 Add integration smoke tests
    - Assess with spinner (TS-09-SMOKE-1)
    - Quiet mode (TS-09-SMOKE-2)
    - _Test Spec: TS-09-SMOKE-1, TS-09-SMOKE-2_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings introduced: `uv run ruff check tests/`

- [x] 2. Implement StatusSpinner and --quiet flag
  - [x] 2.1 Add `rich` dependency
    - Add `rich>=13.0` to `pyproject.toml` dependencies
    - Run `uv sync`
    - _Requirements: 09-REQ-4.1_

  - [x] 2.2 Create `speclib/ui.py` with `StatusSpinner`
    - Context manager using `Rich.Console(stderr=True)` + `Live` + `Spinner`
    - `update(message)` to change spinner text
    - `log(message)` to print permanent line above spinner
    - `quiet=True` makes all methods no-op
    - Non-TTY detection: print plain text lines, no animation
    - _Requirements: 09-REQ-4.1, 09-REQ-4.2, 09-REQ-2.1, 09-REQ-2.2_

  - [x] 2.3 Add `--quiet` / `-q` global option to CLI
    - Add to `main` Click group
    - Store in `ctx.obj["quiet"]`
    - _Requirements: 09-REQ-3.1, 09-REQ-3.4_

  - [x] 2.V Verify task group 2
    - [x] StatusSpinner tests pass: `uv run pytest -q tests/test_ui.py`
    - [x] `--quiet` flag tests pass
    - [x] No linter warnings: `uv run ruff check speclib/ tests/`

- [x] 3. Wire spinner into CLI commands
  - [x] 3.1 Add spinner to `assess_cmd`
    - Wrap `asyncio.run(session.assess())` in `StatusSpinner` context
    - Message: "Assessing PRD..."
    - _Requirements: 09-REQ-1.1, 09-REQ-1.5_

  - [x] 3.2 Add spinner to `refine_cmd` (answer submission path)
    - Wrap `asyncio.run(session.refine(...))` in `StatusSpinner` context
    - Message: "Refining PRD with answers..."
    - No spinner for question-export path (it's instant)
    - _Requirements: 09-REQ-1.2_

  - [x] 3.3 Add spinner to `generate_cmd`
    - Create `StatusSpinner` outside the `asyncio.run` call
    - Use `on_artifact` callback to update spinner and log completions
    - Initial message: "Generating requirements..."
    - _Requirements: 09-REQ-1.3, 09-REQ-1.4_

  - [x] 3.V Verify task group 3
    - [x] All CLI spinner tests pass
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings: `uv run ruff check speclib/ tests/`
    - [x] Requirements 09-REQ-1.*, 09-REQ-2.*, 09-REQ-3.* met

- [x] 4. Wiring verification
  - [x] 4.1 Trace every execution path from design.md end-to-end
    - Path 1 (assess with spinner): CLI → StatusSpinner → session.assess → stop
    - Path 2 (generate with updates): CLI → StatusSpinner → generate → callback → update
    - Path 3 (quiet mode): CLI → StatusSpinner(quiet=True) → no output
    - _Requirements: all_

  - [x] 4.2 Verify return values propagate correctly
    - StatusSpinner.__enter__ returns self with update/log methods
    - on_artifact callback receives (name, content) and calls spinner.update
    - _Requirements: all_

  - [x] 4.3 Run the integration smoke tests
    - TS-09-SMOKE-1 and TS-09-SMOKE-2 pass
    - _Test Spec: TS-09-SMOKE-1, TS-09-SMOKE-2_

  - [x] 4.4 Stub / dead-code audit
    - Verify no unused imports in `speclib/ui.py`
    - Verify `--quiet` is consumed in all async commands
    - _Requirements: all_

  - [x] 4.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain in touched files
    - [x] All execution paths from design.md are live
    - [x] All existing tests still pass: `uv run pytest -q`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 09-REQ-1.1 | TS-09-1 | 3.1 | test_assess_spinner |
| 09-REQ-1.2 | TS-09-2 | 3.2 | test_refine_spinner |
| 09-REQ-1.3 | TS-09-3 | 3.3 | test_generate_spinner |
| 09-REQ-1.4 | TS-09-3 | 3.3 | test_generate_artifact_progress |
| 09-REQ-1.5 | TS-09-4 | 3.1 | test_spinner_stops_on_success |
| 09-REQ-1.E1 | TS-09-E1 | 3.1 | test_spinner_stops_on_error |
| 09-REQ-1.E2 | TS-09-E2 | 2.2 | test_spinner_stops_on_interrupt |
| 09-REQ-2.1 | TS-09-5 | 2.2 | test_spinner_stderr_only |
| 09-REQ-2.2 | TS-09-6 | 2.2 | test_spinner_non_tty |
| 09-REQ-3.1 | TS-09-7 | 2.3 | test_quiet_flag_accepted |
| 09-REQ-3.2 | TS-09-8 | 2.3 | test_quiet_suppresses_spinner |
| 09-REQ-3.3 | TS-09-9 | 2.3 | test_quiet_preserves_output |
| 09-REQ-3.4 | TS-09-10 | 2.3 | test_quiet_in_context |
| 09-REQ-4.1 | TS-09-11 | 2.2 | test_spinner_context_manager |
| 09-REQ-4.2 | TS-09-12 | 2.2 | test_spinner_quiet_noop |
| Property 1 | TS-09-P1 | 2.3 | test_quiet_suppresses_all |
| Property 2 | TS-09-P2 | 2.2 | test_spinner_stderr_property |
| Property 3 | TS-09-P3 | 2.2 | test_spinner_cleanup_property |
| Property 4 | TS-09-P4 | 2.2 | test_non_tty_fallback_property |
| Path 1 | TS-09-SMOKE-1 | 4.3 | test_assess_spinner_smoke |
| Path 3 | TS-09-SMOKE-2 | 4.3 | test_quiet_mode_smoke |

## Notes

- `rich` is a new dependency — add to `pyproject.toml`.
- The `CliRunner` in tests does not provide a real TTY, so tests will
  exercise the non-TTY fallback path by default. TTY behavior can be tested
  by mocking `Console.is_terminal`.
- The `generate` command's `on_artifact` callback is synchronous and called
  from inside `asyncio.run`, so `spinner.update()` must be thread-safe (Rich
  `Live` handles this).
