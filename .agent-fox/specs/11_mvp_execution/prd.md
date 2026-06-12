---
spec_id: "11"
spec_name: "mvp_execution"
title: "MVP Spec Execution — Local CLI"
status: draft
created_at: "2026-06-12T20:00:00Z"
updated_at: "2026-06-12T21:00:00Z"
owner: "michael"
source: "Architecture decision to build a minimalistic MVP that can execute a spec pack locally"
supersedes: []
tags: ["mvp", "execution", "cli"]
intent_hash: null
schema_version: 1
---

## Background

The af-core project has a working spec authoring pipeline: the `spec` CLI
drives speclib to create campaigns, assess PRDs, generate requirements /
test_spec / tasks artifacts, and validate spec packages. What does not
exist yet is the execution side — taking an approved spec pack and running
an agent to implement it.

The full architecture (docs/runtime-layer.md, docs/coordination-layer.md,
docs/services-architecture.md) envisions a hub, sandboxes, the af SDK, a
two-tier harness adapter model, campaigns with dependency graphs, and
multi-agent orchestration. None of that is needed for an MVP. The goal is
the simplest possible execution path that is still spec-driven and correct.

The existing packages are:

- `packages/afspec/` — spec format models, validation, rendering, lifecycle,
  discovery
- `packages/speclib/` — agent pipeline (assessment, generation), sessions,
  campaigns
- `packages/spec-cli/` — the `spec` command (authoring-only, not modified
  by this spec)

The `spec` CLI and speclib are authoring tools. They stay as they are.
Execution is a separate concern with its own CLI (`af`) and its own
packages.

The example spec pack at `examples/golang_service/service_mvp/` is the
reference target: a campaign with one spec (`01_skafolding`) that defines a
minimal Go service. The MVP must be able to take this spec pack and produce
a working implementation.

## Intent

Create a new `af` CLI tool and supporting library packages that execute an
approved spec pack locally, using a single AI agent to implement each
subtask in order. No hub, no sandbox, no gRPC, no af SDK — the agent reads
the spec directly from the filesystem and writes code into a local git
branch. This is the simplest execution path that still follows the
spec-driven model: frozen plan, ordered task groups, verification checks.

## Goals

1. Create a new `af` CLI tool (`packages/af-cli/`) with a `run` subcommand
   that takes an approved spec within a campaign and executes it against a
   local repository.
2. Create a new `packages/afrunner/` library package containing the
   execution engine — spec reading, prompt composition, agent orchestration,
   verification, and state tracking. This is the reusable core; the CLI is
   a thin wrapper.
3. Create a new `packages/afprompt/` library package for spec-driven prompt
   assembly — composing system prompts from spec slices (subtask details,
   traced requirements, traced test spec entries). This logic is reusable
   beyond the MVP.
4. Create a workspace branch, check out the repo, and run a single agent
   that implements subtasks in task-group order.
5. Track subtask execution state in a local state file alongside the spec
   artifacts (not in a database).
6. After each task group, run the group's verification checks. On failure,
   surface the error and stop (no automatic re-delegation in the MVP).
7. Support the Claude Agent SDK as the initial adapter (Tier 1). The
   generic LangGraph adapter is out of scope for the MVP.
8. Inject the relevant spec slice into the agent's system prompt before
   each subtask — the frozen requirements, test spec entries, and task
   details the subtask traces to.
9. On completion (all task groups done, wiring verification passed), commit
   the work and report ready for review.

## Non-Goals

- No changes to `spec` CLI, speclib, or afspec. They stay as they are.
- No hub process. Everything runs in-process within the `af` CLI.
- No OpenShell sandboxes. The agent runs directly on the local filesystem.
- No af SDK / gRPC. The agent reads spec artifacts directly from disk.
- No Contexts or grounding. The agent has no attached Context sources.
- No agent memory. No recall or consolidate.
- No campaign dependency graphs. Only single-spec execution.
- No multi-agent orchestration. One agent, sequential subtask execution.
- No resume/suspend. If interrupted, re-run from the beginning (or from
  the last committed task group, using git state).
- No web dashboard, notification service, or retrieval engine.
- No Google ADK or generic LangGraph adapter — Claude Agent SDK only.
- No operational store (SQLite). State is a JSON file on disk.

## Package Structure

```
packages/
  afspec/          # existing — spec format models, validation (unchanged)
  speclib/         # existing — authoring pipeline (unchanged)
  spec-cli/        # existing — spec command (unchanged)
  afrunner/        # NEW — execution engine (reusable library)
    afrunner/
      __init__.py
      runner.py    # main execution loop: load spec, iterate groups/subtasks
      state.py     # run state tracking (_run.json read/write)
      verify.py    # verification check runner (shell commands)
      branch.py    # git branch create/checkout/commit
    tests/
  afprompt/        # NEW — prompt assembly from spec slices (reusable library)
    afprompt/
      __init__.py
      compose.py   # system prompt composition from spec + subtask traceability
      slice.py     # extract the spec slice relevant to one subtask
    tests/
  af-cli/          # NEW — af command (thin CLI wrapper)
    af_cli/
      __init__.py
      cli.py       # click-based CLI: af run <campaign> <spec> --repo <path>
    tests/
```

