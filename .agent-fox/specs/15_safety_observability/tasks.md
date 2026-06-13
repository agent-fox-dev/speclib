# Implementation Plan: Safety & Observability

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

The implementation adds safety and observability to the existing coder
package. It extends the configuration model, adds circuit breaker and
token tracking modules, integrates them into the LangGraph execution from
spec 14, and adds console logging and post-mortem/summary generation.

## Test Commands

- Spec tests: `uv run pytest -q packages/coder/tests/test_circuit.py packages/coder/tests/test_tokens.py packages/coder/tests/test_postmortem.py packages/coder/tests/test_console.py packages/coder/tests/test_summary.py -v`
- Unit tests: `uv run pytest -q packages/coder/tests/ -v -k "not smoke"`
- Property tests: `uv run pytest -q packages/coder/tests/ -v -k "property"`
- All tests: `uv run pytest -q packages/coder/tests/ -v`
- Linter: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Create test file structure
    - Create `packages/coder/tests/test_circuit.py`
    - Create `packages/coder/tests/test_tokens.py`
    - Create `packages/coder/tests/test_postmortem.py`
    - Create `packages/coder/tests/test_console.py`
    - Create `packages/coder/tests/test_summary.py`
    - Add fixtures for halted states and mock LLM responses in conftest.py
    - _Test Spec: TS-15-1 through TS-15-15_

  - [x] 1.2 Translate acceptance-criterion tests
    - TS-15-1 through TS-15-15 (all acceptance criterion tests)
    - _Test Spec: TS-15-1 through TS-15-15_

  - [x] 1.3 Translate edge-case tests
    - TS-15-E1 through TS-15-E7
    - _Test Spec: TS-15-E1 through TS-15-E7_

  - [x] 1.4 Translate property tests
    - TS-15-P1: Halt guarantee
    - TS-15-P2: Token monotonicity
    - TS-15-P3: Post-mortem section completeness
    - TS-15-P4: Configuration defaults are safe
    - _Test Spec: TS-15-P1 through TS-15-P4_

  - [x] 1.5 Translate integration smoke tests
    - TS-15-SMOKE-1: Circuit breaker halts graph
    - TS-15-SMOKE-2: Token tracking end-to-end
    - _Test Spec: TS-15-SMOKE-1, TS-15-SMOKE-2_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings: `uv run ruff check packages/coder/tests/`

- [x] 2. Safety config & circuit breaker
  - [x] 2.1 Extend configuration with SafetyConfig
    - Update `packages/coder/coder/config.py`
    - Add `SafetyConfig` pydantic model with defaults
    - Add `safety` field to `CoderConfig`
    - Support `safety:` section in `.coder.yaml`
    - Support env vars: `CODER_MAX_ATTEMPTS`, `CODER_MAX_TIME`,
      `CODER_MAX_TOKENS`
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 2.2 Implement CircuitBreaker
    - Create `packages/coder/coder/circuit.py`
    - Implement `check()` method checking attempt, time, and token limits
    - Validate limits at construction (reject zero/negative)
    - Handle null limits as unlimited
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.V Verify task group 2
    - [x] Spec tests pass: TS-15-1 through TS-15-4, TS-15-15
    - [x] Edge case tests pass: TS-15-E1, TS-15-E2
    - [x] Property tests pass: TS-15-P4
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [x] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [x] Requirements 1.1-1.5, 7.1-7.3 met

- [ ] 3. Token tracking & console logging
  - [ ] 3.1 Implement TokenTracker
    - Create `packages/coder/coder/tokens.py`
    - Extend `BaseCallbackHandler` with `on_llm_end` override
    - Normalize token fields from Anthropic, Google, Ollama
    - Implement `total_tokens` property and `to_dict()` method
    - Handle missing metadata gracefully
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.2 Implement ConsoleLogger
    - Create `packages/coder/coder/console.py`
    - Use `rich.console.Console` for formatted output
    - Implement `log_transition()` with colored phase names
    - Implement `log_test_result()` with pass/fail colors
    - Implement `log_token_usage()` with running totals
    - Implement `print_summary()` for final output
    - Implement progress line format: `[group/total] phase (attempt N/max)`
    - Handle non-TTY fallback
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 3.V Verify task group 3
    - [ ] Spec tests pass: TS-15-5 through TS-15-8, TS-15-11, TS-15-12
    - [ ] Edge case tests pass: TS-15-E3, TS-15-E5
    - [ ] Property tests pass: TS-15-P2
    - [ ] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [ ] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [ ] Requirements 2.1-2.4, 4.1-4.5 met

