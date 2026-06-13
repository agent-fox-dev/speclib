# Implementation Plan: TDD Execution Engine (LangGraph)

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

The implementation builds the LangGraph execution engine in layers: state
schema and tools first, then graph nodes and routing, then worktree and
verification, then the runner entry points. Task group 1 creates all failing
tests. This is the largest spec with 7 task groups.

## Test Commands

- Spec tests: `uv run pytest -q packages/coder/tests/test_graph.py packages/coder/tests/test_nodes.py packages/coder/tests/test_tools.py packages/coder/tests/test_worktree.py packages/coder/tests/test_verify.py packages/coder/tests/test_state.py packages/coder/tests/test_runner.py -v`
- Unit tests: `uv run pytest -q packages/coder/tests/ -v -k "not smoke"`
- Property tests: `uv run pytest -q packages/coder/tests/ -v -k "property"`
- All tests: `uv run pytest -q packages/coder/tests/ -v`
- Linter: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Create test file structure
    - Create `packages/coder/tests/test_graph.py`
    - Create `packages/coder/tests/test_nodes.py`
    - Create `packages/coder/tests/test_tools.py`
    - Create `packages/coder/tests/test_worktree.py`
    - Create `packages/coder/tests/test_verify.py`
    - Create `packages/coder/tests/test_state.py`
    - Create `packages/coder/tests/test_runner.py`
    - Add git repo fixtures to conftest.py
    - _Test Spec: TS-14-1 through TS-14-25_

  - [x] 1.2 Translate acceptance-criterion tests
    - TS-14-1 through TS-14-25 (all acceptance criterion tests)
    - _Test Spec: TS-14-1 through TS-14-25_

  - [x] 1.3 Translate edge-case tests
    - TS-14-E1 through TS-14-E12
    - TS-14-E8: Unhandled exception caught by campaign
    - _Test Spec: TS-14-E1 through TS-14-E12_

  - [x] 1.4 Translate property tests
    - TS-14-P1: Monotonic task group progress
    - TS-14-P2: Retry never exceeds max_attempts
    - TS-14-P3: Path containment
    - TS-14-P4: Worktree isolation
    - TS-14-P5: Commit after success
    - TS-14-P6: State persistence completeness
    - TS-14-P7: Verification exit code semantics
    - _Test Spec: TS-14-P1 through TS-14-P7_

  - [x] 1.5 Translate integration smoke tests
    - TS-14-SMOKE-1: Full graph execution
    - TS-14-SMOKE-2: Worktree lifecycle
    - TS-14-SMOKE-3: Campaign runs multiple specs
    - _Test Spec: TS-14-SMOKE-1 through TS-14-SMOKE-3_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings: `uv run ruff check packages/coder/tests/`

- [x] 2. State schema & LangChain tools
  - [x] 2.1 Define CoderState TypedDict
    - Create/update `packages/coder/coder/graph.py` with `CoderState`
    - Define all fields with types and defaults
    - Implement `create_initial_state(parsed_spec)` factory
    - _Requirements: 1.1, 1.2_

  - [x] 2.2 Implement coding tools
    - Create `packages/coder/coder/tools.py`
    - Implement `read_file` tool with path validation
    - Implement `write_file` tool with parent dir creation and symlink check
    - Implement `run_command` tool with timeout and cwd enforcement
    - Implement `list_directory` tool
    - All tools resolve paths relative to a worktree root
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 2.V Verify task group 2
    - [x] Spec tests pass: TS-14-1, TS-14-13 through TS-14-16
    - [x] Edge case tests pass: TS-14-E3, TS-14-E4
    - [x] Property tests pass: TS-14-P3
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [x] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [x] Requirements 1.1, 1.2, 4.1-4.5 met

