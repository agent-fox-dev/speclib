---
spec_id: "05"
spec_name: "spec_skill"
title: "Agent CLI Skill for Spec Authoring"
status: "draft"
created_at: "2026-06-09T12:00:00Z"
updated_at: "2026-06-09T12:00:00Z"
owner: "candlekeep"
source: "Input provided by user via interactive prompt"
supersedes: []
tags: ["skill", "agent", "cli"]
intent_hash: null
schema_version: 1
---

# Agent CLI Skill for Spec Authoring

## Intent

Provide a self-contained agent skill (markdown prompt file) that exposes
speclib's spec authoring capabilities to agent CLIs such as Claude Code and
Gemini CLI, along with a small installation utility to deploy the skill file
to the appropriate agent configuration directory.

## Goals

1. Create a skill prompt file (`speclib/skill/spec.md`) that instructs
   agent CLIs how to drive the spec authoring workflow using `spec` CLI
   commands.
2. Support interactive mode (step-by-step authoring with user conversation)
   and one-shot mode (PRD in, spec out) within the skill.
3. Provide clear instructions for presenting assessment questions
   conversationally and mapping natural language answers to structured
   Question IDs.
4. Provide an `spec install-skill` CLI command that copies the skill file
   to the detected agent CLI's skill directory.

## Non-Goals

- Implementing the Python API directly in the skill (the skill uses CLI
  commands only).
- Hub interaction (the skill only invokes `spec submit` when the user
  explicitly asks).
- Modifying agent CLI configuration beyond copying the skill file.
- Supporting agent CLIs other than Claude Code and Gemini CLI at launch
  (extensible later).

## Background

Agent CLIs like Claude Code support "skills" — markdown files that provide
domain-specific instructions to the agent. When a skill is loaded, the agent
receives its content as context and follows the described workflows.

The speclib spec skill enables agents to author specs by driving the
`spec` CLI. This avoids requiring agents to call the Python API directly,
keeping the interface stable and testable. The skill describes two workflows
(interactive and one-shot), explains how to present questions to users, and
includes examples of every relevant `spec` command.

The skill depends on the campaign/session model (spec 02) for the underlying
data structures and the CLI (spec 04) for the commands it invokes.

## Dependencies

| Spec | From Group | To Group | Relationship |
|------|-----------|----------|--------------|
| 02_campaign_session | 3 | 2 | Skill drives the session model via CLI commands |
| 04_af_spec_cli | 3 | 2 | Skill invokes spec CLI commands |

## Design Decisions

1. **Skill is a markdown prompt file.** The skill is a single `.md` file
   that agent CLIs load as context. It contains no executable code — only
   instructions, examples, and workflow descriptions.
2. **CLI commands only.** The skill instructs the agent to use `spec`
   CLI commands rather than calling the Python API. This keeps the skill
   decoupled from internal implementation details.
3. **Conversational question mapping.** When the assessment produces
   questions, the skill instructs the agent to present them naturally in
   conversation, then map user responses to Question IDs for the `refine`
   command.
4. **Shipped inside the package.** The skill file lives at
   `speclib/skill/spec.md` and is included in the Python package. An
   `spec install-skill` command copies it to the target location.
5. **Agent CLI detection.** The install command detects the agent CLI by
   checking for known configuration directories (`~/.claude/` for Claude
   Code, `~/.gemini/` for Gemini CLI) and copies the skill to the
   appropriate subdirectory.

## Source

Source: Input provided by user via interactive prompt
