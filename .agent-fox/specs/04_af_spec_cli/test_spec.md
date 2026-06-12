# Test Specification: spec CLI

## Overview

Tests validate the spec CLI commands using Click's CliRunner for isolated
command invocation. Business logic (Campaign, SpecSession) is mocked in unit
tests and used directly in integration tests. Test cases map 1:1 to
requirements; property tests verify resolution and error invariants.

## Test Cases

### TS-04-1: Init creates campaign directory

**Requirement:** 04-REQ-1.1
**Type:** unit
**Description:** Verify `spec init` calls Campaign.create and prints confirmation.

**Preconditions:**
- Temp directory exists for target path
- Campaign.create is mocked

**Input:**
- Invoke `spec init /tmp/test-campaign --name "Test" --description "A test"`

**Expected:**
- Campaign.create called with (path, "Test", "A test")
- Output contains the absolute path
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.create:
    result = runner.invoke(main, ["init", str(tmp_path), "--name", "Test", "--description", "A test"])
    ASSERT result.exit_code == 0
    ASSERT str(tmp_path) in result.output
    ASSERT Campaign.create.called_once_with(tmp_path, "Test", "A test")
```

### TS-04-2: Init defaults name to directory basename

**Requirement:** 04-REQ-1.2
**Type:** unit
**Description:** Verify init uses directory basename when --name is omitted.

**Preconditions:**
- Temp directory named "my-project"

**Input:**
- Invoke `spec init /tmp/my-project`

**Expected:**
- Campaign.create called with name="my-project"

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.create:
    result = runner.invoke(main, ["init", "/tmp/my-project"])
    ASSERT Campaign.create.call_args[1]["name"] == "my-project" or
           Campaign.create.call_args[0][1] == "my-project"
```

### TS-04-3: Init defaults description to empty string

**Requirement:** 04-REQ-1.3
**Type:** unit
**Description:** Verify init uses empty description when --description is omitted.

**Preconditions:**
- Temp directory

**Input:**
- Invoke `spec init /tmp/test --name "Test"`

**Expected:**
- Campaign.create called with description=""

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.create:
    result = runner.invoke(main, ["init", str(tmp_path), "--name", "Test"])
    ASSERT Campaign.create.call_args includes description=""
```

### TS-04-4: Init handles CampaignError

**Requirement:** 04-REQ-1.4
**Type:** unit
**Description:** Verify init prints error and exits 1 when Campaign.create fails.

**Preconditions:**
- Campaign.create mocked to raise CampaignError("already exists")

**Input:**
- Invoke `spec init /tmp/existing`

**Expected:**
- Error message printed to stderr
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.create raising CampaignError("already exists"):
    result = runner.invoke(main, ["init", "/tmp/existing"])
    ASSERT result.exit_code == 1
    ASSERT "already exists" in result.output
```

### TS-04-5: Init resolves relative path

**Requirement:** 04-REQ-1.E1
**Type:** unit
**Description:** Verify init resolves a relative path to absolute.

**Preconditions:**
- CWD is /tmp

**Input:**
- Invoke `spec init ./my-campaign --name "Test"`

**Expected:**
- Campaign.create called with an absolute path

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.create:
    result = runner.invoke(main, ["init", "./my-campaign", "--name", "Test"])
    ASSERT Path(Campaign.create.call_args[0][0]).is_absolute()
```

### TS-04-6: List displays spec table

**Requirement:** 04-REQ-2.1
**Type:** unit
**Description:** Verify list displays a table with spec number, name, state, artifacts.

**Preconditions:**
- Campaign with two specs, mocked sessions in different states

**Input:**
- Invoke `spec list` from campaign directory

**Expected:**
- Output contains table with columns for number, name, state, artifacts
- Both specs appear in output

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.open returning campaign with specs:
    result = runner.invoke(main, ["list"])
    ASSERT result.exit_code == 0
    ASSERT "01" in result.output
    ASSERT "data_models" in result.output
    ASSERT "generated" in result.output or state_name in result.output
```

### TS-04-7: List with explicit directory

**Requirement:** 04-REQ-2.2
**Type:** unit
**Description:** Verify list accepts explicit campaign directory argument.

**Preconditions:**
- Campaign directory at a known path

**Input:**
- Invoke `spec list /path/to/campaign`

**Expected:**
- Campaign.open called with the provided path
- Table output produced

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.open:
    result = runner.invoke(main, ["list", str(campaign_dir)])
    ASSERT result.exit_code == 0
    ASSERT Campaign.open.called_with(campaign_dir)
```

### TS-04-8: List empty campaign

**Requirement:** 04-REQ-2.3
**Type:** unit
**Description:** Verify list prints empty message for campaign with no specs.

**Preconditions:**
- Campaign with no spec subdirectories

**Input:**
- Invoke `spec list`

**Expected:**
- Output indicates campaign is empty
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign returning empty specs list:
    result = runner.invoke(main, ["list"])
    ASSERT result.exit_code == 0
    ASSERT "empty" in result.output.lower() or "no specs" in result.output.lower()
```

### TS-04-9: List sorts by numeric prefix

**Requirement:** 04-REQ-2.4
**Type:** unit
**Description:** Verify specs are sorted by number in list output.

**Preconditions:**
- Campaign with specs 03, 01, 02 (out of order internally)

**Input:**
- Invoke `spec list`

**Expected:**
- Output shows specs in order: 01, 02, 03

**Assertion pseudocode:**
```
runner = CliRunner()
result = runner.invoke(main, ["list"])
pos_01 = result.output.index("01")
pos_02 = result.output.index("02")
pos_03 = result.output.index("03")
ASSERT pos_01 < pos_02 < pos_03
```

