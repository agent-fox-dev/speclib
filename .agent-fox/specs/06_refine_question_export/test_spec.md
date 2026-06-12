# Test Specification: Refine Question Export

## Overview

Tests verify the question-export behavior of `spec refine` when called
without `--answers`, the `pending_questions()` session method, and that
existing answer-submission behavior is preserved.

## Test Cases

### TS-06-1: Refine without answers outputs questions JSON

**Requirement:** 06-REQ-1.1
**Type:** unit
**Description:** Verifies that `refine` without `--answers` outputs valid JSON
to stdout and exits 0.

**Preconditions:**
- Campaign directory exists with a spec in `assessing` state.
- Session has at least one assessment with questions.

**Input:**
- CLI invocation: `spec --campaign-dir <dir> refine 01` (no `--answers`).

**Expected:**
- Exit code 0.
- stdout contains valid JSON with top-level keys `questions` and `answers`.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["--campaign-dir", dir, "refine", "01"])
ASSERT result.exit_code == 0
data = json.loads(result.output)
ASSERT "questions" IN data
ASSERT "answers" IN data
```

### TS-06-2: Questions array contains full question details

**Requirement:** 06-REQ-1.2
**Type:** unit
**Description:** Verifies each question object in the output contains all
required fields.

**Preconditions:**
- Session assessment has questions with all fields populated.

**Input:**
- CLI invocation: `spec refine 01` (no `--answers`).

**Expected:**
- Each item in `questions` array has keys: `id`, `text`, `context`, `options`,
  `required`.

**Assertion pseudocode:**
```
data = json.loads(result.output)
FOR EACH q IN data["questions"]:
    ASSERT {"id", "text", "context", "options", "required"} SUBSET OF q.keys()
```

### TS-06-3: Answers template maps question IDs to empty strings

**Requirement:** 06-REQ-1.3
**Type:** unit
**Description:** Verifies the `answers` dict contains one key per question ID,
each mapped to an empty string.

**Preconditions:**
- Session assessment has questions with IDs `q1`, `q2`.

**Input:**
- CLI invocation: `spec refine 01` (no `--answers`).

**Expected:**
- `answers` is `{"q1": "", "q2": ""}`.

**Assertion pseudocode:**
```
data = json.loads(result.output)
question_ids = {q["id"] for q in data["questions"]}
ASSERT set(data["answers"].keys()) == question_ids
ASSERT all(v == "" for v in data["answers"].values())
```

### TS-06-4: Refine with answers still works (existing behavior)

**Requirement:** 06-REQ-1.4
**Type:** unit
**Description:** Verifies the existing answer-submission path is unchanged when
`--answers` is provided.

**Preconditions:**
- Campaign directory with spec in `assessing` state.
- Valid answers file exists.

**Input:**
- CLI invocation: `spec refine 01 --answers answers.json`.

**Expected:**
- `session.refine()` is called with the answers dict.
- Exit code 0.
- Output contains assessment information.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, [..., "refine", "01", "--answers", file])
ASSERT result.exit_code == 0
ASSERT session.refine.called_once()
```

## Edge Case Tests

### TS-06-E1: No assessment exists

**Requirement:** 06-REQ-1.E1
**Type:** unit
**Description:** Verifies error when refine without answers is called on a
session with no assessment.

**Preconditions:**
- Session exists but has no assessment history.

**Input:**
- CLI invocation: `spec refine 01` (no `--answers`).

**Expected:**
- Exit code 1.
- stderr contains error about missing assessment.

**Assertion pseudocode:**
```
result = cli_runner.invoke(main, ["--campaign-dir", dir, "refine", "01"])
ASSERT result.exit_code == 1
ASSERT "no assessment" IN result.output.lower() OR "assessment" IN result.output.lower()
```

### TS-06-E2: Assessment with zero questions

**Requirement:** 06-REQ-1.E2
**Type:** unit
**Description:** Verifies output when assessment has no questions.

**Preconditions:**
- Session has an assessment with quality "ready" and empty questions list.

**Input:**
- CLI invocation: `spec refine 01` (no `--answers`).

**Expected:**
- Exit code 0.
- JSON output: `{"questions": [], "answers": {}}`.

**Assertion pseudocode:**
```
data = json.loads(result.output)
ASSERT data["questions"] == []
ASSERT data["answers"] == {}
```

### TS-06-E3: Pending questions with missing optional fields

**Requirement:** 06-REQ-2.E1
**Type:** unit
**Description:** Verifies `pending_questions()` uses defaults for missing
optional fields.

**Preconditions:**
- Session assessment has a question dict missing `options` and `required` keys.

**Input:**
- Call `session.pending_questions()`.

**Expected:**
- Returned dict has `options: []` and `required: False`.

**Assertion pseudocode:**
```
questions = session.pending_questions()
ASSERT questions[0]["options"] == []
ASSERT questions[0]["required"] == False
```

