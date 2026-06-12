# Requirements Document

## Introduction

This specification defines the agent pipeline for speclib: the AI-driven
operations that assess PRDs, refine them through interactive Q&A, and generate
the three derived spec artifacts. It also covers the prompt templates, tool
definitions for structured output, error handling with retries, and the wiring
of agent operations into the SpecSession lifecycle.

## Glossary

| Term | Definition |
|------|-----------|
| SpecAgent | The core class wrapping the Anthropic client, providing async methods for assessment, refinement, and generation |
| Assessment | A structured evaluation of a PRD containing quality verdict, summary, gaps, and questions |
| Question | A structured question the agent asks the user to improve the PRD, with id, text, context, options, and required flag |
| GenerateResult | The result of artifact generation containing artifact paths, validation results, and warnings |
| tool_use | Anthropic API feature where the model calls a defined tool with structured JSON input, used for structured output |
| artifact | One of the three generated spec files: requirements.json, test_spec.json, or tasks.json |
| prompt template | A parameterized string used to construct the system/user messages sent to the Anthropic API |
| exponential backoff | Retry strategy where wait time doubles between attempts (e.g., 1s, 2s, 4s) |
| afspec | The speclib-python library providing spec format models, validation, rendering, and I/O |

## Requirements

### Requirement 1: PRD Assessment

**User Story:** As a user, I want the agent to evaluate my PRD and tell me what needs improvement, so that I can produce a high-quality spec.

#### Acceptance Criteria
1. [03-REQ-1.1] WHEN `SpecAgent.assess_prd(prd_text, spec_name)` is called with valid PRD text, THE agent SHALL send the PRD to the Anthropic messages API with the assessment prompt and assessment tool definition, and SHALL return an `Assessment` object.
2. [03-REQ-1.2] THE returned `Assessment` SHALL contain a `quality` field with one of the values `"ready"`, `"needs_refinement"`, or `"incomplete"`.
3. [03-REQ-1.3] THE returned `Assessment` SHALL contain a `summary` field (non-empty string) describing the overall PRD quality.
4. [03-REQ-1.4] THE returned `Assessment` SHALL contain a `gaps` field (list of strings) identifying missing or weak areas in the PRD.
5. [03-REQ-1.5] WHEN the quality is `"needs_refinement"` or `"incomplete"`, THE `Assessment` SHALL contain a non-empty `questions` list where each entry is a `Question` with `id`, `text`, `context`, `options` (list, may be empty), and `required` (bool) fields.
6. [03-REQ-1.6] WHEN the quality is `"ready"`, THE `Assessment` SHALL accept an empty `questions` list as valid.

#### Edge Cases
1. [03-REQ-1.E1] IF the PRD text is empty or contains only whitespace, THEN `assess_prd` SHALL raise an `AgentError` without making an API call.
2. [03-REQ-1.E2] IF the agent returns a tool_use response that does not match the Assessment schema, THEN `assess_prd` SHALL raise an `AgentError` with detail about which fields are invalid.
3. [03-REQ-1.E3] IF the agent does not invoke the assessment tool (returns only text), THEN `assess_prd` SHALL raise an `AgentError` indicating the model did not produce structured output.

### Requirement 2: PRD Refinement

**User Story:** As a user, I want to answer the agent's questions and get an updated PRD with a new assessment, so that I can iteratively improve my spec.

#### Acceptance Criteria
1. [03-REQ-2.1] WHEN `SpecAgent.refine_prd(prd_text, answers, previous_assessment)` is called, THE agent SHALL send the original PRD, the previous assessment, and the user's answers to the Anthropic messages API with the refinement prompt and both the PRD update tool and assessment tool definitions.
2. [03-REQ-2.2] THE method SHALL return a tuple `(updated_prd_text, new_assessment)` where `updated_prd_text` is the revised PRD incorporating the user's answers and `new_assessment` is a fresh Assessment of the updated PRD.
3. [03-REQ-2.3] THE `answers` parameter SHALL be a `dict[str, str]` mapping Question IDs to answer text.
4. [03-REQ-2.4] THE agent SHALL preserve the original PRD's frontmatter (YAML header) and only modify body content.
5. [03-REQ-2.5] WHEN the agent produces an updated PRD with quality `"ready"`, THE `refine_prd` method SHALL return the result without enforcing loop termination, leaving the decision to the caller.