- [x] 3. Verification runner & run state
  - [x] 3.1 Implement VerificationRunner
    - Create `packages/coder/coder/verify.py`
    - Implement `run()` method executing test commands
    - Capture stdout, stderr, exit code
    - Implement timeout enforcement
    - Handle empty/missing commands
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 3.2 Implement run state persistence
    - Create `packages/coder/coder/state.py`
    - Implement `persist_state()` with atomic write (temp + rename)
    - Implement `StateTransition` record and history tracking
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 3.V Verify task group 3
    - [x] Spec tests pass: TS-14-19, TS-14-20, TS-14-22, TS-14-23
    - [x] Edge case tests pass: TS-14-E6
    - [ ] Property tests pass: TS-14-P4
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [x] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [x] Requirements 6.1-6.4, 8.1-8.3 met

- [x] 4. Checkpoint — Tools & Infrastructure Complete
  - Ensure all tests pass. All infrastructure modules (state, tools, verify)
    are working. Ask the user if questions arise.

- [x] 5. LangGraph nodes & routing
  - [x] 5.1 Implement workflow nodes
    - Create `packages/coder/coder/nodes.py`
    - Implement `understand_spec` node (LLM reads spec, writes context)
    - Implement `analyze_codebase` node (LLM analyzes code)
    - Implement `write_tests` node (LLM writes failing tests via tools)
    - Implement `verify_test_coverage` node (LLM checks coverage)
    - Implement `implement` node (LLM writes code via tools)
    - Implement `run_tests` node (calls VerificationRunner)
    - Implement `verify_intent` node (LLM with reviewer persona)
    - Each node reads from and writes to CoderState
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 5.2 Implement conditional edge routing
    - Add routing functions to `packages/coder/coder/graph.py`
    - `route_after_coverage`: coverage_ok → implement, else → write_tests
    - `route_after_tests`: pass → verify_intent, fail+attempts → implement,
      fail+max → halted
    - `route_after_intent`: no drift → next_task_group, drift+attempts →
      verify_test_coverage, drift+max → halted
    - `route_next_group`: more groups → write_tests, all done → complete
    - Implement `next_task_group` node that advances group counter
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 5.3 Build graph constructor
    - Implement `build_graph(provider, tools, config)` in graph.py
    - Add all nodes to the graph
    - Wire conditional edges
    - Set entry point to `understand_spec`
    - Compile the graph
    - _Requirements: 9.1 (partial)_

  - [x] 5.V Verify task group 5
    - [x] Spec tests pass: TS-14-2 through TS-14-12
    - [x] Edge case tests pass: TS-14-E1, TS-14-E2
    - [x] Property tests pass: TS-14-P1, TS-14-P2
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [x] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [x] Requirements 2.1-2.7, 3.1-3.6 met

- [x] 6. Worktree, git, & runner entry points
  - [x] 6.1 Implement worktree lifecycle
    - Create `packages/coder/coder/worktree.py`
    - Implement `create_worktree()` with branch naming
    - Implement `merge_worktree()` with fast-forward merge
    - Implement `cleanup_worktree()` with directory removal and prune
    - Implement `commit_task_group()` with conventional message
    - Handle stale worktree cleanup
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 6.2 Implement runner entry points
    - Create `packages/coder/coder/runner.py`
    - Implement `run_spec()`: build graph → init state → execute → return result
    - Implement `run_campaign()`: iterate plan → create worktree → run_spec
      → merge → cleanup per spec
    - Implement `RunResult` data class
    - Wire task group iteration with commit after each group
    - Handle per-spec exception catching in campaign
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 9.1, 9.2, 9.3_

  - [x] 6.3 Wire CLI to runner
    - Update `packages/coder/coder/cli.py` to call `build_execution_plan`
      then `run_campaign`
    - Pass provider, config, and repo path through
    - Print run results summary
    - _Requirements: (cross-spec wiring)_

  - [x] 6.V Verify task group 6
    - [x] Spec tests pass: TS-14-17, TS-14-18, TS-14-21, TS-14-24, TS-14-25
    - [x] Edge case tests pass: TS-14-E5, TS-14-E7
    - [x] Smoke tests pass: TS-14-SMOKE-1, TS-14-SMOKE-2, TS-14-SMOKE-3
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [x] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [x] Requirements 5.1-5.5, 7.1-7.4, 9.1-9.3 met

