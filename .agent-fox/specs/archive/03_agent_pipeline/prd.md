---
spec_id: "03"
spec_name: "agent_pipeline"
title: "Agent Pipeline: PRD Assessment, Refinement, and Artifact Generation"
status: "draft"
created_at: "2026-06-09T12:00:00Z"
updated_at: "2026-06-09T12:00:00Z"
owner: "candlekeep"
source: "Input provided by user via interactive prompt"
supersedes: []
tags: ["agent", "assessment", "generation", "anthropic"]
intent_hash: null
schema_version: 1
---

# Agent Pipeline: PRD Assessment, Refinement, and Artifact Generation

## Intent

Implement the AI-driven operations that power spec authoring: assessing a PRD
for quality and completeness, refining the PRD through interactive Q&A, and
generating the three derived spec artifacts (requirements.json, test_spec.json,
tasks.json) using the Anthropic messages API with structured output via tool
use.

## Goals

1. Implement a `SpecAgent` class that wraps the Anthropic client and provides
   async methods for PRD assessment, PRD refinement, and artifact generation.
2. Implement prompt templates that instruct the agent to evaluate PRDs against
   the spec-format v1.2 expectations (Intent, Goals, Non-Goals, Background
   sections) and produce structured assessments.
3. Implement tool definitions for structured output so the agent returns
   well-typed JSON matching the `Assessment`, `Question`, and artifact schemas.
4. Wire the agent pipeline into `SpecSession` so that `assess()`, `refine()`,
   and `generate()` delegate to `SpecAgent` methods and persist results.
5. Handle transient API errors (rate limits, server errors) with retry logic
   and surface permanent failures as `AgentError`.

## Non-Goals

- CLI commands for invoking the agent (spec 04).
- Skill invocation or MCP tool definition (spec 05).
- Hub interaction (submit, import).
- Agent-driven repair of validation errors (repair is deterministic Python
  logic, not agent-driven).
- Streaming of partial responses to the CLI (the agent returns complete
  responses; spec 04 handles progress display).

## Background

The speclib tool follows a three-phase authoring workflow defined in
services-architecture.md SS7.1.3:

1. **Assessment** -- The user provides a PRD. The agent evaluates it against
   spec-format expectations and produces an Assessment with a quality verdict
   ("ready", "needs_refinement", "incomplete"), a summary, identified gaps,
   and structured Questions for the user.

2. **Refinement** -- The user answers the agent's Questions. The agent
   incorporates the answers into an updated PRD and re-assesses. This loop
   repeats until the PRD is accepted (quality = "ready") or the user manually
   accepts it.

3. **Generation** -- Once the PRD is accepted, the agent generates the three
   remaining artifacts in sequence: requirements.json, then test_spec.json,
   then tasks.json. Each artifact is validated against its JSON schema before
   proceeding to the next. Cross-file integrity validation runs after all
   three exist.

The agent uses the Anthropic messages API with tool use (function calling) to
produce structured output. The tool definitions constrain the JSON shape of
assessments and artifacts, ensuring machine-parseable results.

This spec depends on spec 01 (project scaffold, configuration, client factory)
for the Anthropic client and on spec 02 (campaign/session model) for the
session types (Assessment, Question, SessionState) and the SpecSession
interface that the agent pipeline integrates into.

## Dependencies

| Spec | From Group | To Group | Relationship |
|------|-----------|----------|--------------|
| 01_project_scaffold | 3 | 3 | Uses `create_client()` from speclib.auth for the Anthropic client |
| 02_campaign_session | 3 | 2 | Uses `Assessment`, `Question`, `SpecSession`, `SessionState` types |

## Design Decisions

1. **Async API using asyncio:** The Anthropic Python SDK supports async
   natively. All agent methods are async to avoid blocking the event loop
   during API calls. Callers (CLI, skill) are responsible for running the
   event loop.
2. **Structured output via tool_use:** The assessment prompt instructs the
   agent to call a tool (e.g., `submit_assessment`) whose input schema
   matches the Assessment type. This avoids fragile text parsing.
3. **Sequential artifact generation:** Artifacts are generated one at a time
   in dependency order (requirements -> test_spec -> tasks). This is
   deliberate: later artifacts can reference earlier ones for consistency
   (e.g., test_spec references requirement IDs, tasks reference both).
4. **Retry with exponential backoff:** Transient API errors (HTTP 429, 5xx)
   are retried up to 3 times with exponential backoff. Permanent errors
   (4xx other than 429, malformed tool responses) surface immediately as
   `AgentError`.
5. **Per-artifact validation:** Each generated artifact is validated against
   its JSON schema before the next artifact is generated. If validation
   fails, the generation is aborted and the error is returned so the user
   can inspect what went wrong.
6. **Deterministic repair, not agent-driven:** The repair module
   (`speclib/repair.py`) uses deterministic Python logic to suggest and apply
   fixes to validation errors. It is not part of the agent pipeline.

## Source

Source: Input provided by user via interactive prompt
