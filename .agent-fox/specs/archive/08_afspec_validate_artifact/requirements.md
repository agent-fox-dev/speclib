# Requirements Document

## Introduction

Implements `validate_artifact()` in the local `afspec` stub package
(`packages/afspec/`) to validate individual spec artifacts against their
JSON schemas, fulfilling the contract expected by
`speclib/agent.py:generate_artifacts()`.

## Glossary

- **Artifact**: One of the three generated spec outputs: `requirements`,
  `test_spec`, or `tasks`. Each is a JSON-serializable dict produced by the
  agent during `generate_artifacts()`.
- **JSON Schema**: A declarative format for describing the structure of JSON
  data, used to validate artifact content.
- **Stub package**: The local `packages/afspec/` package that provides a
  minimal `afspec` API without depending on the full `speclib-python`.

## Requirements

### Requirement 1: Validate Artifact Function

**User Story:** As a developer using `generate_artifacts()`, I want each
artifact to be validated against its JSON schema before it is written to
disk, so that malformed artifacts are caught early.

#### Acceptance Criteria

1. [08-REQ-1.1] THE `afspec` stub package SHALL export a
   `validate_artifact(artifact_name: str, content: dict)` function.

2. [08-REQ-1.2] WHEN `validate_artifact` is called with a valid
   `artifact_name` and `content` that conforms to the corresponding JSON
   schema, THE function SHALL return `None` without raising an exception.

3. [08-REQ-1.3] WHEN `validate_artifact` is called with `content` that does
   NOT conform to the corresponding JSON schema, THE function SHALL raise a
   `ValidationError` whose message includes the artifact name and a
   description of the schema violations.

4. [08-REQ-1.4] THE function SHALL accept exactly three artifact names:
   `requirements`, `test_spec`, and `tasks`, mapped to their corresponding
   JSON schema files.

#### Edge Cases

1. [08-REQ-1.E1] IF `validate_artifact` is called with an unrecognized
   `artifact_name`, THEN THE function SHALL raise a `ValueError` identifying
   the invalid name and listing the valid artifact names.

2. [08-REQ-1.E2] IF `content` is an empty dict `{}`, THEN THE function SHALL
   validate it against the schema and raise `ValidationError` if required
   fields are missing.

### Requirement 2: Bundled JSON Schemas

**User Story:** As a maintainer, I want the JSON schemas bundled inside the
stub package, so that validation works without network access or external
dependencies beyond `jsonschema`.

#### Acceptance Criteria

1. [08-REQ-2.1] THE stub package SHALL bundle three JSON schema files:
   `requirements.v1.json`, `test_spec.v1.json`, and `tasks.v1.json` in a
   `schemas/` subdirectory.

2. [08-REQ-2.2] THE schemas SHALL be loadable via `importlib.resources` at
   validation time AND return valid JSON when parsed.

### Requirement 3: Remove Graceful Skip in Agent

**User Story:** As a developer, I want `speclib/agent.py:validate_artifact()`
to call `afspec.validate_artifact()` directly (no skip), so that validation
is actually enforced.

#### Acceptance Criteria

1. [08-REQ-3.1] WHEN `afspec.validate_artifact` is available, THE
   `speclib/agent.py:validate_artifact()` wrapper SHALL call it directly
   without a `getattr` fallback.

### Requirement 4: ValidationError Exception

**User Story:** As a caller of `validate_artifact`, I want a clear exception
type so I can catch validation failures distinctly from other errors.

#### Acceptance Criteria

1. [08-REQ-4.1] THE `afspec` stub package SHALL define a `ValidationError`
   exception class that extends `Exception`.

2. [08-REQ-4.2] THE `ValidationError` SHALL expose the `artifact_name` and
   a list of `errors` (strings) as attributes AND include both in its string
   representation.