- [x] 7. Wiring verification

  - [x] 7.1 Trace every execution path from design.md end-to-end
    - Path 1: run_spec → build_graph → invoke → all nodes → RunResult
    - Path 2: create_worktree → run_spec → commit → merge → cleanup
    - Path 3: run_campaign → loop(create_worktree → run_spec → merge)
    - Verify each function in the chain is called
    - _Requirements: all_

  - [x] 7.2 Verify return values propagate correctly
    - `build_graph()` → `CompiledGraph` used by `run_spec`
    - Node functions → updated `CoderState` consumed by next node
    - `VerificationRunner.run()` → `VerificationResult` consumed by
      `run_tests` node
    - `run_spec()` → `RunResult` consumed by `run_campaign`
    - _Requirements: all_

  - [x] 7.3 Run the integration smoke tests
    - TS-14-SMOKE-1: Full graph execution with mock LLM
    - TS-14-SMOKE-2: Worktree lifecycle end-to-end
    - TS-14-SMOKE-3: Campaign runs multiple specs
    - _Test Spec: TS-14-SMOKE-1 through TS-14-SMOKE-3_

  - [x] 7.4 Stub / dead-code audit
    - Search all files in `packages/coder/coder/` for stubs, TODOs
    - Focus on: graph.py, nodes.py, tools.py, worktree.py, runner.py
    - _Requirements: all_

  - [x] 7.5 Cross-spec entry point verification
    - Verify `run_campaign()` is called from CLI (spec 12)
    - Verify spec 15 can access `CoderState` and graph structure
    - _Requirements: all_

  - [x] 7.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain
    - [x] All execution paths from design.md are live
    - [x] All cross-spec entry points are called from production code
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 14-REQ-1.1 | TS-14-1 | 2.1 | test_graph.py::test_initial_state |
| 14-REQ-1.2 | TS-14-1 | 2.1 | test_graph.py::test_initial_state |
| 14-REQ-2.1 | TS-14-2 | 5.1 | test_nodes.py::test_understand_spec |
| 14-REQ-2.2 | TS-14-3 | 5.1 | test_nodes.py::test_analyze_codebase |
| 14-REQ-2.3 | TS-14-4 | 5.1 | test_nodes.py::test_write_tests |
| 14-REQ-2.4 | TS-14-5 | 5.1 | test_nodes.py::test_verify_coverage |
| 14-REQ-2.5 | TS-14-6 | 5.1 | test_nodes.py::test_implement |
| 14-REQ-2.6 | TS-14-7 | 5.1 | test_nodes.py::test_run_tests |
| 14-REQ-2.7 | TS-14-8 | 5.1 | test_nodes.py::test_verify_intent |
| 14-REQ-2.E1 | TS-14-E1 | 5.1 | test_nodes.py::test_empty_response |
| 14-REQ-3.1 | TS-14-9 | 5.2 | test_graph.py::test_coverage_routing |
| 14-REQ-3.2 | TS-14-10 | 5.2 | test_graph.py::test_fail_routing |
| 14-REQ-3.3 | TS-14-11 | 5.2 | test_graph.py::test_pass_routing |
| 14-REQ-3.6 | TS-14-12 | 5.2 | test_graph.py::test_halt_routing |
| 14-REQ-3.E1 | TS-14-E2 | 5.1 | test_nodes.py::test_halted_passthrough |
| 14-REQ-4.1 | TS-14-13 | 2.2 | test_tools.py::test_read_file |
| 14-REQ-4.2 | TS-14-14 | 2.2 | test_tools.py::test_write_file |
| 14-REQ-4.3 | TS-14-15 | 2.2 | test_tools.py::test_run_command |
| 14-REQ-4.5 | TS-14-16 | 2.2 | test_tools.py::test_path_traversal |
| 14-REQ-4.E1 | TS-14-E3 | 2.2 | test_tools.py::test_command_timeout |
| 14-REQ-4.E3 | TS-14-E4 | 2.2 | test_tools.py::test_symlink_write |
| 14-REQ-5.1 | TS-14-17 | 6.1 | test_worktree.py::test_create |
| 14-REQ-5.3 | TS-14-18 | 6.1 | test_worktree.py::test_merge |
| 14-REQ-5.E1 | TS-14-E5 | 6.1 | test_worktree.py::test_stale_cleanup |
| 14-REQ-6.2 | TS-14-19 | 3.1 | test_verify.py::test_pass_result |
| 14-REQ-6.3 | TS-14-20 | 3.1 | test_verify.py::test_fail_result |
| 14-REQ-6.E1 | TS-14-E6 | 3.1 | test_verify.py::test_empty_command |
| 14-REQ-7.2 | TS-14-21 | 6.1 | test_worktree.py::test_commit_message |
| 14-REQ-7.E1 | TS-14-E7 | 6.1 | test_worktree.py::test_commit_nothing |
| 14-REQ-8.1 | TS-14-22 | 3.2 | test_state.py::test_persist |
| 14-REQ-8.2 | TS-14-23 | 3.2 | test_state.py::test_history |
| 14-REQ-9.1 | TS-14-24 | 6.2 | test_runner.py::test_run_spec |
| 14-REQ-9.2 | TS-14-24 | 6.2 | test_runner.py::test_run_spec |
| 14-REQ-9.3 | TS-14-25 | 6.2 | test_runner.py::test_run_campaign |
| 14-REQ-9.E1 | TS-14-25 | 6.2 | test_runner.py::test_campaign_catches |
| 14-REQ-1.E1 | TS-14-E9 | 2.1 | test_state.py::test_missing_field_defaults |
| 14-REQ-3.4 | TS-14-26 | 5.2 | test_graph.py::test_drift_routing |
| 14-REQ-3.5 | TS-14-27 | 5.2 | test_graph.py::test_no_drift_routing |
| 14-REQ-3.E1 | TS-14-E2 | 5.1 | test_nodes.py::test_halted_passthrough |
| 14-REQ-4.4 | TS-14-28 | 2.2 | test_tools.py::test_list_directory |
| 14-REQ-4.E2 | TS-14-E10 | 2.2 | test_tools.py::test_binary_file_read |
| 14-REQ-5.2 | TS-14-29 | 6.1 | test_worktree.py::test_ops_in_worktree |
| 14-REQ-5.4 | TS-14-30 | 6.1 | test_worktree.py::test_cleanup_after_merge |
| 14-REQ-5.5 | TS-14-31 | 6.1 | test_worktree.py::test_ff_merge_failure |
| 14-REQ-5.E2 | TS-14-E11 | 6.1 | test_worktree.py::test_create_failure |
| 14-REQ-6.1 | TS-14-32 | 3.1 | test_verify.py::test_command_order |
| 14-REQ-6.4 | TS-14-33 | 3.1 | test_verify.py::test_configurable_timeout |
| 14-REQ-6.E2 | TS-14-E12 | 3.1 | test_verify.py::test_binary_not_found |
| 14-REQ-7.1 | TS-14-34 | 6.2 | test_runner.py::test_group_order |
| 14-REQ-7.3 | TS-14-35 | 6.2 | test_runner.py::test_advance_group |
| 14-REQ-7.4 | TS-14-36 | 6.2 | test_runner.py::test_complete_phase |
| 14-REQ-8.3 | TS-14-37 | 3.2 | test_state.py::test_atomic_write |
| 14-REQ-8.E1 | TS-14-E13 | 3.2 | test_state.py::test_write_failure |

## Notes

- Mock LLM provider should return canned responses that simulate the
  coding workflow (code snippets, test files, coverage assessments).
- Worktree tests require `git init` in temporary directories with at least
  one commit before worktree creation works.
- The full graph smoke test (TS-14-SMOKE-1) is the most complex integration
  test — it exercises the entire LangGraph state machine with a mock LLM
  that responds appropriately to each node's prompt.
- Use `asyncio` fixtures for async tool and verification runner tests.
