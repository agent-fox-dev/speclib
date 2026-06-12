# PRD: Implement afspec.validate_artifact

## Intent

Implement `validate_artifact(artifact_name, content)` in the local `afspec`
stub package (`packages/afspec/`) so that generated spec artifacts are
validated against JSON schemas before being written to disk.

## Background

Spec 03 (agent_pipeline) requires each generated artifact to be validated
against its JSON schema (03-REQ-3.4, 03-REQ-3.5). The call site in
`speclib/agent.py:generate_artifacts()` calls
`afspec.validate_artifact(artifact_name, content)` after each artifact is
produced by the agent.

The local `afspec` stub package (`packages/afspec/`) currently contains only a
version string — no validation logic. A graceful skip was added as a
workaround, but the validation gap remains: malformed artifacts pass through
unchecked.

The real `speclib-python` project (at `~/devel/workspace/speclib-python/`)
provides full spec validation via `afspec.validate(spec: Spec)`, but its API
operates on fully-loaded `Spec` Pydantic models, not individual artifact dicts.
It also bundles JSON schemas for `requirements.v1.json`, `test_spec.v1.json`,
and `tasks.v1.json`.

This spec implements `validate_artifact` in the local stub by copying the
JSON schemas from `speclib-python` and validating individual artifact dicts
against them using the `jsonschema` library.

## Requirements

1. The `afspec` stub package SHALL export a `validate_artifact(artifact_name,
   content)` function that validates a single artifact dict against the
   corresponding JSON schema.

2. The function SHALL accept three artifact names: `requirements`, `test_spec`,
   and `tasks` — matching the names used in `speclib/agent.py:generate_artifacts()`.

3. The function SHALL raise a `ValidationError` with details when the content
   does not conform to the schema.

4. The function SHALL silently return `None` when the content is valid.

5. The JSON schemas SHALL be bundled inside `packages/afspec/afspec/schemas/`
   and loaded at validation time.

6. After implementation, the graceful skip in `speclib/agent.py:validate_artifact()`
   SHALL be removed and replaced with a direct call to `afspec.validate_artifact()`.

## Design Decisions

1. **Copy schemas from speclib-python.** The three JSON schema files
   (`requirements.v1.json`, `test_spec.v1.json`, `tasks.v1.json`) are copied
   from `speclib-python/afspec/schemas/` into the local stub package. This
   keeps `speclib` self-contained without a dependency on `speclib-python`.

2. **Use `jsonschema` for validation.** The `jsonschema` library is the
   standard Python JSON Schema validator. It is added as a dependency to
   the local `afspec` stub package.

3. **Raise `ValidationError`** — a new exception class in the stub package —
   with the artifact name and a list of schema violation messages. This
   matches the contract expected by the `speclib/agent.py` call site, which
   catches `Exception` and wraps it in `AgentError`.

4. **Map artifact names to schema files.** The mapping is:
   `requirements` → `requirements.v1.json`,
   `test_spec` → `test_spec.v1.json`,
   `tasks` → `tasks.v1.json`.

## Non-Goals

- Validating PRD frontmatter (not produced by `generate_artifacts`).
- Cross-file integrity checks (e.g., requirement ID references across
  artifacts) — that is `validate_cross_file` in `speclib-python`.
- Replacing the stub with the full `speclib-python` dependency.

## Dependencies

| Spec | From Group | To Group | Relationship |
|------|-----------|----------|--------------|
| 03_agent_pipeline | 4 | 3 | `generate_artifacts` call site defined in group 4; group 4 is where `validate_artifact` is first called |

## Source

Source: Input provided by user via interactive prompt.
