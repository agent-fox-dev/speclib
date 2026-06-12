# Requirements Document

## Introduction

This specification defines the agent CLI skill file for spec authoring and
the installation utility that deploys it. The skill is a markdown prompt file
that instructs agent CLIs (Claude Code, Gemini CLI) how to drive spec
authoring workflows using `spec` CLI commands.

## Glossary

| Term | Definition |
|------|-----------|
| Skill file | A markdown file loaded by agent CLIs as context, providing domain-specific workflow instructions |
| Interactive mode | Step-by-step spec authoring with conversational user interaction between assess/refine/generate phases |
| One-shot mode | Single-command spec generation from a PRD with no intermediate user interaction |
| Question ID | The unique identifier of an assessment question (e.g., `Q1`, `Q2`) used to map user answers to structured input |
| Agent CLI | A command-line interface for AI agents (e.g., Claude Code, Gemini CLI) that supports skill loading |

## Requirements

### Requirement 1: Skill File Structure and Content

**User Story:** As an agent CLI user, I want a well-structured skill file that provides clear instructions for spec authoring, so that the agent can guide me through the process.

#### Acceptance Criteria
1. [05-REQ-1.1] THE skill file SHALL exist at `speclib/skill/spec.md` within the Python package.
2. [05-REQ-1.2] THE skill file SHALL include a header section identifying the skill name (`spec`), a description of its purpose, and trigger conditions describing when the skill should be activated.
3. [05-REQ-1.3] THE skill file SHALL document all `spec` CLI commands relevant to spec authoring: `init`, `new`, `assess`, `refine`, `accept`, `generate`, `status`, `validate`, and `render`.
4. [05-REQ-1.4] THE skill file SHALL include at least one usage example (with expected invocation and sample output description) for each documented command.
5. [05-REQ-1.5] THE skill file SHALL be loadable as valid markdown with no syntax errors.

#### Edge Cases
1. [05-REQ-1.E1] IF the skill file is loaded by an agent CLI that does not support all referenced CLI commands, THEN THE skill file SHALL instruct the agent to report the unsupported command to the user rather than failing silently.

### Requirement 2: Interactive Mode Workflow Instructions

**User Story:** As an agent CLI user, I want the skill to describe the interactive spec authoring workflow, so that the agent can guide me through each step.

#### Acceptance Criteria
1. [05-REQ-2.1] THE skill file SHALL describe the interactive workflow as a numbered sequence: (1) open or create campaign, (2) create new spec from PRD, (3) run assessment, (4) present questions to user, (5) refine based on answers, (6) repeat or accept PRD, (7) generate spec.
2. [05-REQ-2.2] THE skill file SHALL instruct the agent to present the assessment result (summary, suggestions, questions) to the user in a readable format after running `spec assess`.
3. [05-REQ-2.3] THE skill file SHALL instruct the agent to ask the user whether to accept the PRD or continue refining after each assessment round.

#### Edge Cases
1. [05-REQ-2.E1] IF the assessment produces zero questions, THEN THE skill file SHALL instruct the agent to inform the user that the PRD is ready for acceptance and proceed to the accept step.

### Requirement 3: One-Shot Mode Workflow Instructions

**User Story:** As an agent CLI user, I want the skill to support immediate spec generation from a PRD, so that I can get a complete spec without interactive steps.

#### Acceptance Criteria
1. [05-REQ-3.1] THE skill file SHALL describe the one-shot workflow as a single invocation: `spec new <prd-file> --one-shot` followed by automatic assess, accept, and generate.
2. [05-REQ-3.2] THE skill file SHALL instruct the agent to present the final generated spec to the user for review after one-shot generation completes.

#### Edge Cases
1. [05-REQ-3.E1] IF one-shot generation fails (non-zero exit from any step), THEN THE skill file SHALL instruct the agent to report the error and suggest falling back to interactive mode.

### Requirement 4: Question Presentation and Answer Mapping

**User Story:** As an agent CLI user, I want the agent to present assessment questions naturally and map my answers back to Question IDs, so that I can answer questions conversationally.

#### Acceptance Criteria
1. [05-REQ-4.1] THE skill file SHALL instruct the agent to parse question output from `spec assess`, extracting each question's ID and text.
2. [05-REQ-4.2] THE skill file SHALL instruct the agent to present questions to the user in natural language, numbering them for reference but omitting internal Question IDs from the user-facing presentation.
3. [05-REQ-4.3] THE skill file SHALL instruct the agent to accept user answers in natural language (full sentences, partial answers, or grouped responses to multiple questions) and map each answer to the corresponding Question ID.
4. [05-REQ-4.4] THE skill file SHALL instruct the agent to pass mapped answers to `spec refine` using the `--answers` flag with a JSON mapping of Question ID to answer text.

#### Edge Cases
1. [05-REQ-4.E1] IF the user provides an answer that cannot be clearly mapped to any question, THEN THE skill file SHALL instruct the agent to ask for clarification on which question the user is addressing.
2. [05-REQ-4.E2] IF the user answers only some questions, THEN THE skill file SHALL instruct the agent to pass the partial answers to `refine` and note which questions remain unanswered.

### Requirement 5: Skill Installation Mechanism

**User Story:** As a user, I want to install the skill file to my agent CLI with a single command, so that I do not have to manually copy files.

#### Acceptance Criteria
1. [05-REQ-5.1] THE `spec install-skill` command SHALL detect the target agent CLI by checking for known configuration directories: `~/.claude/` (Claude Code) and `~/.gemini/` (Gemini CLI).
2. [05-REQ-5.2] WHEN a supported agent CLI is detected, THE command SHALL copy `speclib/skill/spec.md` to the agent's skill directory (e.g., `~/.claude/skills/spec.md`).
3. [05-REQ-5.3] WHEN `spec install-skill --target claude` is specified, THE command SHALL install to `~/.claude/skills/spec.md` regardless of autodetection.
4. [05-REQ-5.4] WHEN the skill file already exists at the target location, THE command SHALL overwrite it and print a message indicating the skill was updated.
5. [05-REQ-5.5] THE command SHALL print a success message including the installed file path after installation.

#### Edge Cases
1. [05-REQ-5.E1] IF no supported agent CLI is detected and no `--target` is specified, THEN THE command SHALL exit with an error listing supported agent CLIs and the `--target` flag.
2. [05-REQ-5.E2] IF the target skill directory does not exist, THEN THE command SHALL create it before copying the skill file.
3. [05-REQ-5.E3] IF the skill source file is missing from the package (e.g., corrupt installation), THEN THE command SHALL raise a `SpeclibError` indicating the package is incomplete.

### Requirement 6: Error Handling Instructions in the Skill

**User Story:** As an agent CLI user, I want the skill to include error handling guidance, so that the agent can recover from failures gracefully.

#### Acceptance Criteria
1. [05-REQ-6.1] THE skill file SHALL include an error handling section describing common `spec` error conditions and recovery steps.
2. [05-REQ-6.2] THE skill file SHALL instruct the agent to check the exit code of every `spec` command and report failures to the user with the stderr output.
3. [05-REQ-6.3] THE skill file SHALL instruct the agent to use `spec status` to check the current session state before attempting operations, to avoid illegal state transitions.

#### Edge Cases
1. [05-REQ-6.E1] IF `spec` is not found on the PATH, THEN THE skill file SHALL instruct the agent to tell the user to install speclib (`uv pip install speclib`) and retry.

## Source

Source: Input provided by user via interactive prompt
