# Implementation Plan: Coder Foundation & Provider Layer

<!-- AGENT INSTRUCTIONS
- Implement exactly ONE top-level task group per session
- Task group 1 writes failing tests from test_spec.md — all subsequent groups
  implement code to make those tests pass
- Follow the git-flow: feature branch from develop -> implement -> test -> merge to develop
- Update checkbox states as you go: [-] in progress, [x] complete
-->

## Overview

The implementation builds the coder package bottom-up: package scaffolding
first, then configuration, logging, providers, templates, prompt assembly,
and finally the CLI entry point. Task group 1 creates all failing tests.
Subsequent groups implement modules to make those tests pass.

## Test Commands

- Spec tests: `uv run pytest -q packages/coder/tests/ -v`
- Unit tests: `uv run pytest -q packages/coder/tests/ -v -k "not smoke"`
- Property tests: `uv run pytest -q packages/coder/tests/ -v -k "property"`
- All tests: `uv run pytest -q packages/coder/tests/ -v`
- Linter: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`

## Tasks

- [x] 1. Write failing spec tests
  - [x] 1.1 Create test file structure
    - Create `packages/coder/tests/__init__.py`
    - Create `packages/coder/tests/conftest.py` with shared fixtures
      (tmp directories, env var helpers, mock providers)
    - Create `packages/coder/tests/test_config.py`
    - Create `packages/coder/tests/test_providers.py`
    - Create `packages/coder/tests/test_registry.py`
    - Create `packages/coder/tests/test_templates.py`
    - Create `packages/coder/tests/test_prompts.py`
    - Create `packages/coder/tests/test_cli.py`
    - Create `packages/coder/tests/test_logging_setup.py`
    - Also created `packages/coder/tests/test_smoke.py`
    - _Test Spec: TS-12-1 through TS-12-19_

  - [x] 1.2 Translate acceptance-criterion tests
    - TS-12-1: Package importable
    - TS-12-2: Pyproject dependencies
    - TS-12-3: AnthropicProvider wraps ChatAnthropic
    - TS-12-4: GoogleProvider wraps ChatGoogleGenerativeAI
    - TS-12-5: OllamaProvider wraps ChatOllama
    - TS-12-6: Provider validates credentials
    - TS-12-7: Registry resolves claude- to Anthropic
    - TS-12-8: Registry resolves gemini- to Google
    - TS-12-9: Registry falls back to Ollama
    - TS-12-10: Config loads from YAML
    - TS-12-11: Env vars override YAML
    - TS-12-12: Template loader finds defaults
    - TS-12-13: Template loader prefers project override
    - TS-12-14: Template loader strips frontmatter
    - TS-12-15: Prompt assembler composes three layers
    - TS-12-16: Prompt assembler skips missing base
    - TS-12-17: CLI run validates campaign dir
    - TS-12-18: CLI run rejects missing dir
    - TS-12-19: Structured logging output
    - Also: TS-12-20 through TS-12-33
    - _Test Spec: TS-12-1 through TS-12-33_

  - [x] 1.3 Translate edge-case tests
    - TS-12-E1: Ollama server unreachable
    - TS-12-E2: Empty model name rejected
    - TS-12-E3: No config file uses defaults
    - TS-12-E4: Invalid YAML raises ConfigError
    - TS-12-E5: Template not found
    - TS-12-E6: Symlink template rejected
    - TS-12-E7: Unknown YAML keys warned
    - TS-12-E8: Build error on existing dir
    - TS-12-E9: Empty template returns empty
    - TS-12-E10: Provider creation failure at CLI
    - TS-12-E11: Log file not writable fallback
    - TS-12-E12: API key missing
    - TS-12-E13: Extra variables key ignored
    - TS-12-E14: Campaign dir does not exist
    - _Test Spec: TS-12-E1 through TS-12-E14_

  - [x] 1.4 Translate property tests
    - TS-12-P1: Provider resolution determinism
    - TS-12-P2: Configuration precedence
    - TS-12-P3: Template name security
    - TS-12-P4: Prompt layer order
    - TS-12-P5: Safe substitution
    - _Test Spec: TS-12-P1 through TS-12-P5_

  - [x] 1.5 Translate integration smoke tests
    - TS-12-SMOKE-1: CLI run resolves provider
    - TS-12-SMOKE-2: Prompt assembly end-to-end
    - _Test Spec: TS-12-SMOKE-1, TS-12-SMOKE-2_

  - [x] 1.V Verify task group 1
    - [x] All spec tests exist and are syntactically valid
    - [x] All spec tests FAIL (red) — no implementation yet
    - [x] No linter warnings: `uv run ruff check packages/coder/tests/`

- [x] 2. Package scaffolding & configuration
  - [x] 2.1 Create package structure
    - Create `packages/coder/pyproject.toml` with all dependencies
    - Create `packages/coder/coder/__init__.py` with version and exports
    - Update root `pyproject.toml` to include coder as workspace member
    - Run `uv sync` to verify workspace integration
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 2.2 Implement configuration system
    - Create `packages/coder/coder/config.py`
    - Implement `CoderConfig` pydantic model with all fields
    - Implement `load_config()` with YAML loading, env var overrides,
      and precedence chain
    - Implement unknown-key warning
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 2.3 Implement custom exceptions
    - Create `packages/coder/coder/errors.py`
    - Define: `ConfigError`, `ProviderConfigError`,
      `ProviderConnectionError`, `TemplateNotFoundError`,
      `TemplateSecurityError`
    - _Requirements: 2.E1, 2.E2, 4.E3, 5.E1, 5.5_

  - [x] 2.4 Implement structured logging
    - Create `packages/coder/coder/logging.py`
    - Implement `setup_logging(config)` with structlog + rich
    - Implement `get_logger(name)` function
    - Console renderer with timestamps, level, module, event
    - Optional file sink
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 2.V Verify task group 2
    - [x] Spec tests pass: TS-12-1, TS-12-2, TS-12-10, TS-12-11, TS-12-19
    - [x] Edge case tests pass: TS-12-E3, TS-12-E4, TS-12-E7
    - [x] Property tests pass: TS-12-P2
    - [x] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [x] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [x] Requirements 1.1, 1.2, 1.3, 4.1-4.5, 8.1-8.5 met

- [ ] 3. LLM providers & registry
  - [ ] 3.1 Implement LLMProvider interface and providers
    - Create `packages/coder/coder/providers.py`
    - Define `LLMProvider` protocol with `model_name`, `invoke()`,
      `validate()` methods
    - Implement `AnthropicProvider` wrapping `ChatAnthropic`
    - Implement `GoogleProvider` wrapping `ChatGoogleGenerativeAI`
    - Implement `OllamaProvider` wrapping `ChatOllama`
    - Credential validation in each provider constructor
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 3.2 Implement ProviderRegistry
    - Create `packages/coder/coder/registry.py`
    - Implement prefix-based resolution (claude- → Anthropic,
      gemini- → Google, fallback → Ollama)
    - Implement custom registration via config
    - Implement `list_models()` for the CLI
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 3.V Verify task group 3
    - [ ] Spec tests pass: TS-12-3 through TS-12-9
    - [ ] Edge case tests pass: TS-12-E1, TS-12-E2
    - [ ] Property tests pass: TS-12-P1
    - [ ] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [ ] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [ ] Requirements 2.1-2.5, 3.1-3.5 met

- [ ] 4. Prompt templates & assembly
  - [ ] 4.1 Implement TemplateLoader
    - Create `packages/coder/coder/templates.py`
    - Implement search path resolution (project → package)
    - Implement name validation (regex, no traversal)
    - Implement symlink rejection
    - Implement frontmatter stripping
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 4.2 Create default prompt templates
    - Create `packages/coder/coder/_templates/agent.md` — base agent profile
    - Create `packages/coder/coder/_templates/coder.md` — coding persona
    - Create `packages/coder/coder/_templates/reviewer.md` — reviewer persona
    - _Requirements: 5.6_

  - [ ] 4.3 Implement PromptAssembler
    - Create `packages/coder/coder/prompts.py`
    - Implement 3-layer composition (base + persona + context)
    - Implement `$variable` substitution via `string.Template`
    - Handle missing base profile gracefully
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 4.V Verify task group 4
    - [ ] Spec tests pass: TS-12-12 through TS-12-16
    - [ ] Edge case tests pass: TS-12-E5, TS-12-E6
    - [ ] Property tests pass: TS-12-P3, TS-12-P4, TS-12-P5
    - [ ] Smoke test pass: TS-12-SMOKE-2
    - [ ] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [ ] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [ ] Requirements 5.1-5.6, 6.1-6.4 met

- [ ] 5. CLI entry point
  - [ ] 5.1 Implement CLI commands
    - Create `packages/coder/coder/cli.py`
    - Implement `coder` Click group
    - Implement `coder run` subcommand with arguments:
      `campaign_dir`, `--model`, `--repo`
    - Implement `coder models` subcommand
    - Register console script entry point in pyproject.toml
    - Wire up config loading, provider creation, logging setup
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ] 5.V Verify task group 5
    - [ ] Spec tests pass: TS-12-17, TS-12-18
    - [ ] Smoke test pass: TS-12-SMOKE-1
    - [ ] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`
    - [ ] No linter warnings: `uv run ruff check packages/coder/ && uv run mypy packages/coder/coder/`
    - [ ] Requirements 7.1-7.5 met

