# Requirements Document

## Introduction

This specification defines the campaign directory management and spec authoring
session model for speclib. These components manage the working directory
structure and track the stateful lifecycle of authoring a single spec.

## Glossary

| Term | Definition |
|------|-----------|
| Campaign | A working directory containing `campaign.yaml` and one or more spec subdirectories |
| campaign.yaml | YAML file at the campaign root containing campaign metadata (name, description, timestamps) |
| SpecSession | A stateful authoring session tracking the lifecycle of creating one spec |
| SessionState | Enum of session lifecycle states: init, assessing, refining, prd_accepted, generating, generated |
| _session.json | JSON file within a spec directory persisting the session's current state and history |
| spec directory | A subdirectory within a campaign following the `{NN}_{snake_case_name}` naming convention |

## Requirements

### Requirement 1: Campaign Creation

**User Story:** As a user, I want to create a new campaign working directory, so that I have an organized location for authoring related specs.

#### Acceptance Criteria
1. [02-REQ-1.1] WHEN `Campaign.create(path, name, description)` is called with a valid path, THE system SHALL create the directory (if it does not exist), write a `campaign.yaml` with the provided name, description, and current timestamps, and return a `Campaign` instance.
2. [02-REQ-1.2] WHEN `Campaign.create()` is called with a path that already contains `campaign.yaml`, THE system SHALL raise a `CampaignError` indicating the campaign already exists.
3. [02-REQ-1.3] THE `campaign.yaml` SHALL contain the fields: `name` (str), `description` (str), `created_at` (ISO 8601), `updated_at` (ISO 8601).

#### Edge Cases
1. [02-REQ-1.E1] IF the target path exists and is non-empty but does not contain `campaign.yaml`, THEN THE system SHALL raise a `CampaignError` indicating the directory is not empty and not a campaign.
2. [02-REQ-1.E2] IF the target path's parent directory does not exist, THEN THE system SHALL raise a `CampaignError` rather than creating intermediate directories.

### Requirement 2: Campaign Opening

**User Story:** As a user, I want to open an existing campaign directory, so that I can manage specs within it.

#### Acceptance Criteria
1. [02-REQ-2.1] WHEN `Campaign.open(path)` is called with a path containing `campaign.yaml`, THE system SHALL parse the YAML, populate `CampaignMetadata`, and return a `Campaign` instance.
2. [02-REQ-2.2] WHEN `campaign.specs()` is called, THE system SHALL return a list of `Path` objects for all spec subdirectories matching the `{NN}_{snake_case_name}` pattern, sorted by numeric prefix, and SHALL exclude `archive/` and `_session.json` files.

#### Edge Cases
1. [02-REQ-2.E1] IF the path does not contain `campaign.yaml`, THEN THE system SHALL raise a `CampaignError`.
2. [02-REQ-2.E2] IF `campaign.yaml` contains invalid YAML, THEN THE system SHALL raise a `CampaignError` with parse error detail.

### Requirement 3: Spec Creation Within a Campaign

**User Story:** As a user, I want to create a new spec within a campaign, so that I can begin authoring a spec from a PRD.

#### Acceptance Criteria
1. [02-REQ-3.1] WHEN `campaign.new_spec(spec_name, prd, mode)` is called with a string PRD, THE system SHALL create a new spec directory with the next available numeric prefix, write `prd.md` with YAML frontmatter and the PRD content as body, create an initial `_session.json` in `init` state, and return a `SpecSession` instance.
2. [02-REQ-3.2] WHEN `campaign.new_spec()` is called with a `Path` pointing to an existing file, THE system SHALL copy the file's content into `prd.md` in the new spec directory.
3. [02-REQ-3.3] THE spec directory name SHALL follow the pattern `{NN}_{snake_case_name}` where NN is `max(existing numeric prefixes) + 1`, starting from `01` if no specs exist.
4. [02-REQ-3.4] THE generated `prd.md` frontmatter SHALL include `spec_id`, `spec_name`, `title`, `status: draft`, `created_at`, `updated_at`, `owner`, `source`, and `schema_version: 1`.

