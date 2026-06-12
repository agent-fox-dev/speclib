---
spec_id: "04"
spec_name: "af_spec_cli"
title: "spec CLI — Local Spec Authoring Commands"
status: "draft"
created_at: "2026-06-09T12:00:00Z"
updated_at: "2026-06-09T12:00:00Z"
owner: "candlekeep"
source: "Input provided by user via interactive prompt"
supersedes: []
tags: ["cli", "click", "local"]
intent_hash: null
schema_version: 1
---

# spec CLI — Local Spec Authoring Commands

## Intent

Implement the `spec` command-line interface using the Click framework,
providing local-only campaign management and spec authoring commands that wrap
the speclib library. This is the primary user-facing interface for creating,
assessing, refining, and generating specs without requiring network access or
hub interaction.

## Goals

1. Provide a Click-based CLI entry point (`spec`) with a top-level command
   group and subcommands for all local spec authoring operations.
2. Implement campaign management commands (`init`, `list`) for creating and
   inspecting campaign working directories.
3. Implement spec authoring commands (`new`, `assess`, `refine`, `accept`,
   `generate`, `validate`, `render`, `show`, `status`) that drive the spec
   session lifecycle through the speclib library.
4. Provide clear, formatted output for tables (list, status), assessment
   summaries, validation errors, and rendered markdown.
5. Enforce working directory conventions: commands operate relative to CWD or a
   `--campaign-dir` override, and require a valid campaign directory.
6. Deliver actionable error messages for common user mistakes (wrong directory,
   missing spec, wrong session state).

## Non-Goals

- Hub commands (`submit`, `import`) — these are out of scope for this spec
  and will be added in a future spec if needed.
- Spec format internals — handled by afspec (speclib-python).
- Agent logic — handled by spec 03 (agent pipeline). The CLI delegates to
  speclib's session and agent layer.
- Configuration and authentication — handled by spec 01 (project scaffold).
- Campaign and session model internals — handled by spec 02.

## Background

The `spec` CLI is the primary user interface for the speclib project. It is
defined in `pyproject.toml` as `spec = speclib.cli:main` and is installed
as a console script when the package is installed via `uv`.

The CLI wraps the speclib library, specifically the `Campaign` class (spec 02)
for campaign management, the `SpecSession` class (spec 02) for session state
management, and the agent pipeline (spec 03) for AI-driven assessment and
generation. The CLI is responsible for argument parsing, output formatting, and
error presentation — it contains no business logic.

The working directory convention requires that most commands are run from
within a campaign directory (one containing `campaign.yaml`). The
`--campaign-dir` flag on the top-level command group allows overriding this.

The `<spec>` argument used by authoring commands can be either the full
directory name (e.g., `01_data_models`) or just the numeric prefix (e.g.,
`01`). The CLI resolves this to the actual spec directory by scanning the
campaign.

## Dependencies

| Spec | From Group | To Group | Relationship |
|------|-----------|----------|--------------|
| 01_project_scaffold | 2 | 1 | Uses speclib package structure, CLI entry point stub, error hierarchy |
| 02_campaign_session | 3 | 2 | Uses Campaign and SpecSession classes for all operations |
| 03_agent_pipeline | 3 | 2 | Uses agent pipeline for assess, refine, generate operations |

## Design Decisions

1. **Click framework:** The CLI uses `@click.group()` for the main entry point
   and `@click.command()` for each subcommand. Click was chosen for its
   decorator-based API, automatic help generation, and type conversion.
2. **Subcommand structure:** Each CLI operation is a standalone Click command
   function. Campaign commands and spec authoring commands are all at the
   top level (flat namespace, not nested groups).
3. **Async bridging:** Operations that call the agent pipeline (`assess`,
   `refine`, `generate`) are async in speclib. The CLI bridges Click's
   synchronous interface using `asyncio.run()`.
4. **Campaign directory resolution:** The `--campaign-dir` option is defined on
   the `@click.group()` and stored in the Click context. Defaults to CWD.
   Validated before any subcommand runs.
5. **Spec argument resolution:** The `<spec>` argument is resolved by scanning
   for a directory matching by name or numeric prefix. If no match is found,
   the CLI lists available specs and exits with code 1.
6. **Exit codes:** 0 = success, 1 = user error (bad args, wrong state, not
   found), 2 = internal error (unexpected exception).
7. **Output formatting:** Uses Rich (optional dependency) or plain text for
   table formatting (list, status), colored output (assessment), and error
   display. Falls back gracefully when Rich is not available.
8. **Error presentation:** Errors from speclib (CampaignError, SessionError,
   ValidationError) are caught at the CLI boundary and presented as
   user-friendly messages with suggestions, not raw tracebacks.

## Source

Source: Input provided by user via interactive prompt