#### Edge Cases
1. [03-REQ-2.E1] IF `answers` is empty, THEN `refine_prd` SHALL raise an `AgentError` indicating no answers were provided.
2. [03-REQ-2.E2] IF `answers` contains Question IDs that do not match any question in the `previous_assessment`, THEN `refine_prd` SHALL raise an `AgentError` listing the unrecognized IDs.
3. [03-REQ-2.E3] IF the agent returns an updated PRD but fails to produce a new assessment, THEN `refine_prd` SHALL raise an `AgentError`.

### Requirement 3: Artifact Generation

**User Story:** As a user, I want the agent to generate requirements, test spec, and tasks from my accepted PRD, so that I get a complete spec package.

#### Acceptance Criteria
1. [03-REQ-3.1] WHEN `SpecAgent.generate_artifacts(prd_text, spec_id, spec_name)` is called, THE agent SHALL generate three artifacts in sequence: `requirements.json`, then `test_spec.json`, then `tasks.json`.
2. [03-REQ-3.2] EACH artifact SHALL be generated by a separate Anthropic messages API call with the generation prompt, the PRD text, any previously generated artifacts as context, and the appropriate artifact tool definition.
3. [03-REQ-3.3] THE method SHALL return a `dict[str, Any]` mapping artifact names (`"requirements"`, `"test_spec"`, `"tasks"`) to their parsed JSON content.
4. [03-REQ-3.4] EACH generated artifact SHALL be validated against its JSON schema (via afspec validation) before the next artifact is generated.
5. [03-REQ-3.5] IF an artifact fails schema validation, THEN `generate_artifacts` SHALL raise an `AgentError` identifying the artifact name and the validation errors.
6. [03-REQ-3.6] THE generation prompt for `test_spec.json` SHALL include the generated `requirements.json` content so the agent can reference requirement IDs.
7. [03-REQ-3.7] THE generation prompt for `tasks.json` SHALL include both the generated `requirements.json` and `test_spec.json` content so the agent can reference requirement and test IDs.
8. [03-REQ-3.8] THE generation prompt for `requirements.json` SHALL instruct the agent to populate the `glossary` field with definitions for all domain-specific terms used in backtick-delimited references within acceptance criteria, edge cases, and correctness properties.

#### Edge Cases
1. [03-REQ-3.E1] IF `prd_text` is empty or contains only whitespace, THEN `generate_artifacts` SHALL raise an `AgentError` without making any API calls.
2. [03-REQ-3.E2] IF the agent does not invoke the artifact tool for a given artifact, THEN `generate_artifacts` SHALL raise an `AgentError`.
3. [03-REQ-3.E3] IF the agent returns JSON that parses successfully but fails afspec schema validation, THEN THE error message SHALL include both the artifact name and the specific validation failures.

### Requirement 4: Prompt Templates

**User Story:** As a developer, I want prompt templates to be centralized and parameterizable, so that they can be maintained and tuned independently of the agent logic.

#### Acceptance Criteria
1. [03-REQ-4.1] THE `speclib/prompts.py` module SHALL define a function or template for the assessment system prompt that instructs the model to evaluate PRD quality against spec-format expectations, explicitly checking for presence and quality of the Intent section (required), Goals section, Non-Goals section, and Background section.
2. [03-REQ-4.2] THE `speclib/prompts.py` module SHALL define a function or template for the refinement system prompt that instructs the model to incorporate answers, update the PRD, and re-assess.
3. [03-REQ-4.3] THE `speclib/prompts.py` module SHALL define a function or template for the generation system prompt that instructs the model to produce a single artifact at a time in the correct JSON schema.
4. [03-REQ-4.4] THE `speclib/tools.py` module SHALL define tool definitions (JSON-compatible dicts) for: `submit_assessment`, `submit_prd_update`, and `submit_artifact`.
5. [03-REQ-4.5] EACH tool definition SHALL include a `name`, `description`, and `input_schema` that matches the expected output structure (Assessment, PRD update, or artifact JSON).
6. [03-REQ-4.6] THE `submit_assessment` tool input_schema SHALL enforce `quality` as an enum of `["ready", "needs_refinement", "incomplete"]`, `summary` as a required string, `gaps` as an array of strings, and `questions` as an array of objects with `id`, `text`, `context`, `options`, and `required` fields.

