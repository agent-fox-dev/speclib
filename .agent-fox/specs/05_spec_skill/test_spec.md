# Test Specification: Agent CLI Skill for Spec Authoring

## Overview

Tests validate the skill file content (structure, command coverage, workflow
completeness), the `install-skill` CLI command (detection, copying, error
handling), and the correctness properties (source-target identity, package
completeness). Since the skill file is a static markdown asset, most tests
are content-inspection tests rather than behavioral tests.

## Test Cases

### TS-05-1: Skill file exists in package

**Requirement:** 05-REQ-1.1
**Type:** unit
**Description:** Verify the skill file exists at the expected package path.

**Preconditions:**
- speclib package is installed

**Input:**
- Import `SKILL_FILE_PATH` from `speclib.skill`

**Expected:**
- `SKILL_FILE_PATH` points to an existing, non-empty file

**Assertion pseudocode:**
```
from speclib.skill import SKILL_FILE_PATH
ASSERT SKILL_FILE_PATH.exists()
ASSERT SKILL_FILE_PATH.stat().st_size > 0
```

### TS-05-2: Skill file has header section

**Requirement:** 05-REQ-1.2
**Type:** unit
**Description:** Verify the skill file includes a header with name, description, and trigger conditions.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains a top-level heading with "spec"
- Contains a "Trigger" section or subsection

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text()
ASSERT "# spec" in content or "# Af-Spec" in content
ASSERT "trigger" in content.lower()
```

### TS-05-3: Skill file documents all required commands

**Requirement:** 05-REQ-1.3
**Type:** unit
**Description:** Verify the skill file mentions all required spec CLI commands.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains references to: init, new, assess, refine, accept, generate, status, validate, render

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text()
for cmd in ["spec init", "spec new", "spec assess", "spec refine",
            "spec accept", "spec generate", "spec status",
            "spec validate", "spec render"]:
    ASSERT cmd in content
```

### TS-05-4: Skill file includes command examples

**Requirement:** 05-REQ-1.4
**Type:** unit
**Description:** Verify the skill file includes at least one usage example per documented command.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content, search for code blocks containing spec commands

**Expected:**
- At least one code block example per required command

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text()
code_blocks = extract_fenced_code_blocks(content)
for cmd in ["init", "new", "assess", "refine", "accept", "generate",
            "status", "validate", "render"]:
    ASSERT any(f"spec {cmd}" in block for block in code_blocks)
```

### TS-05-5: Skill file is valid markdown

**Requirement:** 05-REQ-1.5
**Type:** unit
**Description:** Verify the skill file can be parsed as valid markdown.

**Preconditions:**
- Skill file exists

**Input:**
- Read and parse skill file

**Expected:**
- No unclosed fenced code blocks
- All headings use proper markdown syntax

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text()
fence_count = content.count("```")
ASSERT fence_count % 2 == 0  # all code fences closed
```

### TS-05-6: Interactive workflow described

**Requirement:** 05-REQ-2.1
**Type:** unit
**Description:** Verify the skill file describes the interactive workflow steps.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains a section about interactive workflow
- Mentions campaign creation, spec creation, assess, refine, accept, generate steps

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "interactive" in content
ASSERT "campaign" in content
ASSERT "assess" in content
ASSERT "refine" in content
ASSERT "accept" in content
ASSERT "generate" in content
```

### TS-05-7: Assessment presentation instructions

**Requirement:** 05-REQ-2.2
**Type:** unit
**Description:** Verify the skill file instructs the agent to present assessment results to the user.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about presenting assessment output to the user

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "present" in content and "assessment" in content
```

### TS-05-8: Accept-or-refine decision instructions

**Requirement:** 05-REQ-2.3
**Type:** unit
**Description:** Verify the skill file instructs the agent to ask the user whether to accept or continue refining.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about asking the user to accept or continue refining

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "accept" in content and "refin" in content
ASSERT "ask" in content or "prompt" in content or "user" in content
```

### TS-05-9: One-shot workflow described

**Requirement:** 05-REQ-3.1
**Type:** unit
**Description:** Verify the skill file describes the one-shot workflow.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains a section about one-shot mode
- Mentions `--one-shot` flag

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text()
ASSERT "--one-shot" in content
```

### TS-05-10: One-shot result presentation

**Requirement:** 05-REQ-3.2
**Type:** unit
**Description:** Verify the skill file instructs the agent to present the generated spec after one-shot mode.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about presenting the result after one-shot generation

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "one-shot" in content or "one_shot" in content
ASSERT "review" in content or "present" in content
```

### TS-05-11: Question ID parsing instructions