## Property Test Cases

### TS-06-P1: Answer template key parity

**Property:** Property 1 from design.md
**Validates:** 06-REQ-1.2, 06-REQ-1.3
**Type:** property
**Description:** For any non-empty set of questions, the answer template keys
match the question IDs exactly.

**For any:** list of 1-10 question dicts with unique string IDs
**Invariant:** `set(answers.keys()) == {q["id"] for q in questions}`

**Assertion pseudocode:**
```
FOR ANY questions IN lists(question_dicts, min_size=1, max_size=10):
    answers = {q["id"]: "" for q in questions}
    ASSERT set(answers.keys()) == {q["id"] for q in questions}
```

### TS-06-P2: Pending questions fidelity

**Property:** Property 2 from design.md
**Validates:** 06-REQ-2.1, 06-REQ-2.E1
**Type:** property
**Description:** `pending_questions()` output matches the assessment's
questions in count and content.

**For any:** assessment history with 0-10 questions, some missing optional fields
**Invariant:** `len(result) == len(assessment.questions)` and each dict
contains matching values for all five keys.

**Assertion pseudocode:**
```
FOR ANY history IN assessment_histories(0, 10):
    session = build_session(history)
    result = session.pending_questions()
    ASSERT len(result) == len(history[-1]["questions"])
    FOR EACH (r, q) IN zip(result, history[-1]["questions"]):
        ASSERT r["id"] == q["id"]
        ASSERT r["text"] == q["text"]
```

### TS-06-P3: Read-only invariant

**Property:** Property 3 from design.md
**Validates:** 06-REQ-2.3
**Type:** property
**Description:** `pending_questions()` does not modify session state.

**For any:** session in any valid state with any assessment history
**Invariant:** `state_before == state_after` and
`history_before == history_after`

**Assertion pseudocode:**
```
FOR ANY session IN valid_sessions():
    state_before = session.state
    history_before = copy(session._assessment_history)
    session.pending_questions()
    ASSERT session.state == state_before
    ASSERT session._assessment_history == history_before
```

### TS-06-P4: Existing behavior preservation

**Property:** Property 4 from design.md
**Validates:** 06-REQ-1.4
**Type:** property
**Description:** When `--answers` is provided, `refine_cmd` calls
`session.refine()` and never outputs the question-export JSON.

**For any:** valid answers dict with 1-5 question IDs
**Invariant:** `session.refine` is called exactly once with the provided
answers, and stdout does not contain a `questions` key.

**Assertion pseudocode:**
```
FOR ANY answers IN valid_answer_dicts(1, 5):
    result = invoke_refine_with_answers(answers)
    ASSERT session.refine.called_once_with(answers)
    ASSERT "questions" NOT IN result.output
```

## Integration Smoke Tests

### TS-06-SMOKE-1: Full question export path

**Execution Path:** Path 1 from design.md
**Description:** Verifies the full path from CLI invocation through session
resume to JSON output on stdout.

**Setup:** Create a real campaign directory with a spec dir containing a
`_session.json` file with an assessment that has questions. No mocking of
`SpecSession` or `pending_questions`.

**Trigger:** `spec --campaign-dir <dir> refine <spec>` (no `--answers`).

**Expected side effects:**
- stdout contains valid JSON.
- JSON has `questions` array matching the session's assessment questions.
- JSON has `answers` dict with matching keys.
- Exit code 0.
- `_session.json` is unchanged (read-only operation).

**Must NOT satisfy with:** Mocking `SpecSession`, `pending_questions()`, or
`SpecSession.resume()`.

**Assertion pseudocode:**
```
session_before = read_file(spec_dir / "_session.json")
result = cli_runner.invoke(main, ["--campaign-dir", dir, "refine", spec])
ASSERT result.exit_code == 0
data = json.loads(result.output)
ASSERT len(data["questions"]) == number_of_questions_in_session
session_after = read_file(spec_dir / "_session.json")
ASSERT session_before == session_after
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 06-REQ-1.1 | TS-06-1 | unit |
| 06-REQ-1.2 | TS-06-2 | unit |
| 06-REQ-1.3 | TS-06-3 | unit |
| 06-REQ-1.4 | TS-06-4 | unit |
| 06-REQ-1.E1 | TS-06-E1 | unit |
| 06-REQ-1.E2 | TS-06-E2 | unit |
| 06-REQ-2.1 | TS-06-P2 | property |
| 06-REQ-2.2 | TS-06-P2 | property |
| 06-REQ-2.3 | TS-06-P3 | property |
| 06-REQ-2.E1 | TS-06-E3 | unit |
| Property 1 | TS-06-P1 | property |
| Property 2 | TS-06-P2 | property |
| Property 3 | TS-06-P3 | property |
| Property 4 | TS-06-P4 | property |
| Path 1 | TS-06-SMOKE-1 | integration |