Dependency direction: `af-cli` → `afrunner` → `afprompt` → `afspec`.
The `af-cli` does NOT depend on speclib or spec-cli. Execution and
authoring are independent.

## User Flow

```
# 1. Author the spec (existing tooling, unchanged)
spec init my-campaign
spec new my-campaign --prd prd.md
spec assess my-campaign 01
spec generate my-campaign 01
spec validate my-campaign 01
spec approve my-campaign 01

# 2. Execute the spec (this PRD — new af CLI)
af run my-campaign 01 --repo /path/to/target/repo

# What happens:
#   - af reads the approved spec pack from the campaign directory
#   - af creates branch af/01_skafolding from the repo's default branch
#   - af checks out the branch
#   - For each task group (in order):
#     - For each subtask in the group:
#       - afprompt composes a system prompt with the subtask details,
#         traced requirements, and traced test spec entries
#       - afrunner runs the Claude Agent SDK to implement the subtask
#       - afrunner marks the subtask as done in the state file
#     - afrunner runs the group's verification checks
#     - On failure: report error, stop
#     - On success: commit the work, continue to next group
#   - After all groups: report ready for review
```

## Execution Model

### Spec reading (afrunner)

afrunner reads the four spec artifacts directly from the campaign's spec
directory on disk. No hub, no gRPC. The spec must be in `active` status
(approved). afrunner uses afspec's existing models and validation to load
and validate the spec.

### Branch management (afrunner)

afrunner creates a git branch named `af/<spec_slug>` (e.g.
`af/01_skafolding`) from the repo's default branch. It checks out this
branch in the target repository directory. The user's current checkout is
modified — there is no sandbox isolation in the MVP.

### Prompt assembly (afprompt)

afprompt composes the system prompt for each subtask from the spec
artifacts. For a given subtask, it:

1. Reads the subtask's `requirement_refs` and `test_spec_refs` from
   tasks.json.
2. Extracts the traced requirements from requirements.json (including
   their acceptance criteria and edge cases).
3. Extracts the traced test spec entries from test_spec.json.
4. Composes a system prompt containing:
   - The specialist role (Implementor) and basic coding instructions
   - The full subtask details (title, details array)
   - The traced requirements (rendered)
   - The traced test spec entries (rendered)
   - The test commands (from tasks.json `test_commands`)

This package is deliberately separate from afrunner because prompt
assembly is a reusable concern — the full architecture's coordination
layer will need the same capability.

### Agent execution (afrunner)

afrunner uses the Claude Agent SDK to run a single agent per subtask:

1. Call afprompt to compose the system prompt.
2. Run the Claude Agent SDK with this prompt and standard coding tools
   (file read/write, shell execution, git).
3. Wait for the agent to complete.
4. Mark the subtask as done in the state file.

The agent has full access to the local filesystem (no sandbox). It can
read and write files, run shell commands, and use git. It does NOT have
access to external MCP servers, Contexts, or af SDK tools.

### Verification (afrunner)

After all subtasks in a task group complete, afrunner runs verification.
For task groups with a `verification` block, it runs the checks. In
the MVP, verification executes the test commands defined in
`tasks.json.test_commands`:

- `spec_tests` after each test group
- `all_tests` after the wiring verification group
- `linter` after the wiring verification group

On failure, afrunner reports the failing command's output and stops. The
user can fix manually and re-run.

### State tracking (afrunner)

Subtask execution state is tracked in a `_run.json` file in the spec
directory (alongside `_session.json`). This file records:

- Which subtasks have been completed
- Which task group is currently active
- Timestamps for each transition
- The branch name
- The target repo path

This allows a re-run to skip already-completed task groups (by checking
git state and the run file).

### Commit discipline (afrunner)

afrunner commits after each completed task group (not after each subtask).
The commit message follows the convention:
`feat(<spec_slug>): complete task group <N> — <title>`

## Technical Constraints

- Python 3.14+, consistent with the existing codebase
- Claude Agent SDK (`anthropic` Python package) for agent execution
- No new infrastructure dependencies (no database, no gRPC, no containers)
- afrunner and afprompt are library packages with no CLI concerns
- af-cli is a thin click-based CLI wrapper over afrunner
- The agent's tool set is whatever the Claude Agent SDK provides by default
  (file editing, shell, git) — no custom tools in the MVP
- Each new package follows the monorepo conventions (pyproject.toml managed
  by uv, tests in `tests/` subdirectory)

## Success Criteria

The MVP is successful when:

1. `af run` can take the `examples/golang_service/service_mvp/` spec pack
   and produce a working Go service that passes all verification checks
   defined in the spec.
2. The execution follows the task group order defined in tasks.json.
3. Each subtask's agent receives only the spec slice relevant to that
   subtask (not the entire spec).
4. Verification checks run after each task group and fail loudly on error.
5. The result is committed on a dedicated branch with clean commit history.
6. `spec` CLI, speclib, and afspec are completely unchanged.