**Requirement:** 05-REQ-4.1
**Type:** unit
**Description:** Verify the skill file instructs the agent to parse question IDs from assess output.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about parsing or extracting question IDs

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "question" in content and "id" in content
```

### TS-05-12: Natural language question presentation

**Requirement:** 05-REQ-4.2
**Type:** unit
**Description:** Verify the skill file instructs the agent to present questions naturally.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about presenting questions in natural language

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "natural" in content or "conversational" in content
ASSERT "question" in content
```

### TS-05-13: Answer mapping to Question IDs

**Requirement:** 05-REQ-4.3, 05-REQ-4.4
**Type:** unit
**Description:** Verify the skill file instructs the agent to map user answers to Question IDs and pass them to refine.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about mapping answers to question IDs
- Mentions `--answers` flag and JSON format

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text()
ASSERT "--answers" in content
ASSERT "JSON" in content or "json" in content
```

### TS-05-14: install-skill detects agent CLI

**Requirement:** 05-REQ-5.1
**Type:** unit
**Description:** Verify detect_agent_cli finds Claude Code and Gemini CLI directories.

**Preconditions:**
- Temp home directory with `~/.claude/` present

**Input:**
- Call detect_agent_cli() with patched home

**Expected:**
- Returns "claude"

**Assertion pseudocode:**
```
with patched_home(tmp_path):
    (tmp_path / ".claude").mkdir()
    result = detect_agent_cli()
    ASSERT result == "claude"
```

### TS-05-15: install-skill copies file to detected location

**Requirement:** 05-REQ-5.2
**Type:** unit
**Description:** Verify install-skill copies the skill file to the agent's skill directory.

**Preconditions:**
- Temp home directory with `~/.claude/` present

**Input:**
- Run `spec install-skill` with Click test runner and patched home

**Expected:**
- Exit code 0
- `~/.claude/skills/spec.md` exists and matches source content

**Assertion pseudocode:**
```
with patched_home(tmp_path):
    (tmp_path / ".claude").mkdir()
    result = cli_runner.invoke(cli, ["install-skill"])
    ASSERT result.exit_code == 0
    installed = tmp_path / ".claude" / "skills" / "spec.md"
    ASSERT installed.exists()
    ASSERT installed.read_text() == SKILL_FILE_PATH.read_text()
```

### TS-05-16: install-skill with --target flag

**Requirement:** 05-REQ-5.3
**Type:** unit
**Description:** Verify install-skill uses explicit --target to determine destination.

**Preconditions:**
- Temp home directory (no agent CLI directories needed)

**Input:**
- Run `spec install-skill --target claude` with Click test runner

**Expected:**
- Exit code 0
- `~/.claude/skills/spec.md` created

**Assertion pseudocode:**
```
with patched_home(tmp_path):
    result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
    ASSERT result.exit_code == 0
    ASSERT (tmp_path / ".claude" / "skills" / "spec.md").exists()
```

### TS-05-17: install-skill overwrites existing file

**Requirement:** 05-REQ-5.4
**Type:** unit
**Description:** Verify install-skill overwrites an existing skill file.

**Preconditions:**
- Temp home directory with existing `~/.claude/skills/spec.md` containing "old content"

**Input:**
- Run `spec install-skill --target claude`

**Expected:**
- Exit code 0
- File content replaced with current skill file content
- Output contains "updated" or similar message

**Assertion pseudocode:**
```
with patched_home(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "spec.md").write_text("old content")
    result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
    ASSERT result.exit_code == 0
    ASSERT (skill_dir / "spec.md").read_text() == SKILL_FILE_PATH.read_text()
    ASSERT "updated" in result.output.lower() or "installed" in result.output.lower()
```

### TS-05-18: install-skill prints success message

**Requirement:** 05-REQ-5.5
**Type:** unit
**Description:** Verify install-skill prints the installed file path on success.

**Preconditions:**
- Temp home directory

**Input:**
- Run `spec install-skill --target claude`

**Expected:**
- Output contains the installed file path

**Assertion pseudocode:**
```
with patched_home(tmp_path):
    result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
    ASSERT result.exit_code == 0
    ASSERT ".claude/skills/spec.md" in result.output
```

### TS-05-19: Error handling section in skill file

**Requirement:** 05-REQ-6.1
**Type:** unit
**Description:** Verify the skill file includes an error handling section.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains a section titled "Error Handling" or similar

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "error handling" in content or "error" in content and "handling" in content
```

### TS-05-20: Exit code checking instructions

**Requirement:** 05-REQ-6.2
**Type:** unit
**Description:** Verify the skill file instructs the agent to check exit codes.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about checking exit codes or command success

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "exit code" in content or "exit status" in content or "failed" in content
```

### TS-05-21: Status check before operations

**Requirement:** 05-REQ-6.3
**Type:** unit
**Description:** Verify the skill file instructs the agent to check session state before operations.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about using `spec status` to check state

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text()
ASSERT "spec status" in content
ASSERT "state" in content.lower() or "status" in content.lower()
```

