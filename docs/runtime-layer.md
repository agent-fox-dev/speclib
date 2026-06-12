# Runtime Layer Specification

**Version:** 1.0
**Status:** Draft

This document specifies the runtime layer that sits underneath the af
coordination layer. It covers container isolation, git worktree management,
harness adapters, agent lifecycle, templates, sidecar services, and the af
MCP bridge. The design follows patterns established by Google's Scion project,
adapted to our requirements.

The coordination layer (domain model, spec package, agents, orchestration)
is specified in [coordination-layer.md](coordination-layer.md). The services
architecture (hub, CLI, storage, deployment) is specified in
[services-architecture.md](services-architecture.md).

---

## 1. Design principles

1. **Thin and focused.** The runtime handles infrastructure; it has no opinion
   on specs, Contexts, coordination, or verification. It starts containers,
   manages worktrees, and exposes agent lifecycle operations.

2. **Provider-agnostic.** Claude Code, Gemini CLI, Codex, and OpenCode are
   interchangeable through one harness adapter interface. Adding a new
   provider means implementing one adapter.

3. **Sandbox-first isolation.** Each agent runs in its own sandbox managed
   by [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell). The worktree
   is mounted in; everything else (spec store, harness configuration, sibling
   agents) is invisible. OpenShell enforces isolation out-of-process through
   defense-in-depth: kernel-level filesystem restrictions, network egress
   filtering, and syscall sandboxing — the agent cannot override its own
   guardrails.

4. **The coordination layer drives.** The runtime exposes a narrow API. The
   coordination layer calls it to start/stop agents, provision worktrees, and
   inject configuration. The runtime never calls back into the coordination
   layer — the af MCP bridge handles that direction (§8).

5. **Portable across sandbox backends.** OpenShell abstracts the underlying
   container backend: Docker, Podman, MicroVM, and Kubernetes are supported
   through a single sandbox interface. The af runtime delegates container
   concerns to OpenShell rather than implementing backend adapters directly.

---

## 2. Container runtime interface

The runtime abstracts the container backend behind one interface. Every
operation the coordination layer needs goes through it. The primary
implementation is an adapter over
[NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell)'s sandbox API (§2.1).

```
interface ContainerRuntime:
    create(spec: ContainerSpec) → ContainerId
    start(id: ContainerId) → void
    stop(id: ContainerId, timeout: Duration) → void
    remove(id: ContainerId) → void
    exec(id: ContainerId, command: list[string]) → ExecResult
    logs(id: ContainerId, follow: boolean) → stream[string]
    inspect(id: ContainerId) → ContainerState

record ContainerSpec:
    image:      string
    name:       string
    mounts:     list[Mount]              -- worktree, agent home, sidecar sockets
    env:        map[string, string]
    command:    list[string]
    services:   list[ServiceSpec]        -- sidecar processes
    resources:  ResourceLimits, optional -- CPU, memory caps

record Mount:
    source:    string   -- host path
    target:    string   -- container path
    readonly:  boolean

record ContainerState:
    id:        ContainerId
    status:    "created" | "running" | "stopped" | "error"
    exitCode:  number or null
    startedAt: string or null
    stoppedAt: string or null
```

### 2.1 OpenShell adapter (default)

The default implementation. Uses
[NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) (Apache 2.0, Rust)
to create, manage, and enforce isolation on agent sandboxes. OpenShell
itself supports Docker, Podman (rootless), MicroVM, and Kubernetes as
underlying container backends, so the af runtime does not implement
backend-specific adapters.

**Sandbox lifecycle.** Each `ContainerRuntime` operation maps to an
OpenShell sandbox operation:

