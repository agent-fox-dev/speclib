# Implementation Plan: Agent CLI Skill for Spec Authoring

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

This plan delivers the agent skill file and installation utility. Groups are
ordered so tests exist before the implementation, the skill file is written
before the install command, and wiring verification is last.

## Test Commands

- Spec tests: `uv run pytest -q tests/test_skill.py tests/test_install_skill.py`
- Content tests: `uv run pytest -q tests/test_skill.py`
- Install tests: `uv run pytest -q tests/test_install_skill.py`
- All tests: `uv run pytest -q`
- Linter: `uv run ruff check && uv run mypy speclib/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Set up test file structure
    - Create `tests/test_skill.py` for skill file content tests (TS-05-1 through TS-05-13, TS-05-19 through TS-05-21)
    - Create `tests/test_install_skill.py` for install-skill command tests (TS-05-14 through TS-05-18)
    - Add fixtures to `tests/conftest.py` for temp home directory and patched home
    - _Test Spec: TS-05-1 through TS-05-21_

  - [x] 1.2 Translate skill content tests
    - One test function per TS-05-{1..13} and TS-05-{19..21}
    - Tests read the skill file and verify content structure, commands, sections
    - Tests MUST fail (skill file doesn't exist yet)
    - _Test Spec: TS-05-1 through TS-05-13, TS-05-19 through TS-05-21_

  - [x] 1.3 Translate install-skill tests
    - One test function per TS-05-{14..18}
    - Tests use Click test runner with patched home directories
    - Tests MUST fail (install-skill command doesn't exist yet)
    - _Test Spec: TS-05-14 through TS-05-18_

  - [x] 1.4 Translate edge-case tests
    - One test function per TS-05-E{1..9}
    - _Test Spec: TS-05-E1 through TS-05-E9_

  - [x] 1.5 Translate property tests
    - One property test per TS-05-P{1..3}
    - _Test Spec: TS-05-P1 through TS-05-P3_

  - [x] 1.6 Write integration smoke test
    - TS-05-SMOKE-1 (full install flow)
    - _Test Spec: TS-05-SMOKE-1_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings introduced: `uv run ruff check tests/`

- [x] 2. Create skill file and package structure
  - [x] 2.1 Create speclib/skill/ package
    - Create `speclib/skill/__init__.py` with `SKILL_FILE_PATH` constant
    - _Requirements: 05-REQ-1.1_

  - [x] 2.2 Write the skill prompt file
    - Create `speclib/skill/spec.md` with all required sections:
      - Header with skill name, description, trigger conditions
      - Command Reference section with all 9 commands and examples
      - Interactive Workflow section with numbered steps
      - One-Shot Workflow section
      - Question Handling section with ID parsing and answer mapping
      - Error Handling section with common errors and recovery
    - _Requirements: 05-REQ-1.1 through 05-REQ-1.5, 05-REQ-2.1 through 05-REQ-2.3,
      05-REQ-3.1, 05-REQ-3.2, 05-REQ-4.1 through 05-REQ-4.4,
      05-REQ-6.1 through 05-REQ-6.3_

  - [x] 2.V Verify task group 2
    - [x] Skill content tests pass: `uv run pytest -q tests/test_skill.py`
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check`

- [x] 3. Implement install-skill command
  - [x] 3.1 Implement detect_agent_cli()
    - Add `detect_agent_cli()` function to `speclib/skill/__init__.py`
    - Check `~/.claude/` and `~/.gemini/` directories
    - Return agent name or None
    - _Requirements: 05-REQ-5.1_

  - [x] 3.2 Implement install-skill CLI command
    - Add `install-skill` subcommand to `speclib/cli.py`
    - Accept `--target` option with choices `claude`, `gemini`
    - Copy skill file to detected or specified target
    - Create target directory if needed
    - Handle overwrite with "updated" message
    - Print success message with installed path
    - _Requirements: 05-REQ-5.2 through 05-REQ-5.5_

  - [x] 3.3 Handle all error conditions
    - No agent CLI detected without --target: error with supported list
    - Target directory missing: create it
    - Source file missing: raise SpeclibError
    - _Requirements: 05-REQ-5.E1 through 05-REQ-5.E3_

  - [x] 3.V Verify task group 3
    - [x] Install-skill tests pass: `uv run pytest -q tests/test_install_skill.py`
    - [x] Property tests pass: `uv run pytest -q tests/ -k property`
    - [x] Smoke test passes: `uv run pytest -q tests/ -k smoke`
    - [x] All existing tests still pass: `uv run pytest -q`
    - [x] No linter warnings introduced: `uv run ruff check && uv run mypy speclib/`

