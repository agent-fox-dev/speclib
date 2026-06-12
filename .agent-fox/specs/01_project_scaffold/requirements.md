# Requirements Document

## Introduction

This specification defines the project scaffold, configuration subsystem, and
Anthropic client factory for the speclib project. These are foundational
components that all other speclib features depend on.

## Glossary

| Term | Definition |
|------|-----------|
| speclib | The Python package being built — the spec creation tool |
| afspec | The existing Python library (speclib-python) implementing spec-format v1.2 |
| uv | The Python package manager and project tool used for installation and dependency management |
| settings.yaml | The YAML configuration file at `~/.af/settings.yaml` for af tool configuration |
| Anthropic client | An instance of the Anthropic Python SDK client (Anthropic, AnthropicVertex, or AnthropicBedrock) |
| Vertex AI | Google Cloud's managed AI platform, providing access to Claude models |
| Bedrock | AWS's managed AI service, providing access to Claude models |

## Requirements

### Requirement 1: Project Package Structure

**User Story:** As a developer, I want a properly structured Python package with uv-managed dependencies, so that I can install and develop speclib reliably.

#### Acceptance Criteria
1. [01-REQ-1.1] THE speclib package SHALL be installable via `uv pip install` from a local path or git URL, producing a working `spec` CLI entry point.
2. [01-REQ-1.2] THE pyproject.toml SHALL declare `afspec` (speclib-python), `anthropic`, `click`, and `pyyaml` as runtime dependencies with minimum version constraints.
3. [01-REQ-1.3] THE pyproject.toml SHALL declare `pytest`, `hypothesis`, `ruff`, and `mypy` as dev dependencies.
4. [01-REQ-1.4] THE pyproject.toml SHALL set `requires-python = ">=3.14"`.
5. [01-REQ-1.5] WHEN `make check` is invoked, THE build system SHALL run the linter (`ruff check`) and the full test suite (`uv run pytest -q`) in sequence, exiting with non-zero status if either fails.
6. [01-REQ-1.6] WHEN `make test` is invoked, THE build system SHALL run `uv run pytest -q` and exit with the test runner's exit code.

#### Edge Cases
1. [01-REQ-1.E1] IF `uv` is not installed on the system, THEN THE installation process SHALL fail with a clear error message rather than falling back to pip.

### Requirement 2: Configuration Loading

**User Story:** As a user, I want speclib to load configuration from a YAML file and environment variables, so that I can configure the tool consistently with other af tools.

#### Acceptance Criteria
1. [01-REQ-2.1] WHEN speclib loads configuration, THE system SHALL read `~/.af/settings.yaml` if it exists and parse the `spec_tool` section.
2. [01-REQ-2.2] WHEN speclib loads configuration, THE system SHALL check environment variables (`AF_SPEC_MODEL`, `AF_SPEC_AUTH`, `ANTHROPIC_API_KEY`) and override any corresponding values from settings.yaml.
3. [01-REQ-2.3] THE configuration module SHALL return a `SpecToolConfig` object containing at minimum: `model` (str), `auth_method` (str), and `api_key` (str | None) fields.
4. [01-REQ-2.4] WHEN no configuration file exists and no environment variables are set, THE system SHALL use default values: model=`claude-sonnet-4-6`, auth_method=`api_key`, api_key=None.

#### Edge Cases
1. [01-REQ-2.E1] IF `~/.af/settings.yaml` exists but contains invalid YAML, THEN THE system SHALL raise a `ConfigError` with the file path and parse error detail.
2. [01-REQ-2.E2] IF `~/.af/settings.yaml` exists but has no `spec_tool` section, THEN THE system SHALL use default values for all spec_tool settings without raising an error.
3. [01-REQ-2.E3] IF the `spec_tool` section contains unknown keys, THEN THE system SHALL ignore them without raising an error.

### Requirement 3: Anthropic Client Factory

**User Story:** As a user, I want speclib to autodetect my Anthropic authentication setup, so that I can use the tool with an API key, Google Vertex AI, or AWS Bedrock without manual configuration.

#### Acceptance Criteria
1. [01-REQ-3.1] WHEN `ANTHROPIC_API_KEY` is set and `AF_SPEC_AUTH` is not set or is `api_key`, THE client factory SHALL return an `anthropic.Anthropic` instance configured with that key.
2. [01-REQ-3.2] WHEN `AF_SPEC_AUTH` is `bedrock`, THE client factory SHALL return an `anthropic.AnthropicBedrock` instance, using AWS credentials from the environment (standard boto3 credential chain).
3. [01-REQ-3.3] WHEN `AF_SPEC_AUTH` is `vertex`, THE client factory SHALL return an `anthropic.AnthropicVertex` instance, using GCP credentials from the environment (standard google-auth credential chain) and the `AF_SPEC_VERTEX_PROJECT` and `AF_SPEC_VERTEX_REGION` environment variables.
4. [01-REQ-3.4] THE client factory SHALL accept an optional `SpecToolConfig` parameter, using its values as fallbacks when environment variables are not set, and SHALL return the appropriate client instance AND the resolved model name as a tuple.
5. [01-REQ-3.5] WHEN the config specifies `auth_method` in settings.yaml and no `AF_SPEC_AUTH` env var overrides it, THE client factory SHALL use the settings.yaml value to select the client type.

#### Edge Cases
1. [01-REQ-3.E1] IF `AF_SPEC_AUTH` is set to an unrecognized value, THEN THE client factory SHALL raise a `ConfigError` listing the valid auth methods (`api_key`, `bedrock`, `vertex`).
2. [01-REQ-3.E2] IF the selected auth method is `api_key` but no `ANTHROPIC_API_KEY` is set and no key is in settings.yaml, THEN THE client factory SHALL raise a `ConfigError` explaining that an API key is required.
3. [01-REQ-3.E3] IF the selected auth method is `vertex` but `AF_SPEC_VERTEX_PROJECT` is not set, THEN THE client factory SHALL raise a `ConfigError` explaining the required environment variables.

### Requirement 4: Exception Hierarchy

**User Story:** As a developer, I want a consistent exception hierarchy for speclib, so that errors are distinguishable and actionable.

#### Acceptance Criteria
1. [01-REQ-4.1] THE speclib package SHALL define a base `SpeclibError` exception that all speclib-specific exceptions inherit from.
2. [01-REQ-4.2] THE speclib package SHALL define a `ConfigError` exception (inheriting from `SpeclibError`) for configuration and authentication errors.

#### Edge Cases
(None — exception hierarchy is structural.)

## Source

Source: Input provided by user via interactive prompt