- [ ] 4. Post-mortem, summary, & graceful shutdown
  - [ ] 4.1 Implement post-mortem generation
    - Create `packages/coder/coder/postmortem.py`
    - Implement `generate_postmortem()` that writes `_postmortem.md`
    - Include all required sections: Summary, Halt Reason, Context,
      History, Last Test Output, Token Usage, Recommendations
    - Handle I/O errors gracefully
    - Fallback to cwd when worktree missing
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 4.2 Implement run summary
    - Create `packages/coder/coder/summary.py`
    - Implement `write_run_summary()` writing `_run_summary.md`
    - Include spec name, model, groups, tokens, time, status
    - Console fallback on write failure
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 4.3 Implement graceful shutdown
    - Register SIGINT handler in runner entry point
    - On SIGINT: set halted flag, persist state, generate post-mortem
    - Leave worktree intact (no merge/cleanup)
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 4.V Verify task group 4
    - [ ] Spec tests pass: TS-15-9, TS-15-10, TS-15-13, TS-15-14
    - [ ] Edge case tests pass: TS-15-E4, TS-15-E6, TS-15-E7
    - [ ] Property tests pass: TS-15-P1, TS-15-P3
    - [ ] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [ ] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [ ] Requirements 3.1-3.4, 5.1-5.3, 6.1-6.3 met

- [ ] 5. Integration with LangGraph execution
  - [ ] 5.1 Wire circuit breaker into graph nodes
    - Update `packages/coder/coder/graph.py` to add circuit breaker
      check before each node execution (node wrapper pattern)
    - Add `generate_postmortem` terminal node to graph
    - Wire halt routing: any node → generate_postmortem when halted
    - Pass TokenTracker as callback to all LLM invocations
    - _Requirements: 1.4, 2.4, 3.3_

  - [ ] 5.2 Wire console logging into graph
    - Add ConsoleLogger calls at each node transition
    - Log test results after verification
    - Log token usage after each LLM call
    - Print run summary at end of execution
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 5.3 Wire safety into runner
    - Update `run_spec()` to create CircuitBreaker and TokenTracker
    - Pass safety config to graph construction
    - Include token totals in RunResult
    - Call `write_run_summary()` after execution
    - _Requirements: 7.3, 9.2 (from spec 14)_

  - [ ] 5.V Verify task group 5
    - [ ] Smoke tests pass: TS-15-SMOKE-1, TS-15-SMOKE-2
    - [ ] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [ ] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [ ] End-to-end: mock LLM that always fails → halts at max_attempts → post-mortem generated

- [ ] 6. Wiring verification

  - [ ] 6.1 Trace every execution path from design.md end-to-end
    - Path 1: node_wrapper → CircuitBreaker.check → halt → generate_postmortem
    - Path 2: LLM invoke → TokenTracker callback → accumulate
    - Path 3: node transition → ConsoleLogger.log_transition → rich output
    - Path 4: completion/halt → write_run_summary → file + console
    - _Requirements: all_

  - [ ] 6.2 Verify return values propagate correctly
    - `CircuitBreaker.check()` → `CheckResult` consumed by node wrapper
    - `TokenTracker.total_tokens` → consumed by circuit breaker and summary
    - `generate_postmortem()` → `Path` logged by console
    - `write_run_summary()` → `Path` returned to runner
    - _Requirements: all_

  - [ ] 6.3 Run the integration smoke tests
    - TS-15-SMOKE-1: Circuit breaker halts graph
    - TS-15-SMOKE-2: Token tracking end-to-end
    - _Test Spec: TS-15-SMOKE-1, TS-15-SMOKE-2_

  - [ ] 6.4 Stub / dead-code audit
    - Search `packages/coder/coder/` for stubs, TODOs in:
      circuit.py, tokens.py, postmortem.py, console.py, summary.py
    - _Requirements: all_

  - [ ] 6.5 Cross-spec entry point verification
    - Verify CircuitBreaker is called from graph node wrapper (spec 14)
    - Verify TokenTracker is registered on LLM invoke (spec 12 providers)
    - Verify ConsoleLogger is called from node transitions (spec 14)
    - _Requirements: all_

  - [ ] 6.V Verify wiring group
    - [ ] All smoke tests pass
    - [ ] No unjustified stubs remain
    - [ ] All execution paths from design.md are live
    - [ ] All cross-spec entry points are called from production code
    - [ ] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 15-REQ-1.1 | TS-15-1 | 2.2 | test_circuit.py::test_max_attempts |