- [x] 4. Wiring verification

  - [x] 4.1 Trace execution path from design.md
    - Path 3: install-skill resolves SKILL_FILE_PATH → detects agent → copies file → prints message
    - Verify each step in the chain is exercised by TS-05-SMOKE-1
    - _Requirements: all_

  - [x] 4.2 Verify skill file content completeness
    - Manually inspect skill file against all 05-REQ-* content requirements
    - Ensure every command example is syntactically correct
    - Ensure workflow instructions match the session state machine from spec 02
    - _Requirements: all content requirements_

  - [x] 4.3 Stub / dead-code audit
    - Search speclib/skill/ for `pass`, `# TODO`, `NotImplementedError`
    - Each hit must be justified or replaced
    - _Requirements: all_

  - [x] 4.4 Cross-spec entry point verification
    - Verify `SKILL_FILE_PATH` is importable from `speclib.skill`
    - Verify `install-skill` subcommand appears in `spec --help` output
    - Verify skill file references to spec commands match the CLI defined in spec 04
    - _Requirements: all_

  - [x] 4.V Verify wiring group
    - [x] All smoke tests pass
    - [x] No unjustified stubs remain in speclib/skill/
    - [x] All execution paths from design.md are live
    - [x] All existing tests still pass: `uv run pytest -q`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 05-REQ-1.1 | TS-05-1 | 2.1, 2.2 | tests/test_skill.py::test_skill_file_exists |
| 05-REQ-1.2 | TS-05-2 | 2.2 | tests/test_skill.py::test_skill_header |
| 05-REQ-1.3 | TS-05-3 | 2.2 | tests/test_skill.py::test_documents_all_commands |
| 05-REQ-1.4 | TS-05-4 | 2.2 | tests/test_skill.py::test_command_examples |
| 05-REQ-1.5 | TS-05-5 | 2.2 | tests/test_skill.py::test_valid_markdown |
| 05-REQ-2.1 | TS-05-6 | 2.2 | tests/test_skill.py::test_interactive_workflow |
| 05-REQ-2.2 | TS-05-7 | 2.2 | tests/test_skill.py::test_assessment_presentation |
| 05-REQ-2.3 | TS-05-8 | 2.2 | tests/test_skill.py::test_accept_or_refine |
| 05-REQ-3.1 | TS-05-9 | 2.2 | tests/test_skill.py::test_one_shot_workflow |
| 05-REQ-3.2 | TS-05-10 | 2.2 | tests/test_skill.py::test_one_shot_result |
| 05-REQ-4.1 | TS-05-11 | 2.2 | tests/test_skill.py::test_question_id_parsing |
| 05-REQ-4.2 | TS-05-12 | 2.2 | tests/test_skill.py::test_natural_language_questions |
| 05-REQ-4.3 | TS-05-13 | 2.2 | tests/test_skill.py::test_answer_mapping |
| 05-REQ-4.4 | TS-05-13 | 2.2 | tests/test_skill.py::test_answer_mapping |
| 05-REQ-5.1 | TS-05-14 | 3.1 | tests/test_install_skill.py::test_detect_agent_cli |
| 05-REQ-5.2 | TS-05-15 | 3.2 | tests/test_install_skill.py::test_install_copies_file |
| 05-REQ-5.3 | TS-05-16 | 3.2 | tests/test_install_skill.py::test_install_with_target |
| 05-REQ-5.4 | TS-05-17 | 3.2 | tests/test_install_skill.py::test_install_overwrites |
| 05-REQ-5.5 | TS-05-18 | 3.2 | tests/test_install_skill.py::test_install_success_message |
| 05-REQ-6.1 | TS-05-19 | 2.2 | tests/test_skill.py::test_error_handling_section |
| 05-REQ-6.2 | TS-05-20 | 2.2 | tests/test_skill.py::test_exit_code_checking |
| 05-REQ-6.3 | TS-05-21 | 2.2 | tests/test_skill.py::test_status_check |
| 05-REQ-1.E1 | TS-05-E7 | 2.2 | tests/test_skill.py::test_unsupported_command_handling |
| 05-REQ-2.E1 | TS-05-E4 | 2.2 | tests/test_skill.py::test_zero_questions |
| 05-REQ-3.E1 | TS-05-E5 | 2.2 | tests/test_skill.py::test_one_shot_fallback |
| 05-REQ-4.E1 | TS-05-E8 | 2.2 | tests/test_skill.py::test_ambiguous_answer_clarification |
| 05-REQ-4.E2 | TS-05-E9 | 2.2 | tests/test_skill.py::test_partial_answers_handling |
| 05-REQ-5.E1 | TS-05-E1 | 3.3 | tests/test_install_skill.py::test_no_agent_detected |
| 05-REQ-5.E2 | TS-05-E2 | 3.3 | tests/test_install_skill.py::test_creates_missing_dir |
| 05-REQ-5.E3 | TS-05-E3 | 3.3 | tests/test_install_skill.py::test_missing_source |
| 05-REQ-6.E1 | TS-05-E6 | 2.2 | tests/test_skill.py::test_af_spec_not_on_path |
| Property 1 | TS-05-P1 | 2.1, 2.2 | tests/test_skill.py::test_property_package_complete |
| Property 2 | TS-05-P2 | 3.2 | tests/test_install_skill.py::test_property_installed_matches_source |
| Property 3 | TS-05-P3 | 2.2 | tests/test_skill.py::test_property_all_commands_documented |
| Path 3 | TS-05-SMOKE-1 | 3.2 | tests/test_install_skill.py::test_smoke_full_install |

## Notes

- The skill file is a static markdown asset; most tests are content-inspection
  rather than behavioral tests.
- Edge case tests for skill content (TS-05-E4 through TS-05-E9) verify that
  the skill file contains the relevant instructional text, not that the agent
  follows the instructions at runtime.
- The `install-skill` command reuses the existing Click CLI group from spec 04.