### TS-04-10: List error on non-campaign directory

**Requirement:** 04-REQ-2.E1
**Type:** unit
**Description:** Verify list fails with clear error when not in a campaign dir.

**Preconditions:**
- CWD is a directory without campaign.yaml

**Input:**
- Invoke `spec list`

**Expected:**
- Error message about campaign directory
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.open raising CampaignError:
    result = runner.invoke(main, ["list"])
    ASSERT result.exit_code == 1
    ASSERT "campaign" in result.output.lower()
```

### TS-04-11: New creates spec from PRD file

**Requirement:** 04-REQ-3.1
**Type:** unit
**Description:** Verify new calls campaign.new_spec and prints created directory.

**Preconditions:**
- Campaign directory exists
- PRD file exists at given path

**Input:**
- Invoke `spec new /path/to/prd.md`

**Expected:**
- campaign.new_spec called with PRD content
- Output contains created spec directory name
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock campaign.new_spec returning session:
    result = runner.invoke(main, ["new", str(prd_path)])
    ASSERT result.exit_code == 0
    ASSERT campaign.new_spec.called
    ASSERT "01_" in result.output or spec_name in result.output
```

### TS-04-12: New with explicit name

**Requirement:** 04-REQ-3.2
**Type:** unit
**Description:** Verify --name option is passed as spec name.

**Preconditions:**
- Campaign and PRD file exist

**Input:**
- Invoke `spec new prd.md --name my_spec`

**Expected:**
- campaign.new_spec called with name="my_spec"

**Assertion pseudocode:**
```
runner = CliRunner()
with mock campaign.new_spec:
    result = runner.invoke(main, ["new", str(prd_path), "--name", "my_spec"])
    ASSERT "my_spec" in str(campaign.new_spec.call_args)
```

### TS-04-13: New derives name from filename

**Requirement:** 04-REQ-3.2
**Type:** unit
**Description:** Verify name is derived from PRD filename when --name is omitted.

**Preconditions:**
- PRD file named "My Data Models.md"

**Input:**
- Invoke `spec new "My Data Models.md"`

**Expected:**
- Derived name is "my_data_models"

**Assertion pseudocode:**
```
runner = CliRunner()
with mock campaign.new_spec:
    result = runner.invoke(main, ["new", "My Data Models.md"])
    ASSERT "my_data_models" in str(campaign.new_spec.call_args)
```

### TS-04-14: New with one-shot flag

**Requirement:** 04-REQ-3.3
**Type:** unit
**Description:** Verify --one-shot sets session mode.

**Preconditions:**
- Campaign and PRD file exist

**Input:**
- Invoke `spec new prd.md --one-shot`

**Expected:**
- campaign.new_spec called with mode="one-shot"

**Assertion pseudocode:**
```
runner = CliRunner()
with mock campaign.new_spec:
    result = runner.invoke(main, ["new", str(prd_path), "--one-shot"])
    ASSERT "one-shot" in str(campaign.new_spec.call_args) or
           campaign.new_spec.call_args includes mode="one-shot"
```

### TS-04-15: New with missing PRD file

**Requirement:** 04-REQ-3.4
**Type:** unit
**Description:** Verify error when PRD file does not exist.

**Preconditions:**
- PRD file path points to non-existent file

**Input:**
- Invoke `spec new /tmp/nonexistent.md`

