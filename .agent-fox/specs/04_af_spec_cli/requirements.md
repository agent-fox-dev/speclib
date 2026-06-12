# Requirements Document

## Introduction

This specification defines the `spec` command-line interface for speclib.
The CLI provides local-only campaign management and spec authoring commands
using the Click framework, wrapping the speclib library for all business
logic. Hub-related commands (submit, import) are out of scope.

## Glossary

| Term | Definition |
|------|-----------|
| spec | The CLI entry point installed as a console script via pyproject.toml |
| Click | Python CLI framework used for argument parsing and help generation |
| campaign directory | A directory containing `campaign.yaml` and zero or more spec subdirectories |
| spec argument | A CLI argument that identifies a spec by full directory name (e.g., `01_data_models`) or numeric prefix (e.g., `01`) |
| session state | The current lifecycle state of a spec authoring session (init, assessing, refining, prd_accepted, generating, generated) |
| CWD | Current working directory from which the CLI is invoked |
| Rich | Optional Python library for formatted terminal output (tables, colors) |

## Requirements

### Requirement 1: Campaign Init Command

**User Story:** As a user, I want to create a new campaign directory from the command line, so that I can begin authoring specs in an organized workspace.

#### Acceptance Criteria
1. [04-REQ-1.1] WHEN `spec init <path> --name <name> --description <text>` is invoked, THE CLI SHALL call `Campaign.create(path, name, description)` and print a confirmation message including the absolute path of the created campaign directory.
2. [04-REQ-1.2] WHEN `spec init` is invoked without `--name`, THE CLI SHALL use the directory's basename as the campaign name.
3. [04-REQ-1.3] WHEN `spec init` is invoked without `--description`, THE CLI SHALL use an empty string as the description.
4. [04-REQ-1.4] WHEN `Campaign.create()` raises a `CampaignError`, THE CLI SHALL print the error message to stderr and exit with code 1.

#### Edge Cases
1. [04-REQ-1.E1] IF `<path>` is a relative path, THEN THE CLI SHALL resolve it to an absolute path before passing to `Campaign.create()`.

### Requirement 2: Campaign List Command

**User Story:** As a user, I want to list all specs in a campaign directory with their session state, so that I can see what specs exist and their progress.

#### Acceptance Criteria
1. [04-REQ-2.1] WHEN `spec list` is invoked from within a campaign directory, THE CLI SHALL display a table with columns: spec number, spec name, session state, and artifact count.
2. [04-REQ-2.2] WHEN `spec list <campaign-dir>` is invoked with an explicit path, THE CLI SHALL open that directory as the campaign.
3. [04-REQ-2.3] WHEN a campaign directory contains no specs, THE CLI SHALL print a message indicating the campaign is empty and exit with code 0.
4. [04-REQ-2.4] THE table output SHALL sort specs by numeric prefix in ascending order.

#### Edge Cases
1. [04-REQ-2.E1] IF the directory is not a campaign directory (no `campaign.yaml`), THEN THE CLI SHALL print an error message explaining what a campaign directory is and exit with code 1.

### Requirement 3: Spec New Command

**User Story:** As a user, I want to create a new spec from a PRD file, so that I can begin the spec authoring process.

#### Acceptance Criteria
1. [04-REQ-3.1] WHEN `spec new <prd-file>` is invoked, THE CLI SHALL call `campaign.new_spec()` with the PRD file contents and print the created spec directory name.
2. [04-REQ-3.2] WHEN `--name <spec-name>` is provided, THE CLI SHALL use it as the spec name. WHEN omitted, THE CLI SHALL derive the name from the PRD filename (stripping extension, converting to snake_case).
3. [04-REQ-3.3] WHEN `--one-shot` is provided, THE CLI SHALL set the session mode to "one-shot" (skipping the interactive refinement loop).
4. [04-REQ-3.4] WHEN the PRD file does not exist, THE CLI SHALL print an error message and exit with code 1.