| `ContainerRuntime` method | OpenShell equivalent |
| --- | --- |
| `create(spec)` | `openshell sandbox create --from <image>` with mounts, env, and policy |
| `start(id)` | Sandbox starts on creation; no separate start step |
| `stop(id, timeout)` | `openshell sandbox stop` with configurable grace period |
| `remove(id)` | `openshell sandbox rm` |
| `exec(id, command)` | `openshell sandbox exec` |
| `logs(id, follow)` | `openshell logs --tail` |
| `inspect(id)` | Sandbox status query via API |

**Mounts.** The agent's worktree is mounted at `/workspace`. The agent's
home directory is mounted at a configurable path (default `/home/agent`).
OpenShell's filesystem policy locks allowed paths at sandbox creation via
Landlock LSM — kernel-enforced, not bypassable from inside the sandbox.
Shadow mounts for `.af` configuration and sibling worktrees are unnecessary:
the Landlock policy denies access to paths not explicitly allowed, which is
a stronger guarantee than tmpfs overlays.

**Credential injection.** OpenShell manages credentials as *providers*:
named credential bundles injected into sandboxes at creation. The CLI
auto-discovers credentials for recognized agents (Claude Code, Codex,
OpenCode, Copilot) from the host's shell environment, or the Operator can
create providers explicitly via `openshell provider create`. Credentials
are injected as environment variables at runtime and never appear on the
sandbox filesystem.

**Defense-in-depth isolation.** OpenShell enforces constraints
out-of-process — the agent cannot override its own guardrails:

| Layer | Mechanism | Enforcement |
| --- | --- | --- |
| Filesystem | Landlock LSM | Kernel-enforced path allowlists, locked at sandbox creation |
| Network | HTTP CONNECT proxy with OPA/Rego policies | Deny-by-default; every outbound connection evaluated at the HTTP method and path level |
| Process | Seccomp BPF filters | Blocks privilege escalation, dangerous syscalls, and socket creation outside the proxy |
| Inference | Privacy router | Routes LLM API calls based on policy; strips caller credentials, injects backend credentials |

Static protections (filesystem, process) are immutable after creation.
Dynamic protections (network, inference) can be hot-reloaded on running
sandboxes via `openshell policy set`.

**Policy model.** Sandbox behavior is governed by declarative YAML policies.
The af runtime ships a default policy that allows: read-write access to
`/workspace` and the agent home, read-only access to template files,
localhost egress to the hub's bridge port, and inference egress to the
configured model provider. The Operator can customize policies per workspace
or per agent role via the configuration hierarchy (§11).

**Inference routing.** The privacy router intercepts LLM API calls from the
harness and routes them based on policy — not the agent's preference. This
enables deployments where sensitive context stays on-device using local
open-weight models while frontier models (Claude, GPT) are used only when
policy allows. The router is model-agnostic by design.

**Built-in agent support.** OpenShell ships with pre-configured support for
Claude Code, Codex, OpenCode, and GitHub Copilot. Agents run unmodified
inside sandboxes with zero code changes. The default sandbox image includes
Python 3.14, Node 22, git, and standard developer tools.

### 2.2 Kubernetes deployment

OpenShell provides an experimental Helm chart for Kubernetes deployment.
The same `ContainerRuntime` adapter works because OpenShell abstracts the
container backend — the adapter calls `openshell sandbox create` regardless
of whether the sandbox runs as a Docker container, a Podman pod, or a
Kubernetes pod. Kubernetes-specific concerns (init containers, CSI volumes,
pod scheduling) are handled by OpenShell, not by the af runtime.

### 2.3 Direct container fallback

For environments where OpenShell is not available (minimal setups, custom
container runtimes), the `ContainerRuntime` interface supports a direct
Podman or Docker adapter. This fallback uses the container engine's socket
API directly, with bind mounts for the worktree and agent home. It provides
process-level isolation but lacks OpenShell's defense-in-depth (no Landlock,
no network proxy, no inference routing). The interface contract is
identical; only the isolation guarantees are weaker.

---

## 3. Git worktree management

