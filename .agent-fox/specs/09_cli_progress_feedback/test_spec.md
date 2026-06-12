# Test Specification: CLI Progress Feedback

## Overview

Tests verify spinner display behavior, quiet mode suppression, stderr-only
output, and proper cleanup on error/interrupt.

## Test Cases

### TS-09-1: Assess shows spinner

**Requirement:** 09-REQ-1.1
**Type:** unit
**Description:** Verifies `assess` writes spinner/status output to stderr.

**Preconditions:**
- Mocked session with agent returning assessment.

**Input:**
- CLI invocation: `spec assess 01` (no `--quiet`).

**Expected:**
- stderr contains "Assessing PRD".
- Exit code 0.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["assess", "01"])
ASSERT result.exit_code == 0
ASSERT "Assessing" IN captured_stderr
```

### TS-09-2: Refine with answers shows spinner

**Requirement:** 09-REQ-1.2
**Type:** unit
**Description:** Verifies `refine --answers` shows status on stderr.

**Preconditions:**
- Mocked session, valid answers file.

**Input:**
- CLI invocation: `spec refine 01 --answers answers.json`.

**Expected:**
- stderr contains "Refining".

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["refine", "01", "--answers", file])
ASSERT "Refining" IN captured_stderr
```

### TS-09-3: Generate shows per-artifact progress

**Requirement:** 09-REQ-1.3, 09-REQ-1.4
**Type:** unit
**Description:** Verifies `generate` shows artifact-specific messages.

**Preconditions:**
- Mocked session with generate returning artifacts.

**Input:**
- CLI invocation: `spec generate 01`.

**Expected:**
- stderr contains "Generating requirements" or similar.
- stderr contains completion messages for each artifact.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["generate", "01"])
ASSERT "Generating" IN captured_stderr
ASSERT "Generated" IN captured_stderr
```

### TS-09-4: Spinner stops on success

**Requirement:** 09-REQ-1.5
**Type:** unit
**Description:** Verifies spinner is stopped after command completes.

**Preconditions:**
- Mocked session.

**Input:**
- Successful `assess` invocation.

**Expected:**
- No spinner animation remnants in stderr after command exits.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["assess", "01"])
ASSERT result.exit_code == 0
# Spinner line is cleared (transient)
```

### TS-09-5: Spinner output on stderr only

**Requirement:** 09-REQ-2.1
**Type:** unit
**Description:** Verifies spinner output goes to stderr, not stdout.

**Preconditions:**
- Mocked session.

**Input:**
- `assess` invocation capturing stdout and stderr separately.

**Expected:**
- stdout contains only assessment output.
- stderr contains spinner messages.
- stdout does NOT contain spinner text.

**Assertion pseudocode:**
```
ASSERT "Assessing" NOT IN captured_stdout
ASSERT "Assessing" IN captured_stderr
```

### TS-09-6: Non-TTY plain text fallback

**Requirement:** 09-REQ-2.2
**Type:** unit
**Description:** Verifies plain text output when stderr is not a TTY.

**Preconditions:**
- stderr is piped (not a TTY).

**Input:**
- `assess` invocation with piped stderr.

**Expected:**
- stderr contains phase message as plain text.
- No animation escape sequences in stderr.

**Assertion pseudocode:**
```
# CliRunner uses non-TTY by default
result = cli_runner.invoke(main, ["assess", "01"])
ASSERT "Assessing" IN captured_stderr
ASSERT "\x1b" NOT IN captured_stderr  # no ANSI escapes
```

### TS-09-7: Quiet flag accepted

**Requirement:** 09-REQ-3.1
**Type:** unit
**Description:** Verifies `--quiet` / `-q` is recognized by the CLI.

**Preconditions:** None.

**Input:**
- `spec --quiet assess 01` and `spec -q assess 01`.

**Expected:**
- Both invocations succeed (exit code 0 or expected error, not "unknown option").

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["--quiet", "assess", "01"])
ASSERT "no such option" NOT IN result.output.lower()
result2 = cli_runner.invoke(main, ["-q", "assess", "01"])
ASSERT "no such option" NOT IN result2.output.lower()
```

### TS-09-8: Quiet suppresses spinner

**Requirement:** 09-REQ-3.2
**Type:** unit
**Description:** Verifies `--quiet` suppresses all spinner output.

**Preconditions:**
- Mocked session.

**Input:**
- `spec --quiet assess 01`.

**Expected:**
- stderr does NOT contain spinner or phase messages.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["--quiet", "assess", "01"])
ASSERT "Assessing" NOT IN captured_stderr
```