#### Edge Cases
1. [04-REQ-3.E1] IF the derived or provided spec name is invalid (not matching `[a-z][a-z0-9_]*`), THEN THE CLI SHALL print a validation error explaining the naming rules and exit with code 1.

### Requirement 4: Spec Assess Command

**User Story:** As a user, I want to run or re-run PRD assessment from the command line, so that I can get quality feedback and improvement suggestions for my PRD.

#### Acceptance Criteria
1. [04-REQ-4.1] WHEN `spec assess <spec>` is invoked, THE CLI SHALL resolve the spec, call `session.assess()`, and print the assessment summary including quality score, identified gaps, and questions for the user.
2. [04-REQ-4.2] THE assessment output SHALL be formatted with clear section headers for quality, gaps, and questions.
3. [04-REQ-4.3] WHEN the session is not in a state that allows assessment (not `init` or `refining`), THE CLI SHALL print an error explaining the current state and which states allow assessment, then exit with code 1.

#### Edge Cases
1. [04-REQ-4.E1] IF the agent pipeline raises an error during assessment, THEN THE CLI SHALL print the error message to stderr and exit with code 2.

### Requirement 5: Spec Refine Command

**User Story:** As a user, I want to submit answers to assessment questions and have the agent update the PRD, so that I can iteratively improve my spec.

#### Acceptance Criteria
1. [04-REQ-5.1] WHEN `spec refine <spec> --answers <file>` is invoked, THE CLI SHALL read the JSON file, call `session.refine(answers)`, and print a confirmation that the PRD has been updated.
2. [04-REQ-5.2] WHEN the answers file does not exist, THE CLI SHALL print an error message and exit with code 1.
3. [04-REQ-5.3] WHEN the answers file contains invalid JSON, THE CLI SHALL print a parse error message and exit with code 1.
4. [04-REQ-5.4] WHEN the session is not in `refining` state, THE CLI SHALL print an error explaining the current state and exit with code 1.
5. [04-REQ-5.5] AFTER successful refinement, THE CLI SHALL print the updated assessment summary (same format as the assess command).

#### Edge Cases
1. [04-REQ-5.E1] IF the answers JSON does not conform to the expected schema (must be an object mapping question IDs to answer strings), THEN THE CLI SHALL print a schema validation error and exit with code 1.

### Requirement 6: Spec Accept Command

**User Story:** As a user, I want to accept the PRD and end the refinement loop, so that I can proceed to artifact generation.

#### Acceptance Criteria
1. [04-REQ-6.1] WHEN `spec accept <spec>` is invoked, THE CLI SHALL call `session.accept_prd()` and print a confirmation message including the new session state.
2. [04-REQ-6.2] WHEN the session is not in a state that allows acceptance (not `assessing` or `refining`), THE CLI SHALL print an error explaining the current state and which states allow acceptance, then exit with code 1.

#### Edge Cases
(None beyond state validation covered in 04-REQ-6.2.)

### Requirement 7: Spec Generate Command

**User Story:** As a user, I want to generate the full set of JSON artifacts from my accepted PRD, so that I can produce the complete spec package.

#### Acceptance Criteria
1. [04-REQ-7.1] WHEN `spec generate <spec>` is invoked, THE CLI SHALL call `session.generate()` and print progress indicators for each artifact being generated.
2. [04-REQ-7.2] WHEN generation completes successfully, THE CLI SHALL print a summary listing all generated artifacts.
3. [04-REQ-7.3] WHEN the session is not in `prd_accepted` state, THE CLI SHALL print an error explaining the current state and that the PRD must be accepted first, then exit with code 1.

#### Edge Cases
1. [04-REQ-7.E1] IF the agent pipeline raises an error during generation, THEN THE CLI SHALL print the error message to stderr and exit with code 2.

### Requirement 8: Spec Validate Command

**User Story:** As a user, I want to run schema and cross-file validation on a spec, so that I can verify correctness before using or sharing it.