#### Edge Cases
1. [02-REQ-3.E1] IF `spec_name` contains characters outside `[a-z0-9_]` or does not start with a letter, THEN THE system SHALL raise a `CampaignError` with a validation message.
2. [02-REQ-3.E2] IF the PRD is a `Path` that does not exist, THEN THE system SHALL raise a `CampaignError`.

### Requirement 4: Session State Machine

**User Story:** As a user, I want the session to enforce a valid authoring lifecycle, so that I cannot skip steps or perform operations out of order.

#### Acceptance Criteria
1. [02-REQ-4.1] THE session SHALL support the following states: `init`, `assessing`, `refining`, `prd_accepted`, `generating`, `generated`.
2. [02-REQ-4.2] THE session SHALL enforce these legal transitions: `init→assessing`, `init→prd_accepted` (one-shot mode), `assessing→refining`, `assessing→prd_accepted`, `refining→assessing`, `refining→prd_accepted`, `prd_accepted→generating`, `generating→generated`.
3. [02-REQ-4.3] IF a method is called that requires a state the session is not in, THEN THE system SHALL raise a `SessionError` naming the current state and the required state.
4. [02-REQ-4.4] WHEN `accept_prd()` is called while the session is in `init`, `assessing`, or `refining` state, THE system SHALL transition the state to `prd_accepted`.

#### Edge Cases
1. [02-REQ-4.E1] IF `generate()` is called when the session is not in `prd_accepted` state, THEN THE system SHALL raise a `SessionError`.
2. [02-REQ-4.E2] IF `assess()` is called when the session is in `generated` state, THEN THE system SHALL raise a `SessionError` (generated is terminal for assessment).

### Requirement 5: Session Persistence

**User Story:** As a user, I want my session progress to be saved automatically, so that I can resume an interrupted authoring session.

#### Acceptance Criteria
1. [02-REQ-5.1] WHEN any session state transition occurs, THE system SHALL atomically write the updated session state to `_session.json` in the spec directory.
2. [02-REQ-5.2] WHEN `SpecSession.resume(spec_dir)` is called, THE system SHALL read `_session.json`, restore the session state including assessment history and Q&A exchanges, and return a `SpecSession` instance in the persisted state.
3. [02-REQ-5.3] THE `_session.json` SHALL contain: `state` (SessionState), `prd_path` (str), `assessment_history` (list of Assessment dicts), `qa_exchanges` (list of Q&A dicts), `generated_artifacts` (list of artifact names), and `mode` ("interactive" or "one-shot").

#### Edge Cases
1. [02-REQ-5.E1] IF `_session.json` does not exist when `resume()` is called, THEN THE system SHALL raise a `SessionError`.
2. [02-REQ-5.E2] IF `_session.json` contains invalid JSON, THEN THE system SHALL raise a `SessionError` with parse detail.

### Requirement 6: Session Validation and Rendering

**User Story:** As a user, I want to validate and render my spec at any point, so that I can check its status.

#### Acceptance Criteria
1. [02-REQ-6.1] WHEN `session.validate()` is called and all four required artifacts exist in the spec directory, THE system SHALL load the spec via `afspec.load_spec()`, run `afspec.validate()`, and return a `ValidationResult` containing validity status and error lists.
2. [02-REQ-6.2] WHEN `session.render(combined=True)` is called and all four required artifacts exist, THE system SHALL load the spec and return `afspec.render_combined()` output.
3. [02-REQ-6.3] WHEN `session.render(combined=False)` is called and all four required artifacts exist, THE system SHALL load the spec and return individually rendered artifacts as a dict mapping artifact name to markdown string.

#### Edge Cases
1. [02-REQ-6.E1] IF `validate()` or `render()` is called before all required artifacts exist, THEN THE system SHALL raise a `SessionError` indicating which artifacts are missing.

## Source

Source: Input provided by user via interactive prompt
