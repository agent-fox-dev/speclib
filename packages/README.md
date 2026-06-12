# af-core

Core packages for the agent-fox agentic development harness.

## Repository Structure

This is a monorepo with three independent packages:

| Package | Path | Description |
|---------|------|-------------|
| `afspec` | `packages/afspec/` | Spec-format library (models, validation, discovery) |
| `speclib` | `packages/speclib/` | Core library (agent pipeline, sessions, campaigns) |
| `spec-cli` | `packages/spec-cli/` | CLI tool providing the `spec` command |

Dependency direction: `spec-cli` → `speclib` → `afspec`.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (required package manager — pip is not supported)

## Installation

### All packages (development)

Install all packages in editable mode from the repo root:

```bash
uv sync
```

### Individual packages

Install just the CLI tool (pulls in `speclib` and `afspec` automatically):

```bash
uv pip install ./packages/spec-cli
```

Install just the library (no CLI dependencies):

```bash
uv pip install ./packages/speclib
```

Install just the spec-format library:

```bash
uv pip install ./packages/afspec
```

## Usage

```bash
spec --help
```

Or use the library programmatically:

```python
from speclib import Campaign, SpecSession
```

## Development

Run the full quality suite (linter + tests) from the repo root:

```bash
make check
```

Run tests only:

```bash
make test
```

Run the linter:

```bash
make lint
```

Run tests for a single package:

```bash
cd packages/speclib && uv run pytest -q
cd packages/spec-cli && uv run pytest -q
cd packages/afspec && uv run pytest -q
```

## Configuration

speclib reads configuration from `~/.af/settings.yaml` and environment
variables. When both are present, environment variables take precedence over
settings file values.

### Settings File

Create `~/.af/settings.yaml` with the following structure:

```yaml
spec_tool:
  model: claude-sonnet-4-6
  auth:
    method: api_key          # api_key | bedrock | vertex
    api_key: sk-ant-...      # for method: api_key
    vertex_project: my-proj  # for method: vertex
    vertex_region: us-east5  # for method: vertex
```

All fields are optional. When not specified, defaults are used:
- `model`: `claude-sonnet-4-6`
- `auth.method`: `api_key`

### Environment Variables

| Variable | Purpose | Overrides |
|----------|---------|-----------|
| `AF_SPEC_MODEL` | Model name | `spec_tool.model` |
| `AF_SPEC_AUTH` | Auth method (`api_key`, `bedrock`, `vertex`) | `spec_tool.auth.method` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `spec_tool.auth.api_key` |
| `AF_SPEC_VERTEX_PROJECT` | GCP project (for Vertex auth) | `spec_tool.auth.vertex_project` |
| `AF_SPEC_VERTEX_REGION` | GCP region (for Vertex auth) | `spec_tool.auth.vertex_region` |

### Authentication Methods

- **api_key** (default): Uses the Anthropic API directly. Requires
  `ANTHROPIC_API_KEY` or `spec_tool.auth.api_key` in settings.yaml.
- **bedrock**: Uses AWS Bedrock. Authenticates via the standard boto3
  credential chain (environment variables, AWS config files, IAM roles).
- **vertex**: Uses Google Vertex AI. Requires `AF_SPEC_VERTEX_PROJECT` (or
  `spec_tool.auth.vertex_project`) and authenticates via the standard
  google-auth credential chain.