- [ ] 6. Wiring verification

  - [ ] 6.1 Trace every execution path from design.md end-to-end
    - Path 1: CLI invocation → config → logging → registry → provider
    - Path 2: Prompt assembly → template loader → assembler → output
    - Path 3: List models → registry → formatted output
    - Verify each function in the chain is called (not stubbed)
    - _Requirements: all_

  - [ ] 6.2 Verify return values propagate correctly
    - `load_config()` → `CoderConfig` consumed by CLI
    - `ProviderRegistry.resolve()` → `LLMProvider` consumed by caller
    - `TemplateLoader.load()` → `str` consumed by `PromptAssembler`
    - `PromptAssembler.assemble()` → `str` consumed by caller
    - Grep for callers of each function; confirm return values are used
    - _Requirements: all_

  - [ ] 6.3 Run the integration smoke tests
    - TS-12-SMOKE-1: CLI run resolves provider (real registry, no mock)
    - TS-12-SMOKE-2: Prompt assembly end-to-end (real filesystem)
    - _Test Spec: TS-12-SMOKE-1, TS-12-SMOKE-2_

  - [ ] 6.4 Stub / dead-code audit
    - Search all files in `packages/coder/coder/` for:
      `return []`, `return None` on non-Optional returns, `pass` in
      non-abstract methods, `# TODO`, `# stub`, `NotImplementedError`
    - Each hit must be justified or replaced
    - _Requirements: all_

  - [ ] 6.5 Cross-spec entry point verification
    - Verify `ProviderRegistry.resolve()` is callable from spec 14 code
    - Verify `PromptAssembler.assemble()` is callable from spec 14 code
    - Verify `load_config()` is callable from spec 13/14 code
    - _Requirements: all_

  - [ ] 6.V Verify wiring group
    - [ ] All smoke tests pass
    - [ ] No unjustified stubs remain in `packages/coder/coder/`
    - [ ] All execution paths from design.md are live
    - [ ] All existing tests still pass: `uv run pytest -q packages/coder/tests/ -v`