| 15-REQ-1.2 | TS-15-2 | 2.2 | test_circuit.py::test_max_time |
| 15-REQ-1.3 | TS-15-3 | 2.2 | test_circuit.py::test_max_tokens |
| 15-REQ-1.4 | TS-15-4 | 2.2 | test_circuit.py::test_within_limits |
| 15-REQ-1.5 | TS-15-15 | 2.1 | test_config.py::test_safety_config |
| 15-REQ-1.E1 | TS-15-E1 | 2.2 | test_circuit.py::test_zero_limit |
| 15-REQ-1.E2 | TS-15-E2 | 2.2 | test_circuit.py::test_null_unlimited |
| 15-REQ-2.1 | TS-15-5 | 3.1 | test_tokens.py::test_anthropic |
| 15-REQ-2.2 | TS-15-6 | 3.1 | test_tokens.py::test_google |
| 15-REQ-2.3 | TS-15-7, TS-15-8 | 3.1 | test_tokens.py::test_total, test_to_dict |
| 15-REQ-2.E1 | TS-15-E3 | 3.1 | test_tokens.py::test_missing_metadata |
| 15-REQ-3.1 | TS-15-10 | 4.1 | test_postmortem.py::test_file_location |
| 15-REQ-3.2 | TS-15-9 | 4.1 | test_postmortem.py::test_sections |
| 15-REQ-3.4 | TS-15-E4 | 4.1 | test_postmortem.py::test_io_error |
| 15-REQ-3.E1 | TS-15-E4 | 4.1 | test_postmortem.py::test_no_worktree |
| 15-REQ-4.1 | TS-15-11 | 3.2 | test_console.py::test_phase_transition |
| 15-REQ-4.2 | TS-15-12 | 3.2 | test_console.py::test_test_results |
| 15-REQ-4.5 | TS-15-11 | 3.2 | test_console.py::test_phase_transition |
| 15-REQ-4.E1 | TS-15-E5 | 3.2 | test_console.py::test_non_tty |
| 15-REQ-5.2 | TS-15-13 | 4.3 | test_postmortem.py::test_shutdown_state |
| 15-REQ-5.E1 | TS-15-E6 | 4.3 | test_runner.py::test_sigint |
| 15-REQ-6.2 | TS-15-14 | 4.2 | test_summary.py::test_fields |
| 15-REQ-6.E1 | TS-15-E7 | 4.2 | test_summary.py::test_write_failure |
| 15-REQ-7.1 | TS-15-15 | 2.1 | test_config.py::test_safety_yaml |
| 15-REQ-7.2 | TS-15-15 | 2.1 | test_config.py::test_safety_config |
| 15-REQ-2.4 | TS-15-16 | 3.1, 5.1 | test_tokens.py::test_tracker_registered |
| 15-REQ-3.3 | TS-15-17 | 4.1, 5.1 | test_postmortem.py::test_terminal_node |
| 15-REQ-4.3 | TS-15-18 | 3.2, 5.2 | test_console.py::test_token_usage_display |
| 15-REQ-4.4 | TS-15-19 | 3.2 | test_console.py::test_rich_colors |
| 15-REQ-5.1 | TS-15-20 | 4.3, 5.1 | test_circuit.py::test_complete_inflight_call |
| 15-REQ-5.3 | TS-15-21 | 4.3 | test_postmortem.py::test_worktree_intact |
| 15-REQ-6.1 | TS-15-22 | 4.2 | test_summary.py::test_file_location |
| 15-REQ-6.3 | TS-15-23 | 4.2, 5.2 | test_console.py::test_print_summary |
| 15-REQ-7.3 | TS-15-24 | 2.1, 5.3 | test_config.py::test_safety_passed_to_cb |

## Notes

- Mock LLM responses should include realistic token usage metadata for
  each provider type (Anthropic, Google, Ollama).
- The SIGINT test (TS-15-E6) requires careful signal handling — use
  `signal.raise_signal(signal.SIGINT)` from a separate thread.
- Property tests for token monotonicity use random sequences of positive
  integers representing token counts.
- The circuit breaker integration smoke test is the most important test
  in this spec — it verifies the entire safety chain works end-to-end
  within the LangGraph execution.
