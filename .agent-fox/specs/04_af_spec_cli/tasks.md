# Implementation Plan: spec CLI

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

This plan implements the spec CLI using Click. The CLI is a thin
presentation layer wrapping speclib's Campaign, SpecSession, and agent
pipeline. Groups are ordered: tests first, then shared infrastructure
(helpers, error handling), then commands in logical clusters, and finally
wiring verification.

## Test Commands

- Spec tests: `uv run pytest -q tests/test_cli.py`
- Unit tests: `uv run pytest -q tests/test_cli.py -k "not smoke"`
- Property tests: `uv run pytest -q tests/test_cli.py -k property`
- Integration tests: `uv run pytest -q tests/test_cli.py -k smoke`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check && uv run mypy speclib/`

## Tasks

- [x] 1. Write failing spec tests — infrastructure and campaign commands
  - [x] 1.1 Set up CLI test infrastructure
    - Create `tests/test_cli.py` for all CLI tests
    - Import Click's `CliRunner` and `main` from `speclib.cli`
    - Create fixtures for: temp campaign directory, temp PRD file, mocked
      Campaign, mocked SpecSession, mocked agent pipeline
    - Create helper to set up a campaign directory with campaign.yaml
    - Create helper to set up a spec directory with _session.json and artifacts
    - _Test Spec: all TS-04-* entries_

  - [x] 1.2 Translate campaign command tests
    - `test_init_creates_campaign` (TS-04-1)
    - `test_init_defaults_name_to_basename` (TS-04-2)
    - `test_init_defaults_description_empty` (TS-04-3)
    - `test_init_handles_campaign_error` (TS-04-4)
    - `test_init_resolves_relative_path` (TS-04-5)
    - `test_list_displays_table` (TS-04-6)
    - `test_list_explicit_directory` (TS-04-7)
    - `test_list_empty_campaign` (TS-04-8)
    - `test_list_sorts_by_prefix` (TS-04-9)
    - `test_list_error_non_campaign` (TS-04-10)
    - Tests MUST fail (CLI commands don't exist yet beyond stub)
    - _Test Spec: TS-04-1 through TS-04-10_

  - [x] 1.3 Translate cross-cutting and resolution tests
    - `test_spec_not_found_lists_available` (TS-04-44)
    - `test_campaign_dir_option_overrides_cwd` (TS-04-45)
    - `test_no_campaign_dir_error` (TS-04-46)
    - `test_spec_resolved_by_full_name` (TS-04-47)
    - `test_spec_resolved_by_number` (TS-04-48)
    - `test_exit_code_0_success` (TS-04-49)
    - `test_exit_code_1_user_error` (TS-04-50)
    - `test_exit_code_2_internal_error` (TS-04-51)
    - _Test Spec: TS-04-44 through TS-04-51_

  - [x] 1.V Verify task group 1
    - [x] All infrastructure and campaign spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — CLI commands are stubs
    - [x] No linter warnings introduced: `uv run ruff check tests/test_cli.py`

- [x] 2. Write failing spec tests — command and integration tests
  - [x] 2.1 Translate spec new command tests
    - `test_new_creates_spec` (TS-04-11)
    - `test_new_explicit_name` (TS-04-12)
    - `test_new_derives_name` (TS-04-13)
    - `test_new_one_shot` (TS-04-14)
    - `test_new_missing_prd` (TS-04-15)
    - `test_new_invalid_name` (TS-04-16)
    - _Test Spec: TS-04-11 through TS-04-16_

  - [x] 2.2 Translate assess and refine command tests
    - `test_assess_runs_and_prints` (TS-04-17)
    - `test_assess_output_formatting` (TS-04-18)
    - `test_assess_wrong_state` (TS-04-19)
    - `test_assess_agent_error` (TS-04-20)
    - `test_refine_submits_answers` (TS-04-21)
    - `test_refine_missing_answers_file` (TS-04-22)
    - `test_refine_invalid_json` (TS-04-23)
    - `test_refine_wrong_state` (TS-04-24)
    - `test_refine_prints_updated_assessment` (TS-04-25)
    - `test_refine_invalid_schema` (TS-04-26)
    - _Test Spec: TS-04-17 through TS-04-26_

  - [x] 2.3 Translate accept, generate, validate, render, show, status tests
    - `test_accept_transitions_state` (TS-04-27)
    - `test_accept_wrong_state` (TS-04-28)
    - `test_generate_runs_and_prints` (TS-04-29)
    - `test_generate_wrong_state` (TS-04-30)
    - `test_generate_agent_error` (TS-04-31)
    - `test_validate_passing` (TS-04-32)
    - `test_validate_with_errors` (TS-04-33)
    - `test_validate_missing_artifacts` (TS-04-34)
    - `test_render_outputs_markdown` (TS-04-35)
    - `test_render_combined` (TS-04-36)
    - `test_render_without_combined` (TS-04-37)
    - `test_render_missing_artifacts` (TS-04-38)
    - `test_status_all_specs` (TS-04-39)
    - `test_status_single_spec` (TS-04-40)
    - `test_show_session_state` (TS-04-41)
    - `test_show_artifact_content` (TS-04-42)
    - `test_show_nonexistent_artifact` (TS-04-43)
    - _Test Spec: TS-04-27 through TS-04-43_

  - [x] 2.4 Translate property tests
    - `test_property_spec_resolution_determinism` (TS-04-P1)
    - `test_property_error_commands_nonzero_exit` (TS-04-P2)
    - `test_property_campaign_dir_precedence` (TS-04-P3)
    - `test_property_init_no_overwrite` (TS-04-P4)
    - `test_property_state_gate_enforcement` (TS-04-P5)
    - _Test Spec: TS-04-P1 through TS-04-P5_

  - [x] 2.5 Write integration smoke tests
    - `test_smoke_init_and_list` (TS-04-SMOKE-1)
    - `test_smoke_new_and_status` (TS-04-SMOKE-2)
    - `test_smoke_show_artifact` (TS-04-SMOKE-3)
    - `test_smoke_validate_and_render` (TS-04-SMOKE-4)
    - _Test Spec: TS-04-SMOKE-1 through TS-04-SMOKE-4_

  - [x] 2.V Verify task group 2
    - [x] All command and integration spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — CLI commands are stubs
    - [x] No linter warnings introduced: `uv run ruff check tests/test_cli.py`

- [x] 3. Implement CLI shared infrastructure
  - [x] 3.1 Implement main Click group and context
    - `@click.group()` decorator on `main()`
    - `--campaign-dir` / `-C` option on the group, defaults to None (uses CWD)
    - Store resolved campaign_dir in `ctx.obj`
    - _Requirements: 04-REQ-CC.1, 04-REQ-CC.2_

  - [x] 3.2 Implement resolve_campaign helper
    - Open `Campaign` from context's campaign_dir
    - Catch `CampaignError`, print user-friendly message with `--campaign-dir` hint
    - Call `sys.exit(1)` on campaign errors
    - _Requirements: 04-REQ-CC.3_

  - [x] 3.3 Implement resolve_spec helper
    - Scan `campaign.specs()` for directory matching by full name or numeric prefix
    - On no match: list available specs and call `sys.exit(1)`
    - _Requirements: 04-REQ-CC.4, 04-REQ-CC.5_

  - [x] 3.4 Implement error handling wrapper
    - Try/except in each command or shared decorator
    - CampaignError, SessionError → stderr + exit 1
    - Other exceptions → stderr + exit 2
    - _Requirements: 04-REQ-CC.6_

  - [x] 3.5 Implement output formatting helpers
    - `format_table(headers, rows)` — plain text table (Rich if available)
    - `format_assessment(assessment)` — quality/gaps/questions sections
    - `format_validation_errors(errors)` — file/path/message table
    - _Requirements: 04-REQ-2.1, 04-REQ-4.2, 04-REQ-8.4_

  - [x] 3.V Verify task group 3
    - [x] Cross-cutting tests pass (TS-04-45, TS-04-46, TS-04-47, TS-04-48, TS-04-49, TS-04-50, TS-04-51)
    - [x] Property tests P1, P2, P3 pass
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings: `uv run ruff check speclib/cli.py`

- [x] 4. Implement campaign commands
  - [x] 4.1 Implement init command
    - `@main.command("init")` with `path`, `--name`, `--description` params
    - Resolve relative path to absolute
    - Default name to directory basename
    - Default description to empty string
    - Call `Campaign.create()`, catch `CampaignError`
    - Print confirmation with absolute path
    - _Requirements: 04-REQ-1.1, 04-REQ-1.2, 04-REQ-1.3, 04-REQ-1.4, 04-REQ-1.E1_

  - [x] 4.2 Implement list command
    - `@main.command("list")` with optional `campaign_dir` argument
    - Use argument if provided, otherwise use context campaign_dir
    - Open campaign, list specs with session state
    - Format as table sorted by numeric prefix
    - Handle empty campaign
    - _Requirements: 04-REQ-2.1, 04-REQ-2.2, 04-REQ-2.3, 04-REQ-2.4, 04-REQ-2.E1_

  - [x] 4.V Verify task group 4
    - [x] Campaign command tests pass (TS-04-1 through TS-04-10)
    - [x] Property test P4 (init no overwrite) passes
    - [x] Smoke test SMOKE-1 (init and list) passes
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings: `uv run ruff check speclib/cli.py`

- [x] 5. Implement spec authoring commands (new, assess, refine, accept)
  - [x] 5.1 Implement new command
    - `@main.command("new")` with `prd_file`, `--name`, `--one-shot`
    - Validate PRD file exists
    - Derive name from filename if not provided (strip extension, snake_case)
    - Call `campaign.new_spec()` with content, name, mode
    - Print created spec directory name
    - _Requirements: 04-REQ-3.1, 04-REQ-3.2, 04-REQ-3.3, 04-REQ-3.4, 04-REQ-3.E1_

  - [x] 5.2 Implement assess command
    - `@main.command("assess")` with `spec` argument
    - Resolve spec, resume session
    - `asyncio.run(session.assess())` — bridge async
    - Format and print assessment summary
    - Handle state and agent errors
    - _Requirements: 04-REQ-4.1, 04-REQ-4.2, 04-REQ-4.3, 04-REQ-4.E1_

  - [x] 5.3 Implement refine command
    - `@main.command("refine")` with `spec`, `--answers`
    - Read and parse JSON answers file
    - Validate answers schema (must be dict of str→str)
    - Resolve spec, resume session
    - `asyncio.run(session.refine(answers))` — bridge async
    - Print updated assessment summary
    - Handle state, file, JSON, and schema errors
    - _Requirements: 04-REQ-5.1, 04-REQ-5.2, 04-REQ-5.3, 04-REQ-5.4, 04-REQ-5.5, 04-REQ-5.E1_

  - [x] 5.4 Implement accept command
    - `@main.command("accept")` with `spec` argument
    - Resolve spec, resume session
    - Call `session.accept_prd()`
    - Print confirmation with new state
    - Handle state errors
    - _Requirements: 04-REQ-6.1, 04-REQ-6.2_

  - [x] 5.V Verify task group 5
    - [x] New command tests pass (TS-04-11 through TS-04-16)
    - [x] Assess command tests pass (TS-04-17 through TS-04-20)
    - [x] Refine command tests pass (TS-04-21 through TS-04-26)
    - [x] Accept command tests pass (TS-04-27, TS-04-28)
    - [x] Property test P5 (state gates) passes for assess, refine, accept
    - [x] Smoke test SMOKE-2 (new and status) passes
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings: `uv run ruff check speclib/cli.py`

- [x] 6. Implement spec lifecycle commands (generate, validate, render, show, status)
  - [x] 6.1 Implement generate command
    - `@main.command("generate")` with `spec` argument
    - Resolve spec, resume session
    - `asyncio.run(session.generate())` — bridge async
    - Print progress and artifact summary
    - Handle state and agent errors
    - _Requirements: 04-REQ-7.1, 04-REQ-7.2, 04-REQ-7.3, 04-REQ-7.E1_

  - [x] 6.2 Implement validate command
    - `@main.command("validate")` with `spec` argument
    - Resolve spec, resume session
    - Call `session.validate()`
    - Print success or error table
    - Handle missing artifacts
    - _Requirements: 04-REQ-8.1, 04-REQ-8.2, 04-REQ-8.3, 04-REQ-8.4, 04-REQ-8.E1_

  - [x] 6.3 Implement render command
    - `@main.command("render")` with `spec`, `--combined`
    - Resolve spec, resume session
    - Call `session.render(combined=combined)`
    - Print markdown to stdout
    - Handle missing artifacts
    - _Requirements: 04-REQ-9.1, 04-REQ-9.2, 04-REQ-9.3, 04-REQ-9.E1_

  - [x] 6.4 Implement show command
    - `@main.command("show")` with `spec`, `--artifact`
    - Resolve spec
    - If `--artifact`: read file from spec dir, print content
    - If no `--artifact`: resume session, print state summary
    - Handle missing artifact: list available files
    - _Requirements: 04-REQ-10.3, 04-REQ-10.4, 04-REQ-10.5_

  - [x] 6.5 Implement status command
    - `@main.command("status")` with optional `spec` argument
    - Without spec: table of all specs with state (like list)
    - With spec: detailed state (state, mode, assessment count, Q&A count, artifacts)
    - _Requirements: 04-REQ-10.1, 04-REQ-10.2_

  - [x] 6.V Verify task group 6
    - [x] Generate command tests pass (TS-04-29 through TS-04-31)
    - [x] Validate command tests pass (TS-04-32 through TS-04-34)
    - [x] Render command tests pass (TS-04-35 through TS-04-38)
    - [x] Show command tests pass (TS-04-39 through TS-04-43)
    - [x] Status command tests pass (TS-04-39, TS-04-40)
    - [x] Property test P5 passes for generate
    - [x] Smoke tests SMOKE-3 and SMOKE-4 pass
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings: `uv run ruff check speclib/cli.py`

- [x] 7. Wiring verification

  - [x] 7.1 Trace every execution path from design.md end-to-end
    - Path 1: init → Campaign.create → confirmation
    - Path 2: list → Campaign.open → specs → sessions → table
    - Path 3: new → Campaign.open → new_spec → confirmation
    - Path 4: assess → resolve_spec → resume → assess → formatted output
    - Path 5: refine → resolve_spec → resume → refine → assessment output
    - Path 6: accept → resolve_spec → resume → accept_prd → confirmation
    - Path 7: generate → resolve_spec → resume → generate → artifact summary
    - Path 8: validate → resolve_spec → resume → validate → result output
    - Path 9: render → resolve_spec → resume → render → markdown output
    - Path 10: show → resolve_spec → file read or session state
    - Path 11: status → campaign.specs or resolve_spec → state table/detail
    - Verify each function in the chain is actually called
    - _Requirements: all_

  - [x] 7.2 Verify Click decorators and help text
    - `spec --help` lists all subcommands
    - Each subcommand has `--help` producing correct usage
    - `--campaign-dir` appears in group help
    - _Requirements: all_

  - [x] 7.3 Verify error message quality
    - Every error path includes an actionable suggestion
    - No raw tracebacks in normal error paths
    - State errors name current and required states
    - Not-found errors list available options
    - _Requirements: 04-REQ-CC.3, 04-REQ-CC.5, 04-REQ-4.3, 04-REQ-5.4, 04-REQ-6.2, 04-REQ-7.3_

  - [x] 7.4 Run the integration smoke tests
    - All TS-04-SMOKE-* tests pass with real components
    - _Test Spec: TS-04-SMOKE-1 through TS-04-SMOKE-4_

  - [x] 7.5 Stub / dead-code audit
    - Search speclib/cli.py for `pass`, `# TODO`, `NotImplementedError`, `return None`
    - Each hit must be justified or replaced
    - No placeholder implementations remaining

  - [x] 7.6 Cross-spec entry point verification
    - Verify spec 01 stub `speclib/cli.py:main` is fully replaced
    - Verify `spec --help` works after `uv sync`
    - Verify all 11 subcommands appear in help output
    - _Requirements: all_

  - [x] 7.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain in speclib/cli.py
    - [x] All execution paths from design.md are live
    - [x] All 51 unit tests pass
    - [x] All 5 property tests pass
    - [x] All 4 smoke tests pass
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings: `uv run ruff check && uv run mypy speclib/`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 04-REQ-1.1 | TS-04-1 | 4.1 | tests/test_cli.py::test_init_creates_campaign |
| 04-REQ-1.2 | TS-04-2 | 4.1 | tests/test_cli.py::test_init_defaults_name_to_basename |
| 04-REQ-1.3 | TS-04-3 | 4.1 | tests/test_cli.py::test_init_defaults_description_empty |
| 04-REQ-1.4 | TS-04-4 | 4.1 | tests/test_cli.py::test_init_handles_campaign_error |
| 04-REQ-1.E1 | TS-04-5, TS-04-E1 | 4.1 | tests/test_cli.py::test_init_resolves_relative_path |
| 04-REQ-2.1 | TS-04-6 | 4.2 | tests/test_cli.py::test_list_displays_table |
| 04-REQ-2.2 | TS-04-7 | 4.2 | tests/test_cli.py::test_list_explicit_directory |
| 04-REQ-2.3 | TS-04-8 | 4.2 | tests/test_cli.py::test_list_empty_campaign |
| 04-REQ-2.4 | TS-04-9 | 4.2 | tests/test_cli.py::test_list_sorts_by_prefix |
| 04-REQ-2.E1 | TS-04-10, TS-04-E2 | 4.2 | tests/test_cli.py::test_list_error_non_campaign |
| 04-REQ-3.1 | TS-04-11 | 5.1 | tests/test_cli.py::test_new_creates_spec |
| 04-REQ-3.2 | TS-04-12, TS-04-13 | 5.1 | tests/test_cli.py::test_new_explicit_name, test_new_derives_name |
| 04-REQ-3.3 | TS-04-14 | 5.1 | tests/test_cli.py::test_new_one_shot |
| 04-REQ-3.4 | TS-04-15 | 5.1 | tests/test_cli.py::test_new_missing_prd |
| 04-REQ-3.E1 | TS-04-16, TS-04-E3 | 5.1 | tests/test_cli.py::test_new_invalid_name |
| 04-REQ-4.1 | TS-04-17 | 5.2 | tests/test_cli.py::test_assess_runs_and_prints |
| 04-REQ-4.2 | TS-04-18 | 5.2 | tests/test_cli.py::test_assess_output_formatting |
| 04-REQ-4.3 | TS-04-19 | 5.2 | tests/test_cli.py::test_assess_wrong_state |
| 04-REQ-4.E1 | TS-04-20, TS-04-E4 | 5.2 | tests/test_cli.py::test_assess_agent_error |
| 04-REQ-5.1 | TS-04-21 | 5.3 | tests/test_cli.py::test_refine_submits_answers |
| 04-REQ-5.2 | TS-04-22 | 5.3 | tests/test_cli.py::test_refine_missing_answers_file |
| 04-REQ-5.3 | TS-04-23 | 5.3 | tests/test_cli.py::test_refine_invalid_json |
| 04-REQ-5.4 | TS-04-24 | 5.3 | tests/test_cli.py::test_refine_wrong_state |
| 04-REQ-5.5 | TS-04-25 | 5.3 | tests/test_cli.py::test_refine_prints_updated_assessment |
| 04-REQ-5.E1 | TS-04-26, TS-04-E5 | 5.3 | tests/test_cli.py::test_refine_invalid_schema |
| 04-REQ-6.1 | TS-04-27 | 5.4 | tests/test_cli.py::test_accept_transitions_state |
| 04-REQ-6.2 | TS-04-28 | 5.4 | tests/test_cli.py::test_accept_wrong_state |
| 04-REQ-7.1 | TS-04-29 | 6.1 | tests/test_cli.py::test_generate_runs_and_prints |
| 04-REQ-7.2 | TS-04-29 | 6.1 | tests/test_cli.py::test_generate_runs_and_prints |
| 04-REQ-7.3 | TS-04-30 | 6.1 | tests/test_cli.py::test_generate_wrong_state |
| 04-REQ-7.E1 | TS-04-31, TS-04-E6 | 6.1 | tests/test_cli.py::test_generate_agent_error |
| 04-REQ-8.1 | TS-04-32 | 6.2 | tests/test_cli.py::test_validate_passing |
| 04-REQ-8.2 | TS-04-32 | 6.2 | tests/test_cli.py::test_validate_passing |
| 04-REQ-8.3 | TS-04-33 | 6.2 | tests/test_cli.py::test_validate_with_errors |
| 04-REQ-8.4 | TS-04-33 | 6.2 | tests/test_cli.py::test_validate_with_errors |
| 04-REQ-8.E1 | TS-04-34, TS-04-E7 | 6.2 | tests/test_cli.py::test_validate_missing_artifacts |
| 04-REQ-9.1 | TS-04-35 | 6.3 | tests/test_cli.py::test_render_outputs_markdown |
| 04-REQ-9.2 | TS-04-36 | 6.3 | tests/test_cli.py::test_render_combined |
| 04-REQ-9.3 | TS-04-37 | 6.3 | tests/test_cli.py::test_render_without_combined |
| 04-REQ-9.E1 | TS-04-38, TS-04-E8 | 6.3 | tests/test_cli.py::test_render_missing_artifacts |
| 04-REQ-10.1 | TS-04-39 | 6.5 | tests/test_cli.py::test_status_all_specs |
| 04-REQ-10.2 | TS-04-40 | 6.5 | tests/test_cli.py::test_status_single_spec |
| 04-REQ-10.3 | TS-04-41 | 6.4 | tests/test_cli.py::test_show_session_state |
| 04-REQ-10.4 | TS-04-42 | 6.4 | tests/test_cli.py::test_show_artifact_content |
| 04-REQ-10.5 | TS-04-43 | 6.4 | tests/test_cli.py::test_show_nonexistent_artifact |
| 04-REQ-10.E1 | TS-04-44, TS-04-E9 | 3.3 | tests/test_cli.py::test_spec_not_found_lists_available |
| 04-REQ-CC.1 | TS-04-45 | 3.1 | tests/test_cli.py::test_campaign_dir_option_overrides_cwd |
| 04-REQ-CC.2 | TS-04-45 | 3.1 | tests/test_cli.py::test_campaign_dir_option_overrides_cwd |
| 04-REQ-CC.3 | TS-04-46 | 3.2 | tests/test_cli.py::test_no_campaign_dir_error |
| 04-REQ-CC.4 | TS-04-47, TS-04-48 | 3.3 | tests/test_cli.py::test_spec_resolved_by_full_name, test_spec_resolved_by_number |
| 04-REQ-CC.5 | TS-04-44 | 3.3 | tests/test_cli.py::test_spec_not_found_lists_available |
| 04-REQ-CC.6 | TS-04-49, TS-04-50, TS-04-51 | 3.4 | tests/test_cli.py::test_exit_code_* |
| Property 1 | TS-04-P1 | 3.3 | tests/test_cli.py::test_property_spec_resolution_determinism |
| Property 2 | TS-04-P2 | 3.4 | tests/test_cli.py::test_property_error_commands_nonzero_exit |
| Property 3 | TS-04-P3 | 3.1 | tests/test_cli.py::test_property_campaign_dir_precedence |
| Property 4 | TS-04-P4 | 4.1 | tests/test_cli.py::test_property_init_no_overwrite |
| Property 5 | TS-04-P5 | 5.2, 5.3, 5.4, 6.1 | tests/test_cli.py::test_property_state_gate_enforcement |
| Path 1+2 | TS-04-SMOKE-1 | 4.1, 4.2 | tests/test_cli.py::test_smoke_init_and_list |
| Path 3+11 | TS-04-SMOKE-2 | 5.1, 6.5 | tests/test_cli.py::test_smoke_new_and_status |
| Path 10 | TS-04-SMOKE-3 | 6.4 | tests/test_cli.py::test_smoke_show_artifact |
| Path 8+9 | TS-04-SMOKE-4 | 6.2, 6.3 | tests/test_cli.py::test_smoke_validate_and_render |

## Notes

- All CLI tests use Click's `CliRunner` for isolated invocation without
  spawning subprocesses.
- Unit tests mock `Campaign` and `SpecSession` to isolate CLI presentation
  logic from business logic. Integration smoke tests use real instances on
  temp directories.
- Task groups 1 and 2 write all tests first (red). Groups 3-6 implement code
  to make them pass (green). Group 7 verifies end-to-end wiring.
- Async session methods (`assess`, `refine`, `generate`) are bridged with
  `asyncio.run()` inside synchronous Click command handlers.
- Run `uv run pytest -q tests/test_cli.py` to execute only CLI tests; run
  `uv run pytest -q` to include all project tests for regression checks.
