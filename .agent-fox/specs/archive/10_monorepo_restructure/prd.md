# PRD: Monorepo Restructure

## Intent

Restructure the speclib repository from a single-package layout into a
monorepo hosting multiple independent Python packages under `packages/`.
The goal is to separate the reusable library code (agents, sessions,
campaigns, config, auth) from the CLI entry point, so that the library
can be consumed programmatically from any Python code — not just through
the `spec` CLI, and establish a pattern for adding future CLI tools as separate
installable packages.

## Goals

1. The spec-authoring library (agent pipeline, session state machine,
   campaign management, configuration, authentication) is importable as
   a standalone Python package without pulling in CLI dependencies
   (Click, Rich).
2. The `spec` CLI is a thin wrapper that depends on the library and can
   be installed independently via `uv pip install ./packages/spec-cli`.
3. Each package under `packages/` is self-contained: own `pyproject.toml`,
   own `tests/` directory, own optional dev dependencies.
4. A root-level Makefile orchestrates cross-package quality commands
   (`make check`, `make test`, `make lint`, `make clean`).
5. Future CLI tools can be added under `packages/` following the same
   pattern.

## Non-Goals

- Changing the public API surface of the library or CLI (this is a
  restructure, not a rewrite).
- Publishing packages to PyPI (installation is from local checkout or
  git URL).
- Introducing a workspace manager like `hatch` workspaces or
  `uv workspaces` beyond what `uv` already supports with path
  dependencies.
- Modifying the `afspec` package — it stays as-is under
  `packages/afspec/`.

## Background

The repository currently has a flat layout:

```
speclib/          # Library + CLI combined
  __init__.py
  agent.py        # SpecAgent (Anthropic API wrapper)
  auth.py         # Client factory
  campaign.py     # Campaign directory management
  cli.py          # Click CLI entry point
  config.py       # YAML/env config loading
  errors.py       # Exception hierarchy
  prompts.py      # Prompt templates
  session.py      # Session state machine
  skill/          # spec.md skill file + install logic
  tools.py        # Tool definitions for structured output
  ui.py           # StatusSpinner (Rich-based)
tests/            # All tests in one directory
packages/afspec/  # Already separated spec-format library
```

The `pyproject.toml` at the root defines both the library and the CLI
entry point (`spec = "speclib.cli:main"`). The library modules
(`agent`, `session`, `campaign`, `config`, `auth`, `prompts`, `tools`,
`errors`) have no dependency on Click or Rich and can be cleanly
separated from the CLI modules (`cli`, `ui`, `skill/`).

## Design Decisions

1. **Library package name stays `speclib`.** The import path
   `from speclib import SpecSession` is already established. Moving to
   `packages/speclib/` changes only the on-disk location, not the import
   name.

2. **CLI package is `spec-cli`** living at `packages/spec-cli/`. Its
   installable name is `spec-cli` and it provides the `spec` console
   script entry point. It depends on `speclib` (path dependency).

3. **Tests move with packages.** Library tests go to
   `packages/speclib/tests/`, CLI tests go to
   `packages/spec-cli/tests/`. Each package's `pyproject.toml` defines
   its own test paths.

4. **Skill files go with the CLI.** The `spec.md` skill prompt and
   the `install-skill` command are CLI concerns and live under
   `packages/spec-cli/`.

5. **Root Makefile orchestrates all packages.** `make check` runs lint
   and tests across all packages. Individual packages can also be tested
   in isolation.

6. **Root `pyproject.toml` becomes a workspace file.** It no longer
   defines an installable package. It serves as the workspace root,
   declaring path dependencies for `uv` to resolve, and defining shared
   tool configuration (ruff, mypy).

7. **CLI module name.** The CLI package's Python module is `spec_cli`
   (since `spec` alone would shadow the stdlib). The entry point is
   `spec = "spec_cli.cli:main"`.

## Target Structure

```
packages/
  afspec/           # Unchanged
  speclib/          # Library (agent, session, campaign, config, auth, etc.)
    speclib/
      __init__.py
      agent.py
      auth.py
      campaign.py
      config.py
      errors.py
      prompts.py
      session.py
      tools.py
    pyproject.toml
    tests/
  spec-cli/         # CLI wrapper
    spec_cli/
      __init__.py
      cli.py
      ui.py
      skill/
        __init__.py
        spec.md
    pyproject.toml
    tests/
pyproject.toml      # Workspace root (not installable)
Makefile            # Orchestrates all packages
```

## Source

Source: Input provided by user via interactive prompt.
