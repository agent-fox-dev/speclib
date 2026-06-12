# PRD: CLI Progress Feedback and Quiet Mode

## Intent

Add animated spinner feedback and status messages to long-running CLI commands
(`assess`, `refine --answers`, `generate`) so that interactive users see what
the tool is doing, and add a global `--quiet` flag to suppress all non-essential
output for scripted use.

## Background

Currently, the `spec` CLI gives no visual feedback during long-running
operations. Commands like `assess` and `generate` make API calls that can
take 10-60 seconds. During this time the terminal is completely silent — the
user has no way to know whether the tool is working, stuck, or crashed.

The `agent-fox` project uses Rich's `Live` display with animated braille
spinners and phase messages to provide real-time feedback. The `spec` CLI
should adopt a similar but simpler pattern — it has fewer concurrent tasks
and a more linear flow.

## Requirements

1. Long-running commands (`assess`, `refine --answers`, `generate`) SHALL
   display an animated spinner with a descriptive status message on stderr
   while the API call is in progress.

2. Each command SHALL display phase-appropriate messages:
   - `assess`: "Assessing PRD..."
   - `refine`: "Refining PRD with answers..."
   - `generate`: "Generating {artifact_name}..." for each artifact in
     sequence, and a completion message after each artifact.

3. The spinner SHALL be written to stderr so that stdout remains clean for
   machine-parseable output (e.g., JSON from `refine` without `--answers`).

4. A global `--quiet` / `-q` flag SHALL suppress all spinner and status
   output. Only success/error messages and command output (assessment JSON,
   question export JSON) SHALL be printed.

5. The spinner SHALL stop cleanly on success, error, or keyboard interrupt.

6. On non-TTY stderr (piped output), the spinner animation SHALL be disabled
   but phase messages SHALL still be printed as plain text lines.

## Design Decisions

1. **Use Rich for spinner display.** Rich provides `Console`, `Live`, and
   `Spinner` with TTY detection, thread-safe output, and clean terminal
   handling. It is already used by `agent-fox` and is a proven choice for
   CLI progress display.

2. **Spinner module at `speclib/ui.py`.** A single module provides a
   context-manager `Spinner` class that wraps Rich's `Live` + `Spinner`.
   Commands use it as `with Spinner("Assessing PRD...", quiet=quiet): ...`.

3. **`--quiet` propagated via Click context.** The flag is added to the
   `main` group and stored in `ctx.obj["quiet"]`. Commands read it from
   context, matching the `--campaign-dir` pattern already used.

4. **Stderr for all progress output.** `Rich.Console(stderr=True)` ensures
   spinners and status messages go to stderr. Command results (assessments,
   JSON) continue to go to stdout via `click.echo`.

5. **`generate` shows per-artifact progress.** Because `generate` calls the
   API three times sequentially (requirements, test_spec, tasks), the spinner
   message updates between artifacts using the existing `on_artifact`
   callback in `session.generate()`.

## Non-Goals

- Progress bars with percentage (API calls have no progress increments).
- Concurrent task display (spec is sequential).
- Token counting or turn display (unnecessary for this tool).
- Colorized output beyond what Rich provides by default.

## Dependencies

| Spec | From Group | To Group | Relationship |
|------|-----------|----------|--------------|
| 04_af_spec_cli | 3 | 2 | CLI command handlers defined in group 3; group 3 is where assess/refine/generate commands are implemented |

## Source

Source: Input provided by user via interactive prompt.