The runtime manages per-workspace git worktrees. This is the mechanism behind
workspace isolation (see [coordination-layer.md §3.2](coordination-layer.md#32-isolation-through-worktrees)).

```
interface WorktreeManager:
    create(input: {
        repoPath:   string    -- path to the main repo
        branch:     string    -- e.g. "af/add-dark-mode"
        baseBranch: string    -- e.g. "main"
    }) → WorktreeInfo

    remove(worktreePath: string, deleteBranch: boolean) → void

    list(repoPath: string) → list[WorktreeInfo]

record WorktreeInfo:
    path:       string   -- absolute path to the worktree directory
    branch:     string
    baseBranch: string
    head:       string   -- current commit SHA
```

### 3.1 Branch naming

Branches follow the convention `af/<workspace-name>`, e.g.
`af/add-dark-mode`. The prefix is configurable per installation. Collisions
are rejected at creation.

### 3.2 Worktree location

Worktrees are created outside the main repo's working directory to avoid
polluting it: `<repo-parent>/.af_worktrees/<workspace-id>/`. Each
worktree is a full working directory checked out to its branch.

### 3.3 Lifecycle

- **Create:** `git worktree add` from the base branch. The worktree is
  empty of untracked files (no env files, secrets, or installed
  dependencies carry over from the main checkout).
- **Remove:** `git worktree remove` plus optional `git branch -d`. The
  coordination layer decides when to remove (see
  [coordination-layer.md §3.7](coordination-layer.md#37-workspace-ownership-and-management));
  the runtime executes it.

---

## 4. Harness adapters

A harness adapter integrates one provider into the runtime. It handles
everything provider-specific so the coordination layer sees a uniform
interface.

```
interface HarnessAdapter:
    name() → string

    -- Build the container command to launch the harness.
    -- `resume` indicates whether to continue a prior session.
    getCommand(input: {
        task:     string
        resume:   boolean
        baseArgs: list[string]
    }) → list[string]

    -- Return harness-specific environment variables.
    getEnv(input: {
        agentName: string
        agentHome: string
    }) → map[string, string]

    -- Perform harness-specific setup in the agent's home directory
    -- after templates are copied. Called once at agent creation.
    provision(input: {
        agentName:     string
        agentHome:     string   -- host path to agent home dir
        workspacePath: string   -- host path to worktree
    }) → void

    -- Inject system prompt content into the harness's expected location.
    injectSystemPrompt(agentHome: string, content: string) → void

    -- Inject agent instructions (rules, conventions) into the harness's
    -- expected location.
    injectInstructions(agentHome: string, content: string) → void

    -- Translate universal MCP server configs into the harness's native
    -- MCP configuration format.
    applyMCPServers(
        agentHome: string,
        servers: map[string, MCPServerConfig]
    ) → void

    -- Resolve authentication: select the best auth method and return
    -- the env vars and file mounts needed to inject credentials.
    resolveAuth(auth: AuthConfig) → ResolvedAuth

    -- Whether this harness supports session suspend/resume.
    supportsResume() → boolean

    -- The key sequence to interrupt the harness process (e.g. "Ctrl-C").
    interruptKey() → string
```

### 4.1 Claude Code adapter

- **Command:** `claude --dangerously-skip-permissions` (or with a
  permissions file). `--continue` on resume.
- **System prompt:** Written to `CLAUDE.md` in the agent home or workspace
  root.
- **MCP servers:** Written to `.claude.json` or `.claude/settings.json`.
- **Auth:** API key via `ANTHROPIC_API_KEY` env var, or Vertex AI / AWS
  Bedrock credentials.
- **Resume:** Supported. `--continue` flag resumes the last session.

### 4.2 Gemini CLI adapter

- **Command:** `gemini` with task as argument. `--resume` on resume.
- **System prompt:** Written to `.gemini/system_prompt.md`.
- **MCP servers:** Written to `.gemini/settings.json`.
- **Auth:** Google Cloud credentials via `GOOGLE_APPLICATION_CREDENTIALS` or
  `GEMINI_API_KEY`.
- **Resume:** Supported. `--resume` flag continues the session.

### 4.3 Codex adapter

- **Command:** `codex` with task as argument.
- **System prompt:** Written to `AGENTS.md` or provider-specific location.
- **MCP servers:** Provider-specific configuration.
- **Auth:** `OPENAI_API_KEY` env var.
- **Resume:** Not supported; starts fresh.

### 4.4 OpenCode adapter

- **Command:** `opencode` with task as argument.
- **System prompt:** Written to provider-specific location.
- **MCP servers:** Written to `opencode.json`.
- **Auth:** Provider-specific API key env var.
- **Resume:** Not supported; starts fresh.

### 4.5 Credential injection under OpenShell

When running under OpenShell (§2.1), credential injection is handled by
OpenShell's provider mechanism rather than by each harness adapter
individually. OpenShell auto-discovers credentials for recognized agents
from the host's shell environment (e.g. `ANTHROPIC_API_KEY` for Claude
Code, `OPENAI_API_KEY` for Codex) and injects them into the sandbox as
environment variables. The adapter's `resolveAuth()` delegates to this
mechanism: it declares which credential type the harness needs, and
OpenShell resolves and injects it. The adapter does not handle raw API
keys or credential files directly.

For agents or auth methods OpenShell does not recognize (Vertex AI, AWS
Bedrock, custom providers), `resolveAuth()` falls back to explicit
credential injection via `openshell provider create --type custom`.

### 4.6 Adding a new adapter

Implement the `HarnessAdapter` interface. Register it in the adapter
registry. No changes to the coordination layer or the container runtime.

---

## 5. Agent lifecycle

The runtime manages agent lifecycle through a state model and a set of
operations the coordination layer calls.

### 5.1 Agent state

Two dimensions, following the Scion pattern:

**Phase** — the container lifecycle:

| Phase | Meaning | Transitions |
| --- | --- | --- |
| `created` | Container spec built, not yet started. | → `provisioning` |
| `provisioning` | Harness adapter running `provision()`, template hydration. | → `starting`, → `error` |
| `starting` | Container starting, harness initializing. | → `running`, → `error` |
| `running` | Harness active, agent working. | → `stopping`, → `suspended`, → `error` |
| `stopping` | Graceful shutdown in progress (SIGTERM sent). | → `stopped` |
| `stopped` | Container exited cleanly. Session ended. | → `provisioning` (fresh start) |
| `suspended` | Container torn down with intent to resume. | → `starting` (resume) |
| `error` | Container exited with non-zero code or setup failed. | → `provisioning` (retry) |

**Activity** — what the agent is doing within the `running` phase:

| Activity | Meaning |
| --- | --- |
| `working` | Agent actively editing, running tools. |
| `thinking` | Agent reasoning (model inference in progress). |
| `waiting_for_input` | Agent waiting for human or Coordinator input. |
| `completed` | Agent finished its task (sticky until restart/stop). |
| `idle` | Agent running but not currently active. |

The coordination layer maps these to its own concepts: a `running` agent
with activity `completed` triggers the Coordinator to check subtask state.
A `stopped` or `error` phase triggers error handling in the run.

### 5.2 Lifecycle operations

```
interface AgentLifecycle:
    -- Create an agent: build container spec, provision harness, copy
    -- template, inject system prompt and MCP config. Does not start.
    create(input: {
        name:         string
        workspace:    WorkspaceRef
        template:     TemplateRef
        systemPrompt: string
        instructions: string
        mcpServers:   map[string, MCPServerConfig]
        env:          map[string, string]
        services:     list[ServiceSpec]
    }) → AgentRef

    -- Start a created or stopped agent. Fresh session.
    start(ref: AgentRef, task: string) → void

    -- Resume a suspended agent. Continues the prior session.
    -- Falls back to fresh start if the harness doesn't support resume.
    resume(ref: AgentRef, task: string, optional) → void

    -- Graceful stop. Sends SIGTERM, waits for timeout, then SIGKILL.
    stop(ref: AgentRef, timeout: Duration, optional) → void

    -- Suspend: stop with intent to resume.
    -- Only for harnesses that support session resume.
    suspend(ref: AgentRef) → void

    -- Remove agent: stop if running, delete container, optionally
    -- delete home directory and worktree branch.
    delete(ref: AgentRef, cleanup: { branch: boolean; home: boolean }, optional) → void

    -- Send a message to a running agent's input stream.
    message(ref: AgentRef, text: string) → void

    -- Query current state.
    state(ref: AgentRef) → { phase: Phase, activity: Activity, detail: string, optional }

    -- Stream agent output.
    logs(ref: AgentRef, follow: boolean) → stream[string]
```

### 5.3 Session management

Agents run inside a terminal multiplexer (tmux) within the container. This
gives:

- **Detached execution.** The agent runs in the background; the user or
  coordination layer attaches/detaches without interrupting work.
- **Session persistence.** On suspend, the tmux session's state (including
  the harness's conversation history, if the harness supports it) enables
  resume.
- **Input injection.** The `message` operation sends text into the tmux pane,
  which the harness reads as user input.

---

## 6. Templates

A template is a blueprint for agent configuration. The coordination layer's
specialists (see [coordination-layer.md §6.4](coordination-layer.md#64-specialists-actor-capabilities-and-instruction-precedence))
map to templates: the specialist defines the role semantically (actor
capability, tool policy); the template defines the configuration
mechanically (system prompt file, env vars, MCP servers).

### 6.1 Template structure

```
templates/
  <template-name>/
    template.yaml           # metadata and configuration
    home/                   # files copied to the agent's home directory
      CLAUDE.md             # (or .gemini/system_prompt.md, etc.)
      ...
```

### 6.2 Template configuration

```yaml
name: implementor
harness: claude
description: "Implements a subtask against a frozen spec."

env:
  AF_ROLE: implementor

mcp_servers:
  af:
    transport: stdio
    command: /usr/local/bin/af-mcp-bridge
    args: ["--workspace", "${AF_WORKSPACE_ID}"]

services:
  - name: af-bridge
    command: ["/usr/local/bin/af-mcp-bridge", "--workspace", "${AF_WORKSPACE_ID}"]
    restart: always
    ready_check:
      type: tcp
      target: "localhost:7400"
      timeout: "10s"
```

### 6.3 Template resolution

Templates are resolved in order: project-level (`.af/templates/`)
overrides global (`<data_dir>/templates/`), which overrides built-in defaults.
The coordination layer can also pass inline configuration at agent creation
time, which overrides the template.

### 6.4 Built-in templates

The runtime ships default templates for each specialist role:

| Template | Harness | Role |
| --- | --- | --- |
| `planner` | configurable | Drafts spec artifacts during `draft`. |
| `coordinator` | configurable | Delegates subtasks, monitors execution. |
| `implementor` | configurable | Implements one subtask. |
| `verifier` | configurable | Runs verification checks. |

Each template includes the af MCP bridge as a sidecar service and
pre-configures the MCP server declaration so the harness discovers it.
The harness itself (Claude Code, Gemini CLI, etc.) is configurable per
template.

---

## 7. Sidecar services

A sidecar service is a long-running process that runs alongside the harness
inside the agent's container. The runtime manages sidecar lifecycle: start
before the harness, health-check, restart on failure, stop on agent stop.

```
record ServiceSpec:
    name:       string
    command:    list[string]
    restart:    "always" | "on-failure" | "never"
    env:        map[string, string], optional
    readyCheck: optional
        type:    "tcp" | "http" | "delay"
        target:  string   -- "localhost:7400", "http://localhost:8080/health", "3s"
        timeout: string   -- max wait before giving up
```

The harness does not start until all sidecar services with readiness checks
have reported ready. This ensures the af MCP bridge is available before
the agent begins working.

### 7.1 Sidecars under OpenShell

OpenShell sandboxes are full environments, not single-process containers.
Each sandbox includes a shell, language runtimes, and standard developer
tools. Sidecar services (including the af MCP bridge) run as background
processes inside the sandbox, managed by the runtime's service supervisor.

The sandbox policy must allow the network access sidecars require. For the
af MCP bridge, this means localhost egress to the hub's bridge port
(`AF_HUB_HOST:AF_HUB_PORT`). The default af sandbox policy includes this
rule. Additional sidecars that reach external services need corresponding
network policy entries — either in the default policy or in a per-workspace
override.

---

## 8. The af MCP bridge

The af MCP bridge is the key integration point between the runtime layer
and the coordination layer. It runs as a sidecar service inside each agent
container and exposes harness-specific capabilities as MCP tools that the
harness (Claude Code, Gemini CLI, etc.) can call.

### 8.1 Why an MCP bridge

The runtime treats the harness as opaque — it does not intercept tool calls
or sit in the model's reasoning loop. But the coordination layer needs to
extend the agent's tool set with capabilities the harness doesn't natively
have (spec read, Context search, memory recall, subtask state transitions).
The MCP bridge resolves this: it's an MCP server the harness
connects to, indistinguishable from any other MCP tool. The coordination
layer's tools appear to the agent as standard MCP tools.

### 8.2 Tools exposed

| Tool | Description | Direction |
| --- | --- | --- |
| `af_spec_read` | Fetch spec artifacts, rendered views, traceability, coverage. | Agent → af service |
| `af_context_search` | Search retrieved sources in attached Contexts. Params: `query`, optional `context_id`, `source_id`, `max_results`. Returns ranked chunks. | Agent → af service |
| `af_context_get` | Fetch a pinned source from an attached Context in full. Params: `context_id`, `source_id`. | Agent → af service |
| `af_memory_recall` | Search agent memory for relevant learnings. | Agent → af service |
| `af_subtask_state` | Transition the agent's own subtask state. | Agent → af service |
| `af_ci_status` | Query CI pipeline runs, job results, and logs. | Agent → af service |
| `af_issues` | Read, search, create, comment on, update issues through the tracker-agnostic interface. | Agent → af service |
| `af_web_search` | Search and fetch public web content through the provider-agnostic interface. | Agent → af service |

### 8.3 Architecture

```
┌─── Agent Container ─────────────────────────────────────┐
│                                                         │
│  ┌─────────────┐         ┌──────────────────────┐       │
│  │   Harness    │◄──MCP──►│  af MCP Bridge    │       │
│  │ (Claude Code │         │  (sidecar service)   │       │
│  │  Gemini CLI) │         └──────────┬───────────┘       │
│  └──────┬──────┘                     │                   │
│         │                            │ gRPC / HTTP       │
│    /workspace                        │                   │
│    (mounted worktree)                │                   │
└─────────────────────────────────────┼───────────────────┘
                                       │
                          ┌────────────▼────────────┐
                          │   af Coordination    │
                          │       Service           │
                          │                         │
                          │  Spec store             │
                          │  Context store          │
                          │  Operational store      │
                          │  Prompt assembly        │
                          │  Run management         │
                          └─────────────────────────┘
```

The bridge communicates with the af coordination service on the host via
gRPC or HTTP. The coordination service is the source of truth for spec
content, Context data, memory, and subtask state. The bridge
is stateless — it proxies requests and returns responses.

### 8.4 Authentication and scoping

Every bridge instance knows its agent's identity (workspace ID, agent ID,
run ID, specialist role) via environment variables injected at container
creation. The coordination service uses this identity to scope tool calls:
an Implementor's `af_subtask_state` call can only transition its own
assigned subtask; a `af_spec_read` call returns only the artifacts for
the agent's workspace.

### 8.5 Activity logging

The bridge logs every tool call and response as activity events, forwarded
to the coordination service. This is how harness-level tool calls (spec reads,
Context searches, subtask transitions) enter the activity log even though
the runtime does not intercept the harness's native tool loop.

---

## 9. Agent provisioning flow

The full sequence from workspace creation to a running agent:

1. **Coordination layer** calls `WorktreeManager.create()` to provision the
   branch and worktree.

2. **Coordination layer** assembles the agent configuration: resolves the
   specialist to a template, composes the system prompt (see
   [coordination-layer.md §6.3](coordination-layer.md#63-prompt-assembly)),
   gathers MCP server configs (including the af bridge), and collects
   environment variables.

3. **Coordination layer** calls `AgentLifecycle.create()` with the assembled
   configuration.

4. **Runtime** resolves the template: copies home directory content, runs the
   harness adapter's `provision()` method, calls `injectSystemPrompt()` and
   `injectInstructions()`, calls `applyMCPServers()` to translate MCP
   configs into the harness's native format.

5. **Runtime** builds the `ContainerSpec`: image, mounts (worktree at
   `/workspace`, agent home, shadow mounts for isolation), env vars, sidecar
   services (including the af MCP bridge), and the harness command.

6. **Runtime** calls `ContainerRuntime.create()` and
   `ContainerRuntime.start()`.

7. **Runtime** starts sidecar services and waits for readiness checks.

8. **Runtime** starts the harness process inside the container with the task
   as input.

9. **Agent** begins working. The harness discovers the af MCP bridge as
   an available MCP server and can call its tools.

---

## 10. Sandbox image

OpenShell's default sandbox image includes a shell, standard Unix tools,
Python 3.14, Node 22, git, and common developer tools (`gh`, `vim`, `nano`).
The af runtime extends this with:

- A terminal multiplexer (tmux).
- The af MCP bridge binary.
- Additional language runtimes and build tools as needed.

OpenShell supports three image sources:

- **Community catalog:** `--from <name>` pulls a pre-built image from the
  OpenShell community registry. The af runtime can publish its base image
  here for zero-setup onboarding.
- **Custom Dockerfile:** `--from ./path` builds from a local Dockerfile.
  This is the standard path for af images that need project-specific tools
  or dependencies.
- **Container registry:** `--from registry.io/img:tag` pulls an existing
  OCI image. For organizations with private registries.

The harness (Claude Code, Gemini CLI, etc.) is either pre-installed in the
image or installed during provisioning.

The image does not include the af coordination service, the spec store,
or any coordination logic. These run on the host and the bridge reaches them
over the network.

---

## 11. Configuration

### 11.1 Global configuration

```yaml
# ~/.af/settings.yaml
data_dir: ~/.local/share/af   # default; override with AF_DATA_DIR env var

runtime:
  backend: openshell           # openshell (default) | podman | kubernetes
  image: af/agent:latest       # default base image (or --from source for OpenShell)
  openshell:
    policy: ~/.af/sandbox-policy.yaml   # default sandbox policy
    inference:                          # inference privacy routing
      local_model: null                 # e.g. "ollama:llama3" for local routing
      allow_remote: true                # allow frontier model API calls

defaults:
  harness: claude
  template: implementor

worktrees:
  prefix: af                # branch prefix: af/<workspace-name>
  location: ../.af_worktrees  # relative to repo root

spec_tool:
  model: claude-sonnet-4-6  # model for PRD assessment and artifact generation
```

### 11.2 Per-workspace overrides

```yaml
# Set via the coordination layer's workspace config
# (see coordination-layer.md §3.6)
harness: gemini
template: implementor
image: af/agent:gemini
env:
  CUSTOM_VAR: value
```

Global settings are the defaults. Per-workspace overrides take precedence.
Inline overrides at agent creation time take highest precedence.