### TS-09-9: Quiet preserves final output

**Requirement:** 09-REQ-3.3
**Type:** unit
**Description:** Verifies `--quiet` still prints command results.

**Preconditions:**
- Mocked session returning assessment.

**Input:**
- `spec --quiet assess 01`.

**Expected:**
- stdout contains assessment output.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["--quiet", "assess", "01"])
ASSERT result.exit_code == 0
ASSERT "quality" IN result.output.lower() OR assessment_text IN result.output
```

### TS-09-10: Quiet flag in context

**Requirement:** 09-REQ-3.4
**Type:** unit
**Description:** Verifies `--quiet` is accessible via `ctx.obj["quiet"]`.

**Preconditions:** None.

**Input:**
- Invoke CLI with `--quiet`, check context in command.

**Expected:**
- `ctx.obj["quiet"]` is `True`.

**Assertion pseudocode:**
```
# Verified by checking that quiet mode behavior is active
# (tested transitively through TS-09-8)
```

### TS-09-11: StatusSpinner context manager

**Requirement:** 09-REQ-4.1
**Type:** unit
**Description:** Verifies `StatusSpinner` works as a context manager.

**Preconditions:** None.

**Input:**
- `with StatusSpinner("Working...", quiet=False) as s: s.update("Done")`

**Expected:**
- No exceptions raised.
- `update()` method exists and is callable.

**Assertion pseudocode:**
```
with StatusSpinner("Working...", quiet=False) as s:
    s.update("Phase 2...")
    s.log("Completed phase 1")
# No exception
```

### TS-09-12: StatusSpinner quiet no-op

**Requirement:** 09-REQ-4.2
**Type:** unit
**Description:** Verifies `StatusSpinner` in quiet mode is a no-op.

**Preconditions:** None.

**Input:**
- `with StatusSpinner("Working...", quiet=True) as s: s.update("X")`

**Expected:**
- No output on stderr.
- No exceptions.

**Assertion pseudocode:**
```
with StatusSpinner("Working...", quiet=True) as s:
    s.update("Phase 2...")
    s.log("Done")
ASSERT captured_stderr == ""
```

## Edge Case Tests

### TS-09-E1: Spinner stops on error

**Requirement:** 09-REQ-1.E1
**Type:** unit
**Description:** Verifies spinner is cleaned up when command errors.

**Preconditions:**
- Mocked session that raises an error.

**Input:**
- `assess` invocation that triggers a SessionError.

**Expected:**
- Spinner is stopped.
- Error message appears on stderr.
- No orphaned spinner animation.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["assess", "01"])
ASSERT result.exit_code != 0
ASSERT "Error" IN result.output
# Spinner was cleaned up (context manager __exit__ called)
```

### TS-09-E2: Spinner stops on KeyboardInterrupt

**Requirement:** 09-REQ-1.E2
**Type:** unit
**Description:** Verifies spinner stops on Ctrl-C.

**Preconditions:**
- Mocked session that raises `KeyboardInterrupt`.

**Input:**
- `assess` invocation that triggers interrupt.

**Expected:**
- Spinner is stopped cleanly.
- No traceback from spinner cleanup.

**Assertion pseudocode:**
```
with StatusSpinner("Working...") as s:
    raise KeyboardInterrupt
# __exit__ was called, no spinner remnants
```

## Property Test Cases

### TS-09-P1: Quiet suppresses all spinner output

**Property:** Property 1 from design.md
**Validates:** 09-REQ-3.2, 09-REQ-3.3
**Type:** property
**Description:** In quiet mode, no spinner text appears on stderr.

**For any:** command in {assess, refine, generate} invoked with `--quiet`
**Invariant:** stderr is empty (no spinner text)

**Assertion pseudocode:**
```
FOR ANY cmd IN ["assess", "refine", "generate"]:
    result = invoke_with_quiet(cmd)
    ASSERT "Assessing" NOT IN stderr AND "Refining" NOT IN stderr AND "Generating" NOT IN stderr
```

### TS-09-P2: Spinner stderr only

**Property:** Property 2 from design.md
**Validates:** 09-REQ-2.1
**Type:** property
**Description:** Spinner text never appears on stdout.

