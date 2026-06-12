---
spec_id: "02"
spec_name: "campaign_session"
title: "Campaign Management and Spec Authoring Session Model"
status: "draft"
created_at: "2026-06-09T12:00:00Z"
updated_at: "2026-06-09T12:00:00Z"
owner: "candlekeep"
source: "Input provided by user via interactive prompt"
supersedes: []
tags: ["campaign", "session", "persistence"]
intent_hash: null
schema_version: 1
---

# Campaign Management and Spec Authoring Session Model

## Intent

Implement the campaign directory management and spec authoring session model
that tracks the stateful lifecycle of creating one spec — from PRD input
through assessment, refinement, and generation.

## Goals

1. Implement the `Campaign` class for creating and managing campaign working
   directories containing one or more spec subdirectories.
2. Implement the `SpecSession` class that tracks the authoring lifecycle of a
   single spec within a campaign.
3. Persist session state to `_session.json` so interrupted sessions can be
   resumed.
4. Enforce a session state machine: init → assessing → refining →
   prd_accepted → generating → generated.
5. Manage spec directory naming with monotonically increasing numeric prefixes.

## Non-Goals

- Agent-driven assessment and generation (spec 03 — this spec provides the
  session interface; spec 03 implements the agent logic behind `assess()` and
  `generate()`).
- CLI commands (spec 04).
- Hub interaction (submit, import).
- Skill definition (spec 05).

## Background

Spec creation is a stateful, session-based process as defined in
services-architecture.md §7.1.1. A session starts with a PRD, uses an agent to
assess and refine it, then generates the remaining artifacts. The session state
is persisted in `_session.json` within the spec directory, enabling the user to
interrupt and resume authoring across CLI invocations.

The campaign directory is the working directory containing `campaign.yaml` and
one or more numbered spec subdirectories. Each spec has its own independent
session. Multiple specs can be authored in parallel within the same campaign.

This spec builds on `afspec` (speclib-python) for spec format models, I/O,
validation, and rendering, and on spec 01 for project structure and
configuration.

## Dependencies

| Spec | From Group | To Group | Relationship |
|------|-----------|----------|--------------|
| 01_project_scaffold | 2 | 1 | Uses speclib package structure and error hierarchy from group 2 |

## Design Decisions

1. **Session state machine:** States are `init`, `assessing`, `refining`,
   `prd_accepted`, `generating`, `generated`. Transitions are enforced; illegal
   transitions raise `SessionError`.
2. **Session persistence format:** `_session.json` is a JSON file with the
   session state, PRD path, assessment history, Q&A exchanges, and artifact
   generation status. It uses the same deterministic JSON serialization as
   afspec.
3. **Spec directory naming:** `{NN}_{snake_case_name}` where NN is
   `max(existing) + 1`. Names are validated against the pattern from
   spec-format v1.2 §3.1.
4. **Campaign metadata:** `campaign.yaml` stores name, description, created_at,
   updated_at. Minimal — the campaign is primarily a directory convention.
5. **PRD handling:** When `new_spec()` is called with a file path, the PRD is
   copied into the spec directory as `prd.md`. When called with a string, the
   string is written as `prd.md` with minimal frontmatter.
6. **Session does NOT contain agent logic.** The `assess()` and `generate()`
   methods are stubs in this spec that raise `NotImplementedError`. Spec 03
   provides the agent pipeline that these methods delegate to. This spec tests
   the session state machine and persistence independently of the agent.

## Source

Source: Input provided by user via interactive prompt