## Traceability

| Requirement | Test Spec Entry | Implemented By Task | Verified By Test |
|-------------|-----------------|---------------------|------------------|
| 12-REQ-1.1 | TS-12-1 | 2.1 | test_config.py::test_package_importable |
| 12-REQ-1.2 | TS-12-2 | 2.1 | test_config.py::test_pyproject_dependencies |
| 12-REQ-2.2 | TS-12-3 | 3.1 | test_providers.py::test_anthropic_wraps_chat |
| 12-REQ-2.3 | TS-12-4 | 3.1 | test_providers.py::test_google_wraps_chat |
| 12-REQ-2.4 | TS-12-5 | 3.1 | test_providers.py::test_ollama_wraps_chat |
| 12-REQ-2.5 | TS-12-6 | 3.1 | test_providers.py::test_credential_validation |
| 12-REQ-2.E1 | TS-12-E1 | 3.1 | test_providers.py::test_ollama_unreachable |
| 12-REQ-2.E2 | TS-12-6 | 3.1 | test_providers.py::test_credential_validation |
| 12-REQ-3.2 | TS-12-7 | 3.2 | test_registry.py::test_claude_prefix |
| 12-REQ-3.3 | TS-12-8 | 3.2 | test_registry.py::test_gemini_prefix |
| 12-REQ-3.4 | TS-12-9 | 3.2 | test_registry.py::test_ollama_fallback |
| 12-REQ-3.E1 | TS-12-E2 | 3.2 | test_registry.py::test_empty_model_name |
| 12-REQ-4.1 | TS-12-10 | 2.2 | test_config.py::test_yaml_loading |
| 12-REQ-4.4 | TS-12-11 | 2.2 | test_config.py::test_env_override |
| 12-REQ-4.E1 | TS-12-E7 | 2.2 | test_config.py::test_unknown_keys_warned |
| 12-REQ-4.E2 | TS-12-E3 | 2.2 | test_config.py::test_no_config_defaults |
| 12-REQ-4.E3 | TS-12-E4 | 2.2 | test_config.py::test_invalid_yaml |
| 12-REQ-5.1 | TS-12-12 | 4.1 | test_templates.py::test_load_package_default |
| 12-REQ-5.2 | TS-12-13 | 4.1 | test_templates.py::test_project_override |
| 12-REQ-5.3 | TS-12-14 | 4.1 | test_templates.py::test_frontmatter_stripped |
| 12-REQ-5.4 | TS-12-P3 | 4.1 | test_templates.py::test_property_path_traversal |
| 12-REQ-5.5 | TS-12-E6 | 4.1 | test_templates.py::test_symlink_rejected |
| 12-REQ-5.6 | TS-12-12 | 4.2 | test_templates.py::test_load_package_default |
| 12-REQ-5.E1 | TS-12-E5 | 4.1 | test_templates.py::test_not_found |
| 12-REQ-6.1 | TS-12-15 | 4.3 | test_prompts.py::test_three_layers |
| 12-REQ-6.2 | TS-12-16 | 4.3 | test_prompts.py::test_skip_base |
| 12-REQ-6.3 | TS-12-P5 | 4.3 | test_prompts.py::test_property_substitution |
| 12-REQ-6.E1 | TS-12-P5 | 4.3 | test_prompts.py::test_property_substitution |
| 12-REQ-7.1 | TS-12-17 | 5.1 | test_cli.py::test_run_command |
| 12-REQ-7.3 | TS-12-17 | 5.1 | test_cli.py::test_run_command |
| 12-REQ-7.E1 | TS-12-18 | 5.1 | test_cli.py::test_missing_campaign_dir |
| 12-REQ-8.1 | TS-12-19 | 2.4 | test_logging_setup.py::test_structured_output |
| 12-REQ-8.4 | TS-12-19 | 2.4 | test_logging_setup.py::test_structured_output |
| 12-REQ-1.3 | TS-12-20 | 2.1 | test_config.py::test_root_pyproject_workspace_member |
| 12-REQ-1.E1 | TS-12-E8 | 2.1 | test_config.py::test_build_error_on_existing_dir |
| 12-REQ-2.1 | TS-12-21 | 3.1 | test_providers.py::test_llmprovider_interface |
| 12-REQ-3.1 | TS-12-22 | 3.2 | test_registry.py::test_registry_returns_provider |
| 12-REQ-3.5 | TS-12-23 | 3.2 | test_registry.py::test_custom_registration |
| 12-REQ-4.2 | TS-12-24 | 2.2 | test_config.py::test_config_all_keys |
| 12-REQ-4.3 | TS-12-25 | 2.2 | test_config.py::test_env_var_coder_prefix |
| 12-REQ-4.5 | TS-12-26 | 2.2 | test_config.py::test_config_frozen_pydantic |
| 12-REQ-5.E2 | TS-12-E9 | 4.1 | test_templates.py::test_empty_template_returns_empty |
| 12-REQ-6.4 | TS-12-27 | 4.3 | test_prompts.py::test_assemble_accepts_variables |
| 12-REQ-7.2 | TS-12-28 | 5.1 | test_cli.py::test_run_arguments |
| 12-REQ-7.4 | TS-12-29 | 5.1 | test_cli.py::test_models_subcommand |
| 12-REQ-7.5 | TS-12-30 | 5.1 | test_cli.py::test_run_help |
| 12-REQ-7.E2 | TS-12-E10 | 5.1 | test_cli.py::test_provider_creation_failure |
| 12-REQ-8.2 | TS-12-31 | 2.4 | test_logging_setup.py::test_default_debug_level |
| 12-REQ-8.3 | TS-12-32 | 2.4 | test_logging_setup.py::test_log_to_file |
| 12-REQ-8.5 | TS-12-33 | 2.4 | test_logging_setup.py::test_get_logger |
| 12-REQ-8.E1 | TS-12-E11 | 2.4 | test_logging_setup.py::test_unwritable_log_fallback |

## Notes

- Provider tests should mock LangChain chat model constructors to avoid
  requiring real API keys in CI, except for credential validation tests
  which explicitly test the absence of keys.
- Template tests use `tmp_path` fixtures for isolated filesystem operations.
- The CLI smoke test (TS-12-SMOKE-1) mocks only the LLM `invoke()` call,
  not the provider creation or config loading.
- Property tests use Hypothesis with the `text()` strategy for model names
  and template names.