#### Acceptance Criteria
1. [04-REQ-8.1] WHEN `spec validate <spec>` is invoked, THE CLI SHALL call `session.validate()` and display the validation results.
2. [04-REQ-8.2] WHEN validation passes with no errors, THE CLI SHALL print a success message and exit with code 0.
3. [04-REQ-8.3] WHEN validation finds errors, THE CLI SHALL print each error with its file, path (within the file), and error message, then exit with code 1.
4. [04-REQ-8.4] THE error list SHALL be formatted as a table with columns: file, path, message.

#### Edge Cases
1. [04-REQ-8.E1] IF required artifacts are missing (spec not yet generated), THEN THE CLI SHALL print a message listing which artifacts are missing and exit with code 1.

### Requirement 9: Spec Render Command

**User Story:** As a user, I want to render a spec as markdown, so that I can review it in a human-readable format.

#### Acceptance Criteria
1. [04-REQ-9.1] WHEN `spec render <spec>` is invoked, THE CLI SHALL call `session.render()` and print the rendered markdown to stdout.
2. [04-REQ-9.2] WHEN `--combined` is provided, THE CLI SHALL call `session.render(combined=True)` to produce a single combined markdown document.
3. [04-REQ-9.3] WHEN `--combined` is not provided, THE CLI SHALL call `session.render(combined=False)` and print each artifact's rendered markdown separated by a header line.

#### Edge Cases
1. [04-REQ-9.E1] IF required artifacts are missing, THEN THE CLI SHALL print a message listing which artifacts are missing and exit with code 1.

### Requirement 10: Spec Show and Status Commands

**User Story:** As a user, I want to inspect the current session state and view individual artifacts, so that I can understand where I am in the authoring process.

#### Acceptance Criteria
1. [04-REQ-10.1] WHEN `spec status` is invoked without a spec argument, THE CLI SHALL display a table of all specs in the campaign with their session state (same as `list` but focused on state).
2. [04-REQ-10.2] WHEN `spec status <spec>` is invoked, THE CLI SHALL display detailed session state for that spec, including: state, mode, assessment count, Q&A exchange count, and list of generated artifacts.
3. [04-REQ-10.3] WHEN `spec show <spec>` is invoked without `--artifact`, THE CLI SHALL display the session state summary (same as `status <spec>`).
4. [04-REQ-10.4] WHEN `spec show <spec> --artifact <name>` is invoked, THE CLI SHALL read and display the content of the named artifact file from the spec directory.
5. [04-REQ-10.5] WHEN the named artifact does not exist, THE CLI SHALL print an error listing available artifacts and exit with code 1.

#### Edge Cases
1. [04-REQ-10.E1] IF the spec argument does not match any spec in the campaign, THEN THE CLI SHALL print an error listing available specs by number and name, and exit with code 1.

### Cross-Cutting Requirements

#### Campaign Directory Resolution

1. [04-REQ-CC.1] THE `spec` command group SHALL accept a `--campaign-dir` option that overrides the default CWD-based campaign directory resolution.
2. [04-REQ-CC.2] WHEN `--campaign-dir` is not provided, THE CLI SHALL use the current working directory as the campaign directory.
3. [04-REQ-CC.3] WHEN a subcommand requires a campaign directory and the resolved directory does not contain `campaign.yaml`, THE CLI SHALL print an error message explaining that the command must be run from within a campaign directory (or use `--campaign-dir`), and exit with code 1.

#### Spec Argument Resolution

4. [04-REQ-CC.4] THE CLI SHALL resolve a `<spec>` argument by scanning campaign spec directories for a match by full directory name or by numeric prefix (e.g., `01` matches `01_data_models`).
5. [04-REQ-CC.5] IF the `<spec>` argument does not match any spec, THE CLI SHALL list all available specs and exit with code 1.

#### Exit Codes

6. [04-REQ-CC.6] THE CLI SHALL use exit code 0 for success, 1 for user errors (bad arguments, wrong state, not found), and 2 for internal errors (unexpected exceptions).

## Source

Source: Input provided by user via interactive prompt