**Expected:**
- Error message about missing file
- Exit code 1 (or Click's built-in exit code 2 for bad parameter)

**Assertion pseudocode:**
```
runner = CliRunner()
result = runner.invoke(main, ["new", "/tmp/nonexistent.md"])
ASSERT result.exit_code != 0
```

### TS-04-16: New with invalid spec name

**Requirement:** 04-REQ-3.E1
**Type:** unit
**Description:** Verify error when spec name contains invalid characters.

**Preconditions:**
- Campaign and PRD file exist

**Input:**
- Invoke `spec new prd.md --name "Invalid Name!"`

**Expected:**
- Error about naming rules
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock campaign.new_spec raising CampaignError("invalid name"):
    result = runner.invoke(main, ["new", str(prd_path), "--name", "Invalid Name!"])
    ASSERT result.exit_code == 1
```

### TS-04-17: Assess runs assessment and prints summary

**Requirement:** 04-REQ-4.1
**Type:** unit
**Description:** Verify assess calls session.assess and prints formatted summary.

**Preconditions:**
- Campaign with spec in init state
- session.assess mocked to return assessment result

**Input:**
- Invoke `spec assess 01`

**Expected:**
- session.assess called
- Output contains quality score, gaps, questions
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.assess returning assessment:
    result = runner.invoke(main, ["assess", "01"])
    ASSERT result.exit_code == 0
    ASSERT "quality" in result.output.lower() or "score" in result.output.lower()
```

### TS-04-18: Assess output formatting

**Requirement:** 04-REQ-4.2
**Type:** unit
**Description:** Verify assessment output has clear section headers.

**Preconditions:**
- Mocked assessment with quality, gaps, and questions

**Input:**
- Invoke `spec assess 01`

**Expected:**
- Output contains section headers for quality, gaps, questions

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.assess returning full assessment:
    result = runner.invoke(main, ["assess", "01"])
    ASSERT "Quality" in result.output or "quality" in result.output
    ASSERT "Gaps" in result.output or "gaps" in result.output
    ASSERT "Questions" in result.output or "questions" in result.output
```

### TS-04-19: Assess wrong state error

**Requirement:** 04-REQ-4.3
**Type:** unit
**Description:** Verify assess prints state error when session is not in init or refining.

**Preconditions:**
- Session in generated state

**Input:**
- Invoke `spec assess 01`

**Expected:**
- Error about current state
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.assess raising SessionError("wrong state"):
    result = runner.invoke(main, ["assess", "01"])
    ASSERT result.exit_code == 1
    ASSERT "state" in result.output.lower()
```

### TS-04-20: Assess agent error

**Requirement:** 04-REQ-4.E1
**Type:** unit
**Description:** Verify assess exits 2 on agent pipeline error.

**Preconditions:**
- session.assess raises unexpected exception

**Input:**
- Invoke `spec assess 01`

**Expected:**
- Error to stderr
- Exit code 2

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.assess raising RuntimeError("agent failed"):
    result = runner.invoke(main, ["assess", "01"])
    ASSERT result.exit_code == 2
```

### TS-04-21: Refine submits answers and prints update

**Requirement:** 04-REQ-5.1
**Type:** unit
**Description:** Verify refine reads JSON, calls session.refine, prints confirmation.

**Preconditions:**
- Session in refining state
- Answers JSON file exists with valid content

**Input:**
- Invoke `spec refine 01 --answers answers.json`

**Expected:**
- session.refine called with parsed answers
- Confirmation printed
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with temp file "answers.json" = '{"q1": "answer1"}':
    with mock session.refine:
        result = runner.invoke(main, ["refine", "01", "--answers", str(answers_path)])
        ASSERT result.exit_code == 0
        ASSERT session.refine.called
```

### TS-04-22: Refine with missing answers file

**Requirement:** 04-REQ-5.2
**Type:** unit
**Description:** Verify refine fails when answers file does not exist.

**Preconditions:**
- No file at given path

**Input:**
- Invoke `spec refine 01 --answers /tmp/nonexistent.json`

**Expected:**
- Error message
- Exit code 1 (or Click's bad parameter exit code)

**Assertion pseudocode:**
```
runner = CliRunner()
result = runner.invoke(main, ["refine", "01", "--answers", "/tmp/nonexistent.json"])
ASSERT result.exit_code != 0
```

### TS-04-23: Refine with invalid JSON

**Requirement:** 04-REQ-5.3
**Type:** unit
**Description:** Verify refine fails on malformed JSON.

**Preconditions:**
- Answers file contains invalid JSON

**Input:**
- Invoke `spec refine 01 --answers bad.json`

**Expected:**
- Parse error message
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with temp file "bad.json" = "{not valid json":
    result = runner.invoke(main, ["refine", "01", "--answers", str(bad_path)])
    ASSERT result.exit_code == 1
    ASSERT "json" in result.output.lower() or "parse" in result.output.lower()
```

### TS-04-24: Refine wrong state error

**Requirement:** 04-REQ-5.4
**Type:** unit
**Description:** Verify refine prints state error when not in refining state.

**Preconditions:**
- Session in init state

**Input:**
- Invoke `spec refine 01 --answers answers.json`

**Expected:**
- Error about required state
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.refine raising SessionError("not in refining state"):
    result = runner.invoke(main, ["refine", "01", "--answers", str(answers_path)])
    ASSERT result.exit_code == 1
    ASSERT "state" in result.output.lower()
```

### TS-04-25: Refine prints updated assessment

**Requirement:** 04-REQ-5.5
**Type:** unit
**Description:** Verify refine prints updated assessment summary after success.

**Preconditions:**
- session.refine returns updated assessment

**Input:**
- Invoke `spec refine 01 --answers answers.json`

**Expected:**
- Output contains assessment summary (quality, gaps, questions)

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.refine returning assessment:
    result = runner.invoke(main, ["refine", "01", "--answers", str(answers_path)])
    ASSERT result.exit_code == 0
    ASSERT "quality" in result.output.lower() or "score" in result.output.lower()
```

### TS-04-26: Refine invalid answers schema

**Requirement:** 04-REQ-5.E1
**Type:** unit
**Description:** Verify refine fails when JSON is not an object mapping question IDs to strings.

**Preconditions:**
- Answers file contains valid JSON but wrong structure (e.g., a list)

**Input:**
- Invoke `spec refine 01 --answers bad_schema.json`

**Expected:**
- Schema validation error
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with temp file "bad_schema.json" = '["not", "an", "object"]':
    result = runner.invoke(main, ["refine", "01", "--answers", str(bad_path)])
    ASSERT result.exit_code == 1
```

### TS-04-27: Accept transitions state and prints confirmation

**Requirement:** 04-REQ-6.1
**Type:** unit
**Description:** Verify accept calls session.accept_prd and prints new state.

**Preconditions:**
- Session in assessing or refining state

**Input:**
- Invoke `spec accept 01`

**Expected:**
- session.accept_prd called
- Output contains "prd_accepted" or similar state name
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.accept_prd:
    result = runner.invoke(main, ["accept", "01"])
    ASSERT result.exit_code == 0
    ASSERT "accepted" in result.output.lower()
```

### TS-04-28: Accept wrong state error

**Requirement:** 04-REQ-6.2
**Type:** unit
**Description:** Verify accept fails when session is not in assessing or refining state.

**Preconditions:**
- Session in init state

**Input:**
- Invoke `spec accept 01`

**Expected:**
- Error about current state
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.accept_prd raising SessionError:
    result = runner.invoke(main, ["accept", "01"])
    ASSERT result.exit_code == 1
    ASSERT "state" in result.output.lower()
```

### TS-04-29: Generate runs generation and prints summary

**Requirement:** 04-REQ-7.1, 04-REQ-7.2
**Type:** unit
**Description:** Verify generate calls session.generate and prints artifact summary.

**Preconditions:**
- Session in prd_accepted state
- session.generate mocked to return artifact list

**Input:**
- Invoke `spec generate 01`

**Expected:**
- session.generate called
- Output lists generated artifacts
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.generate returning ["requirements.md", "design.md", "test_spec.md", "tasks.md"]:
    result = runner.invoke(main, ["generate", "01"])
    ASSERT result.exit_code == 0
    ASSERT "requirements" in result.output.lower()
```

### TS-04-30: Generate wrong state error

**Requirement:** 04-REQ-7.3
**Type:** unit
**Description:** Verify generate fails when session is not in prd_accepted state.

**Preconditions:**
- Session in init state

**Input:**
- Invoke `spec generate 01`

**Expected:**
- Error about accepting PRD first
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session raising SessionError("not in prd_accepted"):
    result = runner.invoke(main, ["generate", "01"])
    ASSERT result.exit_code == 1
    ASSERT "accept" in result.output.lower() or "state" in result.output.lower()
```

### TS-04-31: Generate agent error

**Requirement:** 04-REQ-7.E1
**Type:** unit
**Description:** Verify generate exits 2 on agent pipeline error.

**Preconditions:**
- session.generate raises unexpected exception

**Input:**
- Invoke `spec generate 01`

**Expected:**
- Error to stderr
- Exit code 2

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.generate raising RuntimeError("agent failed"):
    result = runner.invoke(main, ["generate", "01"])
    ASSERT result.exit_code == 2
```

### TS-04-32: Validate with passing spec

**Requirement:** 04-REQ-8.1, 04-REQ-8.2
**Type:** unit
**Description:** Verify validate prints success when no errors found.

**Preconditions:**
- Session with all artifacts, validation returns no errors

**Input:**
- Invoke `spec validate 01`

**Expected:**
- Success message
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.validate returning ValidationResult(valid=True, errors=[]):
    result = runner.invoke(main, ["validate", "01"])
    ASSERT result.exit_code == 0
    ASSERT "valid" in result.output.lower() or "success" in result.output.lower() or "pass" in result.output.lower()
```

### TS-04-33: Validate with errors

**Requirement:** 04-REQ-8.3, 04-REQ-8.4
**Type:** unit
**Description:** Verify validate prints error table and exits 1 when errors found.

**Preconditions:**
- Validation returns errors

**Input:**
- Invoke `spec validate 01`

**Expected:**
- Error table with file, path, message columns
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.validate returning errors:
    result = runner.invoke(main, ["validate", "01"])
    ASSERT result.exit_code == 1
    ASSERT "requirements.md" in result.output
    ASSERT "Missing" in result.output or error_message in result.output
```

### TS-04-34: Validate with missing artifacts

**Requirement:** 04-REQ-8.E1
**Type:** unit
**Description:** Verify validate reports missing artifacts.

**Preconditions:**
- Session raises SessionError about missing artifacts

**Input:**
- Invoke `spec validate 01`

**Expected:**
- Error listing missing artifacts
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.validate raising SessionError("missing artifacts"):
    result = runner.invoke(main, ["validate", "01"])
    ASSERT result.exit_code == 1
    ASSERT "missing" in result.output.lower()
```

### TS-04-35: Render outputs markdown

**Requirement:** 04-REQ-9.1
**Type:** unit
**Description:** Verify render prints markdown to stdout.

**Preconditions:**
- Session with all artifacts, render returns markdown string

**Input:**
- Invoke `spec render 01`

**Expected:**
- Markdown content on stdout
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.render returning "# Spec Title\n\n## Requirements\n...":
    result = runner.invoke(main, ["render", "01"])
    ASSERT result.exit_code == 0
    ASSERT "# " in result.output
```

### TS-04-36: Render with --combined flag

**Requirement:** 04-REQ-9.2
**Type:** unit
**Description:** Verify render passes combined=True when flag is set.

**Preconditions:**
- Session with all artifacts

**Input:**
- Invoke `spec render 01 --combined`

**Expected:**
- session.render called with combined=True

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.render:
    result = runner.invoke(main, ["render", "01", "--combined"])
    ASSERT session.render.called_with(combined=True)
```

### TS-04-37: Render without --combined flag

**Requirement:** 04-REQ-9.3
**Type:** unit
**Description:** Verify render calls session.render(combined=False) by default.

**Preconditions:**
- Session with all artifacts

**Input:**
- Invoke `spec render 01`

**Expected:**
- session.render called with combined=False
- Each artifact's markdown printed with separator

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.render(combined=False) returning dict:
    result = runner.invoke(main, ["render", "01"])
    ASSERT session.render.called_with(combined=False)
```

### TS-04-38: Render with missing artifacts

**Requirement:** 04-REQ-9.E1
**Type:** unit
**Description:** Verify render reports missing artifacts.

**Preconditions:**
- Session raises SessionError about missing artifacts

**Input:**
- Invoke `spec render 01`

**Expected:**
- Error listing missing artifacts
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.render raising SessionError("missing artifacts"):
    result = runner.invoke(main, ["render", "01"])
    ASSERT result.exit_code == 1
    ASSERT "missing" in result.output.lower()
```

### TS-04-39: Status without spec shows all specs

**Requirement:** 04-REQ-10.1
**Type:** unit
**Description:** Verify status without argument shows table of all specs.

**Preconditions:**
- Campaign with multiple specs

**Input:**
- Invoke `spec status`

**Expected:**
- Table showing all specs with their states
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock campaign with specs:
    result = runner.invoke(main, ["status"])
    ASSERT result.exit_code == 0
    ASSERT "01" in result.output
    ASSERT "02" in result.output
```

### TS-04-40: Status with spec shows detail

**Requirement:** 04-REQ-10.2
**Type:** unit
**Description:** Verify status with spec shows detailed session state.

**Preconditions:**
- Campaign with spec 01

**Input:**
- Invoke `spec status 01`

**Expected:**
- Detailed state: state name, mode, assessment count, Q&A count, artifacts
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session with state data:
    result = runner.invoke(main, ["status", "01"])
    ASSERT result.exit_code == 0
    ASSERT "state" in result.output.lower()
    ASSERT "mode" in result.output.lower()
```

### TS-04-41: Show without artifact shows session state

**Requirement:** 04-REQ-10.3
**Type:** unit
**Description:** Verify show without --artifact displays session state.

**Preconditions:**
- Campaign with spec

**Input:**
- Invoke `spec show 01`

**Expected:**
- Session state summary displayed
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session:
    result = runner.invoke(main, ["show", "01"])
    ASSERT result.exit_code == 0
    ASSERT "state" in result.output.lower()
```

### TS-04-42: Show with artifact displays content

**Requirement:** 04-REQ-10.4
**Type:** unit
**Description:** Verify show --artifact reads and displays artifact content.

**Preconditions:**
- Spec directory with prd.md file

**Input:**
- Invoke `spec show 01 --artifact prd.md`

**Expected:**
- Content of prd.md printed to stdout
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with spec dir containing prd.md:
    result = runner.invoke(main, ["show", "01", "--artifact", "prd.md"])
    ASSERT result.exit_code == 0
    ASSERT prd_content in result.output
```

### TS-04-43: Show with nonexistent artifact

**Requirement:** 04-REQ-10.5
**Type:** unit
**Description:** Verify show --artifact fails when artifact does not exist.

**Preconditions:**
- Spec directory without the requested artifact

**Input:**
- Invoke `spec show 01 --artifact nonexistent.md`

**Expected:**
- Error listing available artifacts
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
result = runner.invoke(main, ["show", "01", "--artifact", "nonexistent.md"])
ASSERT result.exit_code == 1
ASSERT "available" in result.output.lower() or "prd.md" in result.output
```

### TS-04-44: Spec not found lists available specs

**Requirement:** 04-REQ-10.E1, 04-REQ-CC.5
**Type:** unit
**Description:** Verify unmatched spec argument lists available specs.

**Preconditions:**
- Campaign with specs 01 and 02

**Input:**
- Invoke `spec assess 99`

**Expected:**
- Error listing available specs (01, 02)
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with campaign containing specs 01 and 02:
    result = runner.invoke(main, ["assess", "99"])
    ASSERT result.exit_code == 1
    ASSERT "01" in result.output
    ASSERT "02" in result.output
```

### TS-04-45: Campaign-dir option overrides CWD

**Requirement:** 04-REQ-CC.1, 04-REQ-CC.2
**Type:** unit
**Description:** Verify --campaign-dir option is used instead of CWD.

**Preconditions:**
- Campaign at /tmp/my-campaign, CWD is /tmp

**Input:**
- Invoke `spec --campaign-dir /tmp/my-campaign list`

**Expected:**
- Campaign opened from /tmp/my-campaign, not CWD

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.open:
    result = runner.invoke(main, ["--campaign-dir", str(campaign_dir), "list"])
    ASSERT Campaign.open.called_with(campaign_dir)
```

### TS-04-46: No campaign directory error

**Requirement:** 04-REQ-CC.3
**Type:** unit
**Description:** Verify clear error when not in a campaign directory.

**Preconditions:**
- CWD has no campaign.yaml

**Input:**
- Invoke `spec status`

**Expected:**
- Error message about campaign directory with --campaign-dir hint
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.open raising CampaignError:
    result = runner.invoke(main, ["status"])
    ASSERT result.exit_code == 1
    ASSERT "campaign" in result.output.lower()
    ASSERT "--campaign-dir" in result.output
```

### TS-04-47: Spec resolved by full name

**Requirement:** 04-REQ-CC.4
**Type:** unit
**Description:** Verify spec can be resolved by full directory name.

**Preconditions:**
- Campaign with spec "01_data_models"

**Input:**
- Invoke `spec status 01_data_models`

**Expected:**
- Spec resolved to 01_data_models directory
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with campaign containing "01_data_models":
    result = runner.invoke(main, ["status", "01_data_models"])
    ASSERT result.exit_code == 0
```

### TS-04-48: Spec resolved by numeric prefix

**Requirement:** 04-REQ-CC.4
**Type:** unit
**Description:** Verify spec can be resolved by just the number.

**Preconditions:**
- Campaign with spec "01_data_models"

**Input:**
- Invoke `spec status 01`

**Expected:**
- Spec resolved to 01_data_models directory
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with campaign containing "01_data_models":
    result = runner.invoke(main, ["status", "01"])
    ASSERT result.exit_code == 0
```

### TS-04-49: Exit code 0 on success

**Requirement:** 04-REQ-CC.6
**Type:** unit
**Description:** Verify successful commands exit with code 0.

**Preconditions:**
- Valid campaign and spec

**Input:**
- Invoke `spec status 01` (any successful command)

**Expected:**
- Exit code 0

**Assertion pseudocode:**
```
runner = CliRunner()
with valid setup:
    result = runner.invoke(main, ["status", "01"])
    ASSERT result.exit_code == 0
```

### TS-04-50: Exit code 1 on user error

**Requirement:** 04-REQ-CC.6
**Type:** unit
**Description:** Verify user errors exit with code 1.

**Preconditions:**
- CampaignError or SessionError raised

**Input:**
- Invoke command that triggers user error

**Expected:**
- Exit code 1

**Assertion pseudocode:**
```
runner = CliRunner()
with mock raising CampaignError:
    result = runner.invoke(main, ["list"])
    ASSERT result.exit_code == 1
```

### TS-04-51: Exit code 2 on internal error

**Requirement:** 04-REQ-CC.6
**Type:** unit
**Description:** Verify unexpected exceptions exit with code 2.

**Preconditions:**
- Unexpected RuntimeError raised

**Input:**
- Invoke command that triggers unexpected error

**Expected:**
- Exit code 2

**Assertion pseudocode:**
```
runner = CliRunner()
with mock raising RuntimeError("unexpected"):
    result = runner.invoke(main, ["assess", "01"])
    ASSERT result.exit_code == 2
```

## Edge Case Tests

### TS-04-E1: Init resolves relative path to absolute

**Requirement:** 04-REQ-1.E1
**Type:** edge-case
**Description:** Verify init resolves a relative path to absolute before passing to Campaign.create.
**Covered by:** TS-04-5

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.create:
    result = runner.invoke(main, ["init", "./my-campaign", "--name", "Test"])
    ASSERT Path(Campaign.create.call_args[0][0]).is_absolute()
```

### TS-04-E2: List error on non-campaign directory

**Requirement:** 04-REQ-2.E1
**Type:** edge-case
**Description:** Verify list fails with clear error when directory has no campaign.yaml.
**Covered by:** TS-04-10

**Assertion pseudocode:**
```
runner = CliRunner()
with mock Campaign.open raising CampaignError:
    result = runner.invoke(main, ["list"])
    ASSERT result.exit_code == 1
    ASSERT "campaign" in result.output.lower()
```

### TS-04-E3: New with invalid spec name

**Requirement:** 04-REQ-3.E1
**Type:** edge-case
**Description:** Verify error when spec name contains characters not matching `[a-z][a-z0-9_]*`.
**Covered by:** TS-04-16

**Assertion pseudocode:**
```
runner = CliRunner()
with mock campaign.new_spec raising CampaignError("invalid name"):
    result = runner.invoke(main, ["new", str(prd_path), "--name", "Invalid Name!"])
    ASSERT result.exit_code == 1
```

### TS-04-E4: Assess agent pipeline error

**Requirement:** 04-REQ-4.E1
**Type:** edge-case
**Description:** Verify assess exits 2 on unexpected agent pipeline error.
**Covered by:** TS-04-20

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.assess raising RuntimeError("agent failed"):
    result = runner.invoke(main, ["assess", "01"])
    ASSERT result.exit_code == 2
```

### TS-04-E5: Refine invalid answers schema

**Requirement:** 04-REQ-5.E1
**Type:** edge-case
**Description:** Verify refine fails when JSON is not an object mapping question IDs to strings.
**Covered by:** TS-04-26

**Assertion pseudocode:**
```
runner = CliRunner()
with temp file "bad_schema.json" = '["not", "an", "object"]':
    result = runner.invoke(main, ["refine", "01", "--answers", str(bad_path)])
    ASSERT result.exit_code == 1
```

### TS-04-E6: Generate agent pipeline error

**Requirement:** 04-REQ-7.E1
**Type:** edge-case
**Description:** Verify generate exits 2 on unexpected agent pipeline error.
**Covered by:** TS-04-31

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.generate raising RuntimeError("agent failed"):
    result = runner.invoke(main, ["generate", "01"])
    ASSERT result.exit_code == 2
```

### TS-04-E7: Validate with missing artifacts

**Requirement:** 04-REQ-8.E1
**Type:** edge-case
**Description:** Verify validate reports missing artifacts when spec is not yet generated.
**Covered by:** TS-04-34

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.validate raising SessionError("missing artifacts"):
    result = runner.invoke(main, ["validate", "01"])
    ASSERT result.exit_code == 1
    ASSERT "missing" in result.output.lower()
```

### TS-04-E8: Render with missing artifacts

**Requirement:** 04-REQ-9.E1
**Type:** edge-case
**Description:** Verify render reports missing artifacts.
**Covered by:** TS-04-38

**Assertion pseudocode:**
```
runner = CliRunner()
with mock session.render raising SessionError("missing artifacts"):
    result = runner.invoke(main, ["render", "01"])
    ASSERT result.exit_code == 1
    ASSERT "missing" in result.output.lower()
```

### TS-04-E9: Spec not found lists available specs

**Requirement:** 04-REQ-10.E1
**Type:** edge-case
**Description:** Verify unmatched spec argument lists available specs by number and name.
**Covered by:** TS-04-44

**Assertion pseudocode:**
```
runner = CliRunner()
with campaign containing specs 01 and 02:
    result = runner.invoke(main, ["assess", "99"])
    ASSERT result.exit_code == 1
    ASSERT "01" in result.output
    ASSERT "02" in result.output
```

## Property Test Cases

### TS-04-P1: Spec resolution determinism

**Property:** Property 1 from design.md
**Validates:** 04-REQ-CC.4
**Type:** property
**Description:** For any campaign and any valid spec identifier, resolve_spec always returns the same path.

**For any:** spec_prefix in range(1, max_spec+1), and campaign with known specs
**Invariant:** resolve_spec(campaign, str(prefix)) == resolve_spec(campaign, str(prefix))

**Assertion pseudocode:**
```
FOR ANY spec_arg IN [spec.name, str(spec.number) for spec in campaign.specs]:
    result1 = resolve_spec(campaign, spec_arg)
    result2 = resolve_spec(campaign, spec_arg)
    ASSERT result1 == result2
    ASSERT result1.exists()
```

### TS-04-P2: Error commands never exit 0

**Property:** Property 2 from design.md
**Validates:** 04-REQ-CC.6
**Type:** property
**Description:** Any command invocation that encounters CampaignError or SessionError exits with non-zero code.

**For any:** subcommand in all_commands, error in [CampaignError, SessionError]
**Invariant:** result.exit_code != 0

**Assertion pseudocode:**
```
FOR ANY cmd IN ["list", "status", "assess", "accept", "generate", "validate", "render", "show"]:
    FOR ANY error_cls IN [CampaignError, SessionError]:
        with mock raising error_cls("test"):
            result = runner.invoke(main, [cmd, "01"])
            ASSERT result.exit_code != 0
```

### TS-04-P3: Campaign dir resolution precedence

**Property:** Property 3 from design.md
**Validates:** 04-REQ-CC.1, 04-REQ-CC.2
**Type:** property
**Description:** When --campaign-dir is provided, CWD is ignored.

**For any:** campaign_dir path and CWD path (both valid campaign dirs)
**Invariant:** The campaign opened is always the one from --campaign-dir

**Assertion pseudocode:**
```
FOR ANY campaign_dir, cwd IN pairs_of_campaign_dirs:
    with mock Campaign.open, CWD=cwd:
        runner.invoke(main, ["--campaign-dir", str(campaign_dir), "list"])
        ASSERT Campaign.open.called_with(Path(campaign_dir))
```

### TS-04-P4: Init never overwrites existing campaign

**Property:** Property 4 from design.md
**Validates:** 04-REQ-1.4
**Type:** property
**Description:** Init always fails on a directory that already has campaign.yaml.

**For any:** directory containing campaign.yaml
**Invariant:** exit_code == 1

**Assertion pseudocode:**
```
FOR ANY dir WITH campaign.yaml:
    result = runner.invoke(main, ["init", str(dir)])
    ASSERT result.exit_code == 1
```

### TS-04-P5: State gate enforcement

**Property:** Property 5 from design.md
**Validates:** 04-REQ-4.3, 04-REQ-5.4, 04-REQ-6.2, 04-REQ-7.3
**Type:** property
**Description:** Commands requiring specific state fail with code 1 in wrong state.

**For any:** (command, required_state, wrong_state) triple
**Invariant:** exit_code == 1 when session is in wrong_state

**Assertion pseudocode:**
```
state_gates = [
    ("assess", ["init", "refining"], ["generated", "prd_accepted"]),
    ("refine", ["refining"], ["init", "generated"]),
    ("accept", ["assessing", "refining"], ["init", "generated"]),
    ("generate", ["prd_accepted"], ["init", "refining", "generated"]),
]
FOR ANY (cmd, valid_states, invalid_states) IN state_gates:
    FOR ANY wrong_state IN invalid_states:
        with session in wrong_state raising SessionError:
            result = runner.invoke(main, [cmd, "01", ...])
            ASSERT result.exit_code == 1
```

## Integration Smoke Tests

### TS-04-SMOKE-1: Init and list round trip

**Execution Path:** Path 1, then Path 2 from design.md
**Description:** Create a campaign and list its contents (empty).

**Setup:** Temp directory, no prior campaign.

**Trigger:**
1. `spec init <tmp> --name "Test"`
2. `spec --campaign-dir <tmp> list`

**Expected side effects:**
- Init creates directory with campaign.yaml
- List shows empty campaign message

**Must NOT satisfy with:** Mocking Campaign class.

**Assertion pseudocode:**
```
runner = CliRunner()
result1 = runner.invoke(main, ["init", str(tmp_path), "--name", "Test"])
ASSERT result1.exit_code == 0
ASSERT (tmp_path / "campaign.yaml").exists()
result2 = runner.invoke(main, ["--campaign-dir", str(tmp_path), "list"])
ASSERT result2.exit_code == 0
ASSERT "empty" in result2.output.lower() or "no specs" in result2.output.lower()
```

### TS-04-SMOKE-2: New and status round trip

**Execution Path:** Path 3, then Path 11 from design.md
**Description:** Create a spec and check its status.

**Setup:** Existing campaign directory, PRD file.

**Trigger:**
1. `spec --campaign-dir <tmp> new prd.md --name test_spec`
2. `spec --campaign-dir <tmp> status 01`

**Expected side effects:**
- New creates spec directory with prd.md and _session.json
- Status shows spec in init state

**Must NOT satisfy with:** Mocking SpecSession class.

**Assertion pseudocode:**
```
runner = CliRunner()
create_campaign(tmp_path)
write(tmp_path / "prd.md", "# Test PRD\n\nSome content.")
result1 = runner.invoke(main, ["--campaign-dir", str(tmp_path), "new",
                                str(tmp_path / "prd.md"), "--name", "test_spec"])
ASSERT result1.exit_code == 0
result2 = runner.invoke(main, ["--campaign-dir", str(tmp_path), "status", "01"])
ASSERT result2.exit_code == 0
ASSERT "init" in result2.output.lower()
```

### TS-04-SMOKE-3: Show artifact content

**Execution Path:** Path 10 from design.md
**Description:** Show a specific artifact from a spec.

**Setup:** Campaign with spec containing prd.md.

**Trigger:** `spec --campaign-dir <tmp> show 01 --artifact prd.md`

**Expected side effects:**
- PRD content printed to stdout

**Must NOT satisfy with:** Mocking file reads.

**Assertion pseudocode:**
```
runner = CliRunner()
create_campaign_with_spec(tmp_path)
result = runner.invoke(main, ["--campaign-dir", str(tmp_path), "show", "01",
                               "--artifact", "prd.md"])
ASSERT result.exit_code == 0
ASSERT "Test PRD" in result.output or prd_content in result.output
```

### TS-04-SMOKE-4: Validate and render round trip

**Execution Path:** Path 8, then Path 9 from design.md
**Description:** Validate a spec and then render it.

**Setup:** Campaign with spec in generated state (all artifacts present).

**Trigger:**
1. `spec --campaign-dir <tmp> validate 01`
2. `spec --campaign-dir <tmp> render 01`

**Expected side effects:**
- Validate reports results (pass or fail)
- Render outputs markdown

**Must NOT satisfy with:** Mocking session methods.

**Assertion pseudocode:**
```
runner = CliRunner()
create_campaign_with_generated_spec(tmp_path)
result1 = runner.invoke(main, ["--campaign-dir", str(tmp_path), "validate", "01"])
# May pass or fail depending on spec quality
result2 = runner.invoke(main, ["--campaign-dir", str(tmp_path), "render", "01"])
ASSERT result2.exit_code == 0
ASSERT "#" in result2.output  # markdown headers
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 04-REQ-1.1 | TS-04-1 | unit |
| 04-REQ-1.2 | TS-04-2 | unit |
| 04-REQ-1.3 | TS-04-3 | unit |
| 04-REQ-1.4 | TS-04-4 | unit |
| 04-REQ-1.E1 | TS-04-5, TS-04-E1 | unit, edge-case |
| 04-REQ-2.1 | TS-04-6 | unit |
| 04-REQ-2.2 | TS-04-7 | unit |
| 04-REQ-2.3 | TS-04-8 | unit |
| 04-REQ-2.4 | TS-04-9 | unit |
| 04-REQ-2.E1 | TS-04-10, TS-04-E2 | unit, edge-case |
| 04-REQ-3.1 | TS-04-11 | unit |
| 04-REQ-3.2 | TS-04-12, TS-04-13 | unit |
| 04-REQ-3.3 | TS-04-14 | unit |
| 04-REQ-3.4 | TS-04-15 | unit |
| 04-REQ-3.E1 | TS-04-16, TS-04-E3 | unit, edge-case |
| 04-REQ-4.1 | TS-04-17 | unit |
| 04-REQ-4.2 | TS-04-18 | unit |
| 04-REQ-4.3 | TS-04-19 | unit |
| 04-REQ-4.E1 | TS-04-20, TS-04-E4 | unit, edge-case |
| 04-REQ-5.1 | TS-04-21 | unit |
| 04-REQ-5.2 | TS-04-22 | unit |
| 04-REQ-5.3 | TS-04-23 | unit |
| 04-REQ-5.4 | TS-04-24 | unit |
| 04-REQ-5.5 | TS-04-25 | unit |
| 04-REQ-5.E1 | TS-04-26, TS-04-E5 | unit, edge-case |
| 04-REQ-6.1 | TS-04-27 | unit |
| 04-REQ-6.2 | TS-04-28 | unit |
| 04-REQ-7.1 | TS-04-29 | unit |
| 04-REQ-7.2 | TS-04-29 | unit |
| 04-REQ-7.3 | TS-04-30 | unit |
| 04-REQ-7.E1 | TS-04-31, TS-04-E6 | unit, edge-case |
| 04-REQ-8.1 | TS-04-32 | unit |
| 04-REQ-8.2 | TS-04-32 | unit |
| 04-REQ-8.3 | TS-04-33 | unit |
| 04-REQ-8.4 | TS-04-33 | unit |
| 04-REQ-8.E1 | TS-04-34, TS-04-E7 | unit, edge-case |
| 04-REQ-9.1 | TS-04-35 | unit |
| 04-REQ-9.2 | TS-04-36 | unit |
| 04-REQ-9.3 | TS-04-37 | unit |
| 04-REQ-9.E1 | TS-04-38, TS-04-E8 | unit, edge-case |
| 04-REQ-10.1 | TS-04-39 | unit |
| 04-REQ-10.2 | TS-04-40 | unit |
| 04-REQ-10.3 | TS-04-41 | unit |
| 04-REQ-10.4 | TS-04-42 | unit |
| 04-REQ-10.5 | TS-04-43 | unit |
| 04-REQ-10.E1 | TS-04-44, TS-04-E9 | unit, edge-case |
| 04-REQ-CC.1 | TS-04-45 | unit |
| 04-REQ-CC.2 | TS-04-45 | unit |
| 04-REQ-CC.3 | TS-04-46 | unit |
| 04-REQ-CC.4 | TS-04-47, TS-04-48 | unit |
| 04-REQ-CC.5 | TS-04-44 | unit |
| 04-REQ-CC.6 | TS-04-49, TS-04-50, TS-04-51 | unit |
| Property 1 | TS-04-P1 | property |
| Property 2 | TS-04-P2 | property |
| Property 3 | TS-04-P3 | property |
| Property 4 | TS-04-P4 | property |
| Property 5 | TS-04-P5 | property |
| Path 1+2 | TS-04-SMOKE-1 | integration |
| Path 3+11 | TS-04-SMOKE-2 | integration |
| Path 10 | TS-04-SMOKE-3 | integration |
| Path 8+9 | TS-04-SMOKE-4 | integration |