#### Edge Cases
1. [03-REQ-4.E1] IF a prompt template is called with missing required parameters (e.g., no prd_text), THEN it SHALL raise a `ValueError` with a descriptive message.

### Requirement 5: Agent Error Handling

**User Story:** As a user, I want the agent to handle transient API errors gracefully with retries, so that temporary failures do not interrupt my workflow.

#### Acceptance Criteria
1. [03-REQ-5.1] WHEN the Anthropic API returns HTTP 429 (rate limited) or 5xx (server error), THE agent SHALL retry the request up to 3 times with exponential backoff (base delay 1 second, doubling each retry).
2. [03-REQ-5.2] WHEN all retry attempts are exhausted, THE agent SHALL raise an `AgentError` wrapping the original API error.
3. [03-REQ-5.3] WHEN the Anthropic API returns a 4xx error other than 429, THE agent SHALL raise an `AgentError` immediately without retrying.
4. [03-REQ-5.4] THE `AgentError` exception SHALL inherit from `SpeclibError` and SHALL provide the original exception as a `__cause__`.
5. [03-REQ-5.5] WHEN the agent returns a response that cannot be parsed as the expected structured output, THE agent SHALL raise an `AgentError` with details about the parsing failure.

#### Edge Cases
1. [03-REQ-5.E1] IF the API connection times out, THE agent SHALL treat it as a transient error and retry.
2. [03-REQ-5.E2] IF the retry delay would exceed 30 seconds total cumulative wait, THE agent SHALL abandon retries and raise immediately.

### Requirement 6: Session Integration

**User Story:** As a developer, I want the agent pipeline wired into SpecSession, so that session methods delegate to the agent and persist results correctly.

#### Acceptance Criteria
1. [03-REQ-6.1] WHEN `SpecSession.assess()` is called, THE session SHALL create a `SpecAgent` using the client from `create_client()`, call `assess_prd()` with the session's PRD text and spec name, persist the returned Assessment to `_session.json`, and transition the session state.
2. [03-REQ-6.2] WHEN `SpecSession.refine(answers)` is called, THE session SHALL call `SpecAgent.refine_prd()` with the current PRD text, the provided answers, and the most recent Assessment, update the PRD file with the returned text, persist the new Assessment to `_session.json`, and transition state.
3. [03-REQ-6.3] WHEN `SpecSession.generate()` is called, THE session SHALL call `SpecAgent.generate_artifacts()` with the accepted PRD text, spec_id, and spec_name, write each returned artifact to the spec directory as the corresponding `.json` file, run cross-file integrity validation via afspec, and transition state to `generated`.
4. [03-REQ-6.4] IF the agent raises an `AgentError` during any session method, THE session SHALL NOT transition state, SHALL persist the error in `_session.json`, and SHALL re-raise the `AgentError` to the caller.
5. [03-REQ-6.5] THE session SHALL store Assessment history: each call to `assess()` or `refine()` SHALL append the new Assessment to the `assessment_history` list in `_session.json`.

#### Edge Cases
1. [03-REQ-6.E1] IF `generate()` succeeds for `requirements.json` but fails for `test_spec.json`, THEN THE session SHALL persist the partial result (requirements.json on disk), remain in `generating` state, and re-raise the `AgentError`.
2. [03-REQ-6.E2] IF the session is resumed after a partial generation failure, THEN `generate()` SHALL detect existing artifacts and re-generate only the missing ones.

## Source

Source: Input provided by user via interactive prompt