## Edge Case Tests

### TS-05-E1: No agent CLI detected without --target

**Requirement:** 05-REQ-5.E1
**Type:** unit
**Description:** Verify install-skill errors when no agent CLI is detected and no --target given.

**Preconditions:**
- Temp home directory with no agent CLI directories

**Input:**
- Run `spec install-skill` with Click test runner

**Expected:**
- Non-zero exit code
- Output lists supported agent CLIs

**Assertion pseudocode:**
```
with patched_home(tmp_path):
    result = cli_runner.invoke(cli, ["install-skill"])
    ASSERT result.exit_code != 0
    ASSERT "claude" in result.output.lower()
    ASSERT "gemini" in result.output.lower()
```

### TS-05-E2: Target skill directory created if missing

**Requirement:** 05-REQ-5.E2
**Type:** unit
**Description:** Verify install-skill creates the skill directory if it does not exist.

**Preconditions:**
- Temp home directory with `~/.claude/` but no `~/.claude/skills/`

**Input:**
- Run `spec install-skill --target claude`

**Expected:**
- `~/.claude/skills/` directory created
- Skill file installed successfully

**Assertion pseudocode:**
```
with patched_home(tmp_path):
    (tmp_path / ".claude").mkdir()
    result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
    ASSERT result.exit_code == 0
    ASSERT (tmp_path / ".claude" / "skills").is_dir()
    ASSERT (tmp_path / ".claude" / "skills" / "spec.md").exists()
```

### TS-05-E3: Missing source file raises SpeclibError

**Requirement:** 05-REQ-5.E3
**Type:** unit
**Description:** Verify install-skill raises SpeclibError if the source file is missing.

**Preconditions:**
- SKILL_FILE_PATH patched to a non-existent path

**Input:**
- Run `spec install-skill --target claude`

**Expected:**
- SpeclibError raised (or non-zero exit with error message)

**Assertion pseudocode:**
```
with patched_skill_path(Path("/nonexistent/spec.md")):
    result = cli_runner.invoke(cli, ["install-skill", "--target", "claude"])
    ASSERT result.exit_code != 0
    ASSERT "missing" in result.output.lower() or "not found" in result.output.lower()
```

### TS-05-E4: Zero questions in assessment

**Requirement:** 05-REQ-2.E1
**Type:** unit
**Description:** Verify the skill file instructs the agent to proceed to accept when no questions exist.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions for the zero-questions case

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "no question" in content or "zero question" in content or "no remaining" in content
```

### TS-05-E5: One-shot failure fallback

**Requirement:** 05-REQ-3.E1
**Type:** unit
**Description:** Verify the skill file instructs the agent to suggest interactive mode on one-shot failure.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about falling back to interactive mode on one-shot failure

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "interactive" in content
ASSERT "fail" in content or "error" in content
```

### TS-05-E6: spec not on PATH

**Requirement:** 05-REQ-6.E1
**Type:** unit
**Description:** Verify the skill file instructs the agent to tell the user to install speclib.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about installing speclib when spec is not found

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "install" in content and "speclib" in content
```

### TS-05-E7: Unsupported command handling

**Requirement:** 05-REQ-1.E1
**Type:** unit
**Description:** Verify the skill file instructs the agent to report unsupported commands to the user rather than failing silently.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about reporting unsupported or unavailable commands to the user

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "unsupported" in content or "not supported" in content or "not available" in content
ASSERT "report" in content or "inform" in content or "tell" in content
```

### TS-05-E8: Ambiguous answer clarification

**Requirement:** 05-REQ-4.E1
**Type:** unit
**Description:** Verify the skill file instructs the agent to ask for clarification when an answer cannot be mapped to a question.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about asking for clarification when an answer is ambiguous

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "clarif" in content  # matches clarify, clarification
ASSERT "map" in content or "match" in content or "which question" in content
```

### TS-05-E9: Partial answers handling

**Requirement:** 05-REQ-4.E2
**Type:** unit
**Description:** Verify the skill file instructs the agent to pass partial answers to refine and note unanswered questions.

**Preconditions:**
- Skill file exists

**Input:**
- Read skill file content

**Expected:**
- Contains instructions about handling partial answers and noting unanswered questions

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text().lower()
ASSERT "partial" in content or "some question" in content or "unanswered" in content
```

## Property Test Cases

### TS-05-P1: Skill file is package-complete

**Property:** Property 1 from design.md
**Validates:** 05-REQ-1.1
**Type:** property
**Description:** The skill file at SKILL_FILE_PATH always exists and is non-empty.

**For any:** import of speclib.skill
**Invariant:** SKILL_FILE_PATH.exists() and SKILL_FILE_PATH.stat().st_size > 0