**For any:** command invoked without `--quiet`
**Invariant:** stdout does not contain spinner keywords

**Assertion pseudocode:**
```
FOR ANY cmd IN ["assess", "refine", "generate"]:
    result = invoke_without_quiet(cmd)
    ASSERT "Assessing" NOT IN stdout
    ASSERT "Refining" NOT IN stdout
    ASSERT "Generating" NOT IN stdout
```

### TS-09-P3: Spinner cleanup on error

**Property:** Property 3 from design.md
**Validates:** 09-REQ-1.E1
**Type:** property
**Description:** Spinner is stopped before error output.

**For any:** command that raises an error
**Invariant:** StatusSpinner.__exit__ was called

**Assertion pseudocode:**
```
FOR ANY error_type IN [SessionError, AgentError]:
    spinner = StatusSpinner("Test")
    with spinner:
        raise error_type("test")
    # __exit__ was called (verified by mock)
```

### TS-09-P4: Non-TTY fallback

**Property:** Property 4 from design.md
**Validates:** 09-REQ-2.2
**Type:** property
**Description:** Non-TTY stderr gets plain text, no ANSI escapes.

**For any:** StatusSpinner on non-TTY stderr
**Invariant:** output contains no ANSI escape sequences

**Assertion pseudocode:**
```
# CliRunner is non-TTY by default
FOR ANY message IN ["Working...", "Phase 2..."]:
    with StatusSpinner(message) as s:
        pass
    ASSERT "\x1b" NOT IN captured_stderr
```

## Integration Smoke Tests

### TS-09-SMOKE-1: Assess with spinner end-to-end

**Execution Path:** Path 1 from design.md
**Description:** Verifies full assess flow with spinner on stderr and
assessment on stdout.

**Setup:** Mock only the agent API call. Do not mock `StatusSpinner`,
`cli.py`, or `SpecSession`.

**Trigger:** `spec --campaign-dir <dir> assess 01`

**Expected side effects:**
- stderr contains "Assessing" phase message.
- stdout contains assessment output.
- Exit code 0.

**Must NOT satisfy with:** Mocking `StatusSpinner` or `click.echo`.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["--campaign-dir", dir, "assess", "01"])
ASSERT result.exit_code == 0
ASSERT "Assessing" IN captured_stderr
ASSERT "quality" IN result.output.lower()
```

### TS-09-SMOKE-2: Quiet mode end-to-end

**Execution Path:** Path 3 from design.md
**Description:** Verifies quiet mode suppresses spinner but preserves output.

**Setup:** Mock only the agent API call.

**Trigger:** `spec --quiet --campaign-dir <dir> assess 01`

**Expected side effects:**
- stderr is empty (no spinner).
- stdout contains assessment output.
- Exit code 0.

**Must NOT satisfy with:** Mocking `StatusSpinner` or `click.echo`.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["--quiet", "--campaign-dir", dir, "assess", "01"])
ASSERT result.exit_code == 0
ASSERT captured_stderr == ""
ASSERT "quality" IN result.output.lower()
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 09-REQ-1.1 | TS-09-1 | unit |
| 09-REQ-1.2 | TS-09-2 | unit |
| 09-REQ-1.3 | TS-09-3 | unit |
| 09-REQ-1.4 | TS-09-3 | unit |
| 09-REQ-1.5 | TS-09-4 | unit |
| 09-REQ-1.E1 | TS-09-E1 | unit |
| 09-REQ-1.E2 | TS-09-E2 | unit |
| 09-REQ-2.1 | TS-09-5 | unit |
| 09-REQ-2.2 | TS-09-6 | unit |
| 09-REQ-3.1 | TS-09-7 | unit |
| 09-REQ-3.2 | TS-09-8 | unit |
| 09-REQ-3.3 | TS-09-9 | unit |
| 09-REQ-3.4 | TS-09-10 | unit |
| 09-REQ-4.1 | TS-09-11 | unit |
| 09-REQ-4.2 | TS-09-12 | unit |
| Property 1 | TS-09-P1 | property |
| Property 2 | TS-09-P2 | property |
| Property 3 | TS-09-P3 | property |
| Property 4 | TS-09-P4 | property |
| Path 1 | TS-09-SMOKE-1 | integration |
| Path 3 | TS-09-SMOKE-2 | integration |
