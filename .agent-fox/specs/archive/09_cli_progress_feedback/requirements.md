# Requirements Document

## Introduction

Adds animated spinner feedback to the `spec` CLI's long-running commands
and a global `--quiet` flag for scripted use.

## Glossary

- **Spinner**: An animated character sequence (braille dots) displayed on
  stderr that indicates work is in progress, accompanied by a status message.
- **Phase message**: A text description of the current operation stage, shown
  alongside the spinner (e.g., "Assessing PRD...").
- **Quiet mode**: A CLI mode enabled by `--quiet` / `-q` that suppresses all
  spinner and status output, emitting only final results and errors.
- **TTY**: A terminal device capable of cursor positioning and overwriting.
  When stderr is not a TTY (e.g., piped to a file), animation is disabled.

## Requirements

### Requirement 1: Spinner During Long-Running Commands

**User Story:** As a user running `spec` interactively, I want to see a
spinner with a status message during long operations, so that I know the
tool is working.

#### Acceptance Criteria

1. [09-REQ-1.1] WHILE the `assess` command is calling the agent API, THE CLI
   SHALL display an animated spinner on stderr with the message
   "Assessing PRD...".

2. [09-REQ-1.2] WHILE the `refine --answers` command is calling the agent
   API, THE CLI SHALL display an animated spinner on stderr with the message
   "Refining PRD with answers...".

3. [09-REQ-1.3] WHILE the `generate` command is generating an artifact, THE
   CLI SHALL display an animated spinner on stderr with the message
   "Generating {artifact_name}..." where `{artifact_name}` is the name of
   the artifact currently being generated.

4. [09-REQ-1.4] WHEN an artifact is successfully generated during `generate`,
   THE CLI SHALL print a completion line to stderr (e.g.,
   "Generated requirements") before updating the spinner for the next
   artifact.

5. [09-REQ-1.5] WHEN a command completes successfully, THE CLI SHALL stop
   the spinner and clear the spinner line from stderr.

#### Edge Cases

1. [09-REQ-1.E1] IF the command raises an error, THEN THE CLI SHALL stop the
   spinner before printing the error message.

2. [09-REQ-1.E2] IF the user presses Ctrl-C during a spinner, THEN THE CLI
   SHALL stop the spinner cleanly and allow Click's default keyboard
   interrupt handling to proceed.

### Requirement 2: Stderr Output

**User Story:** As an agent piping `spec` output, I want spinner output
on stderr only, so that stdout remains clean for JSON parsing.

#### Acceptance Criteria

1. [09-REQ-2.1] THE spinner and all phase messages SHALL be written to stderr,
   not stdout.

2. [09-REQ-2.2] WHEN stderr is not a TTY, THE CLI SHALL print phase messages
   as plain text lines to stderr without animation.

### Requirement 3: Global Quiet Flag

**User Story:** As a script author, I want a `--quiet` flag to suppress
spinner and status output, so that only results and errors appear.

#### Acceptance Criteria

1. [09-REQ-3.1] THE `spec` CLI group SHALL accept a `--quiet` / `-q`
   global option.

2. [09-REQ-3.2] WHEN `--quiet` is set, THE CLI SHALL suppress all spinner
   animation and phase messages.

3. [09-REQ-3.3] WHEN `--quiet` is set, THE CLI SHALL still print final
   command output (assessment results, JSON export, error messages) to
   stdout/stderr as appropriate.

4. [09-REQ-3.4] THE `--quiet` flag SHALL be accessible to all subcommands
   via the Click context object at `ctx.obj["quiet"]`.

### Requirement 4: Spinner Context Manager

**User Story:** As a developer adding spinner support to a command, I want
a simple context-manager API, so that adding spinner to a command is a
two-line change.

#### Acceptance Criteria

1. [09-REQ-4.1] THE `speclib` package SHALL provide a `StatusSpinner` class
   in `speclib/ui.py` that can be used as a context manager AND returns a
   handle with an `update(message)` method to change the displayed message.

2. [09-REQ-4.2] THE `StatusSpinner` constructor SHALL accept a `message`
   string and a `quiet` boolean, AND when `quiet` is `True`, all display
   operations SHALL be no-ops.