**Assertion pseudocode:**
```
from speclib.skill import SKILL_FILE_PATH
ASSERT SKILL_FILE_PATH.exists()
ASSERT SKILL_FILE_PATH.stat().st_size > 0
```

### TS-05-P2: Installed file matches source

**Property:** Property 2 from design.md
**Validates:** 05-REQ-5.2, 05-REQ-5.4
**Type:** property
**Description:** After install-skill, the installed file is byte-identical to the source.

**For any:** target in {"claude", "gemini"}
**Invariant:** installed_content == source_content

**Assertion pseudocode:**
```
FOR ANY target IN ["claude", "gemini"]:
    with patched_home(tmp_path):
        cli_runner.invoke(cli, ["install-skill", "--target", target])
        target_dirs = {"claude": ".claude/skills", "gemini": ".gemini/skills"}
        installed = tmp_path / target_dirs[target] / "spec.md"
        ASSERT installed.read_bytes() == SKILL_FILE_PATH.read_bytes()
```

### TS-05-P3: All required commands documented

**Property:** Property 3 from design.md
**Validates:** 05-REQ-1.3, 05-REQ-1.4
**Type:** property
**Description:** Every required CLI command appears in the skill file.

**For any:** command in {init, new, assess, refine, accept, generate, status, validate, render}
**Invariant:** `spec {command}` appears in the skill file content

**Assertion pseudocode:**
```
content = SKILL_FILE_PATH.read_text()
required_commands = ["init", "new", "assess", "refine", "accept",
                     "generate", "status", "validate", "render"]
FOR ANY cmd IN required_commands:
    ASSERT f"spec {cmd}" in content
```

## Integration Smoke Tests

### TS-05-SMOKE-1: Full install-skill flow

**Execution Path:** Path 3 from design.md
**Description:** End-to-end skill installation from package source to agent CLI directory.

**Setup:** Temp home directory with `~/.claude/` present.

**Trigger:** Run `spec install-skill`.

**Expected side effects:**
- `~/.claude/skills/spec.md` exists with content matching source
- Success message printed with file path

**Must NOT satisfy with:** Mocking the copy operation.

**Assertion pseudocode:**
```
with patched_home(tmp_path):
    (tmp_path / ".claude").mkdir()
    result = cli_runner.invoke(cli, ["install-skill"])
    ASSERT result.exit_code == 0
    installed = tmp_path / ".claude" / "skills" / "spec.md"
    ASSERT installed.exists()
    ASSERT installed.read_bytes() == SKILL_FILE_PATH.read_bytes()
    ASSERT str(installed) in result.output or ".claude/skills/spec.md" in result.output
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 05-REQ-1.1 | TS-05-1 | unit |
| 05-REQ-1.2 | TS-05-2 | unit |
| 05-REQ-1.3 | TS-05-3 | unit |
| 05-REQ-1.4 | TS-05-4 | unit |
| 05-REQ-1.5 | TS-05-5 | unit |
| 05-REQ-2.1 | TS-05-6 | unit |
| 05-REQ-2.2 | TS-05-7 | unit |
| 05-REQ-2.3 | TS-05-8 | unit |
| 05-REQ-3.1 | TS-05-9 | unit |
| 05-REQ-3.2 | TS-05-10 | unit |
| 05-REQ-4.1 | TS-05-11 | unit |
| 05-REQ-4.2 | TS-05-12 | unit |
| 05-REQ-4.3 | TS-05-13 | unit |
| 05-REQ-4.4 | TS-05-13 | unit |
| 05-REQ-5.1 | TS-05-14 | unit |
| 05-REQ-5.2 | TS-05-15 | unit |
| 05-REQ-5.3 | TS-05-16 | unit |
| 05-REQ-5.4 | TS-05-17 | unit |
| 05-REQ-5.5 | TS-05-18 | unit |
| 05-REQ-6.1 | TS-05-19 | unit |
| 05-REQ-6.2 | TS-05-20 | unit |
| 05-REQ-6.3 | TS-05-21 | unit |
| 05-REQ-1.E1 | TS-05-E7 | unit |
| 05-REQ-2.E1 | TS-05-E4 | unit |
| 05-REQ-3.E1 | TS-05-E5 | unit |
| 05-REQ-4.E1 | TS-05-E8 | unit |
| 05-REQ-4.E2 | TS-05-E9 | unit |
| 05-REQ-5.E1 | TS-05-E1 | unit |
| 05-REQ-5.E2 | TS-05-E2 | unit |
| 05-REQ-5.E3 | TS-05-E3 | unit |
| 05-REQ-6.E1 | TS-05-E6 | unit |
| Property 1 | TS-05-P1 | property |
| Property 2 | TS-05-P2 | property |
| Property 3 | TS-05-P3 | property |
| Path 3 | TS-05-SMOKE-1 | integration |
