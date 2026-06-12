---
spec_id: "01"
spec_name: "project_scaffold"
title: "Project Scaffold, Configuration, and Anthropic Client Factory"
status: "draft"
created_at: "2026-06-09T12:00:00Z"
updated_at: "2026-06-09T12:00:00Z"
owner: "candlekeep"
source: "Input provided by user via interactive prompt"
supersedes: []
tags: ["foundation", "config", "auth"]
intent_hash: null
schema_version: 1
---

# Project Scaffold, Configuration, and Anthropic Client Factory

## Intent

Establish the speclib Python project with its package structure, build
configuration, dependency management via uv, and the foundational configuration
and authentication subsystem that all other specs depend on.

## Goals

1. Create a fully functional Python package (`speclib`) installable via `uv`.
2. Integrate `afspec` (speclib-python) as a dependency, reusing its models,
   validation, rendering, lifecycle, and I/O capabilities.
3. Provide a configuration module that loads settings from `~/.af/settings.yaml`
   and environment variables with a well-defined precedence order.
4. Provide an Anthropic client factory that autodetects whether to use a direct
   API key, Google Vertex AI, or AWS Bedrock, and returns the appropriate
   client instance.

## Non-Goals

- CLI implementation (spec 04).
- Campaign or session management (spec 02).
- Agent-driven assessment or generation (spec 03).
- Skill definition (spec 05).
- Hub interaction or network services.

## Background

The speclib project is the standalone spec creation tool for authoring spec
packages as defined by spec-format v1.2. It builds on top of `afspec`
(speclib-python), which already implements the spec format's data models,
validation, rendering, I/O, and lifecycle management. speclib adds campaign
management, session state, AI-driven assessment/generation, a CLI, and an
agent skill.

This spec covers the foundational infrastructure: project layout, build system,
configuration loading, and authentication. All other specs depend on this one
being complete.

## Design Decisions

1. **Package name:** `speclib`. The CLI entry point is `spec` (matching the
   architecture specification).
2. **Build system:** `hatchling` (same as afspec) with `uv` as the only
   supported installer. No pip.
3. **Python version:** 3.14+ as required.
4. **CLI framework:** Click, installed as a dependency. Used by spec 04.
5. **Config file format:** YAML (`~/.af/settings.yaml`), consistent with the
   af hub configuration format defined in services-architecture.md.
6. **Auth autodetect order:** Environment variables checked in order:
   (a) `ANTHROPIC_API_KEY` → direct API client, (b) `AF_SPEC_AUTH=bedrock` +
   AWS credentials → Bedrock client, (c) `AF_SPEC_AUTH=vertex` + GCP
   credentials → Vertex client. Falls back to settings.yaml `spec_tool.auth`
   if env vars are not set.
7. **Default model:** `claude-sonnet-4-6` as specified in
   services-architecture.md §7.1.3.
8. **Config precedence:** Environment variables override settings.yaml values.

## Source

Source: Input provided by user via interactive prompt
