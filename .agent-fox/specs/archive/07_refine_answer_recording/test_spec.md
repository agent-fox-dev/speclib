# Test Specification: Refine Answer Recording

## Overview

Tests verify that `SpecSession.refine()` appends QA exchange entries to
`qa_exchanges` in `_session.json` with the correct structure, and that
failed refines and existing interfaces remain unaffected.

## Test Cases

### TS-07-1: Refine appends QA exchange entry

**Requirement:** 07-REQ-1.1
**Type:** unit
**Description:** Verifies that a successful `refine()` call appends one
entry to `qa_exchanges`.

**Preconditions:**
- Session in `assessing` state with one assessment containing questions.
- Agent mock returns updated PRD and new assessment.

**Input:**
- `answers = {"q1": "answer1", "q2": "answer2"}`

**Expected:**
- `qa_exchanges` has exactly 1 entry after refine.
- Entry contains `assessment_index`, `answers`, `timestamp`.

**Assertion pseudocode:**
```
session = create_session(state=assessing, with_assessment=True)
mock_agent_success()
await session.refine({"q1": "a1", "q2": "a2"})
ASSERT len(session._qa_exchanges) == 1
entry = session._qa_exchanges[0]
ASSERT "assessment_index" IN entry
ASSERT "answers" IN entry
ASSERT "timestamp" IN entry
```

### TS-07-2: QA exchange persisted to _session.json

**Requirement:** 07-REQ-1.2
**Type:** unit
**Description:** Verifies that the QA exchange entry appears in the
persisted `_session.json` file.

**Preconditions:**
- Session in `assessing` state with one assessment.

**Input:**
- Successful refine call with answers.

**Expected:**
- `_session.json` on disk contains `qa_exchanges` with one entry.

**Assertion pseudocode:**
```
await session.refine(answers)
data = json.loads(session_file.read_text())
ASSERT len(data["qa_exchanges"]) == 1
```

### TS-07-3: Assessment index is correct

**Requirement:** 07-REQ-1.3
**Type:** unit
**Description:** Verifies that `assessment_index` equals the index of the
assessment whose questions were answered.

**Preconditions:**
- Session with 2 assessments in history (from assess + refine).
- Second refine call being made.

**Input:**
- Second refine with answers to assessment 1's questions.

**Expected:**
- Second QA exchange entry has `assessment_index == 1`.

**Assertion pseudocode:**
```
# After first refine: assessment_history has 2 entries
await session.refine(answers_round_2)
ASSERT session._qa_exchanges[1]["assessment_index"] == 1
```

### TS-07-4: QA exchange entry has correct schema

**Requirement:** 07-REQ-2.1
**Type:** unit
**Description:** Verifies the QA exchange entry contains exactly the three
required keys with correct types.

**Preconditions:**
- Session in `assessing` state with assessment.

**Input:**
- Successful refine call.

**Expected:**
- Entry keys are exactly `{"assessment_index", "answers", "timestamp"}`.
- `assessment_index` is int, `answers` is dict, `timestamp` is str.

**Assertion pseudocode:**
```
await session.refine(answers)
entry = session._qa_exchanges[0]
ASSERT set(entry.keys()) == {"assessment_index", "answers", "timestamp"}
ASSERT isinstance(entry["assessment_index"], int)
ASSERT isinstance(entry["answers"], dict)
ASSERT isinstance(entry["timestamp"], str)
ASSERT len(entry["timestamp"]) > 0
```

### TS-07-5: Timestamp is patchable

**Requirement:** 07-REQ-2.2
**Type:** unit
**Description:** Verifies that the timestamp comes from the patchable
`_utcnow()` function.

**Preconditions:**
- Session in `assessing` state.
- `_utcnow` patched to return a fixed value.

**Input:**
- Successful refine call with patched timestamp.

**Expected:**
- Entry's `timestamp` equals the patched value.

**Assertion pseudocode:**
```
with patch("speclib.session._utcnow", return_value="2026-01-01T00:00:00+00:00"):
    await session.refine(answers)
ASSERT session._qa_exchanges[0]["timestamp"] == "2026-01-01T00:00:00+00:00"
```

### TS-07-6: Question export unchanged

**Requirement:** 07-REQ-3.1
**Type:** unit
**Description:** Verifies that refine without `--answers` still outputs
only questions and answer template, with no qa_exchanges data.

**Preconditions:**
- Session with assessment and populated qa_exchanges.

**Input:**
- CLI invocation: `spec refine 01` (no `--answers`).

**Expected:**
- JSON output has only `questions` and `answers` keys.

**Assertion pseudocode:**
```
data = json.loads(result.output)
ASSERT set(data.keys()) == {"questions", "answers"}
```

### TS-07-7: pending_questions unaffected

**Requirement:** 07-REQ-3.2
**Type:** unit
**Description:** Verifies `pending_questions()` returns the same result
regardless of qa_exchanges content.

**Preconditions:**
- Session with assessment and populated qa_exchanges.

**Input:**
- Call `session.pending_questions()`.

**Expected:**
- Returns questions from latest assessment, not affected by qa_exchanges.

**Assertion pseudocode:**
```
result = session.pending_questions()
ASSERT result == expected_questions_from_assessment
```

## Edge Case Tests

### TS-07-E1: Failed refine does not record exchange

**Requirement:** 07-REQ-1.E1
**Type:** unit
**Description:** Verifies qa_exchanges is unchanged when refine fails.

**Preconditions:**
- Session in `assessing` state.
- Agent mock raises `AgentError`.

**Input:**
- Refine call that triggers agent error.

**Expected:**
- `qa_exchanges` remains empty.

**Assertion pseudocode:**
```
with pytest.raises(AgentError):
    await session.refine(answers)
ASSERT len(session._qa_exchanges) == 0
```

### TS-07-E2: Existing empty qa_exchanges loads fine

**Requirement:** 07-REQ-1.E2
**Type:** unit
**Description:** Verifies sessions with empty qa_exchanges load normally.

**Preconditions:**
- `_session.json` with `"qa_exchanges": []`.

**Input:**
- `SpecSession.resume(spec_dir)`.

**Expected:**
- Session loads without error.
- `qa_exchanges` is an empty list.

**Assertion pseudocode:**
```
session = SpecSession.resume(spec_dir)
ASSERT session._qa_exchanges == []
```

## Property Test Cases

### TS-07-P1: Exchange count matches refine count

**Property:** Property 1 from design.md
**Validates:** 07-REQ-1.1, 07-REQ-1.E1
**Type:** property
**Description:** After N successful refine calls, qa_exchanges has N entries.

**For any:** sequence of 1-5 successful refine calls
**Invariant:** `len(qa_exchanges) == number_of_successful_refines`

**Assertion pseudocode:**
```
FOR ANY n IN range(1, 6):
    session = create_session_with_assessment()
    for i in range(n):
        mock_agent_success_with_new_questions()
        await session.refine(answers)
    ASSERT len(session._qa_exchanges) == n
```

### TS-07-P2: Assessment index consistency

**Property:** Property 2 from design.md
**Validates:** 07-REQ-1.3
**Type:** property
**Description:** Each QA exchange's assessment_index is valid and sequential.

**For any:** session with 1-5 refine rounds
**Invariant:** `qa_exchanges[i]["assessment_index"] == i` for all i

**Assertion pseudocode:**
```
FOR ANY n IN range(1, 6):
    session = run_n_refines(n)
    FOR i IN range(n):
        ASSERT session._qa_exchanges[i]["assessment_index"] == i
```

### TS-07-P3: Exchange schema consistency

**Property:** Property 3 from design.md
**Validates:** 07-REQ-2.1
**Type:** property
**Description:** Every QA exchange entry has exactly the required keys
with correct types.

**For any:** QA exchange entry produced by any successful refine
**Invariant:** keys are {assessment_index, answers, timestamp} with
correct types

**Assertion pseudocode:**
```
FOR ANY entry IN all_qa_exchanges_from_session:
    ASSERT set(entry.keys()) == {"assessment_index", "answers", "timestamp"}
    ASSERT isinstance(entry["assessment_index"], int)
    ASSERT isinstance(entry["answers"], dict)
    ASSERT isinstance(entry["timestamp"], str)
```

### TS-07-P4: Failed refine no-append

**Property:** Property 4 from design.md
**Validates:** 07-REQ-1.E1
**Type:** property
**Description:** Agent errors never increase qa_exchanges length.

**For any:** refine call that raises AgentError
**Invariant:** `len_before == len_after`

**Assertion pseudocode:**
```
FOR ANY session WITH agent_that_fails:
    len_before = len(session._qa_exchanges)
    with pytest.raises(AgentError):
        await session.refine(answers)
    ASSERT len(session._qa_exchanges) == len_before
```

## Integration Smoke Tests

### TS-07-SMOKE-1: Full refine records exchange in persisted session

**Execution Path:** Path 1 from design.md
**Description:** Verifies the full path from `refine()` through agent call
to persisted QA exchange in `_session.json`.

**Setup:** Create a real campaign/spec directory with a `_session.json`
containing one assessment with questions. Mock only the agent API call
(return updated PRD + new assessment). Patch `_utcnow` for deterministic
timestamp.

**Trigger:** `await session.refine({"q1": "answer1"})`.

**Expected side effects:**
- `_session.json` on disk has `qa_exchanges` with one entry.
- Entry has `assessment_index == 0`, `answers == {"q1": "answer1"}`,
  `timestamp` equals patched value.
- `assessment_history` has 2 entries (original + new).

**Must NOT satisfy with:** Mocking `SpecSession`, `_persist()`, or
`_qa_exchanges`.

**Assertion pseudocode:**
```
session = SpecSession.resume(spec_dir)  # real session
with patch("speclib.session._create_agent") as mock_agent_factory:
    mock_agent = mock_agent_factory.return_value
    mock_agent.refine_prd = AsyncMock(return_value=(updated_prd, new_assessment))
    with patch("speclib.session._utcnow", return_value="2026-06-10T12:00:00+00:00"):
        await session.refine({"q1": "answer1"})

data = json.loads((spec_dir / "_session.json").read_text())
ASSERT len(data["qa_exchanges"]) == 1
ASSERT data["qa_exchanges"][0]["assessment_index"] == 0
ASSERT data["qa_exchanges"][0]["answers"] == {"q1": "answer1"}
ASSERT data["qa_exchanges"][0]["timestamp"] == "2026-06-10T12:00:00+00:00"
ASSERT len(data["assessment_history"]) == 2
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 07-REQ-1.1 | TS-07-1 | unit |
| 07-REQ-1.2 | TS-07-2 | unit |
| 07-REQ-1.3 | TS-07-3 | unit |
| 07-REQ-1.E1 | TS-07-E1 | unit |
| 07-REQ-1.E2 | TS-07-E2 | unit |
| 07-REQ-2.1 | TS-07-4 | unit |
| 07-REQ-2.2 | TS-07-5 | unit |
| 07-REQ-3.1 | TS-07-6 | unit |
| 07-REQ-3.2 | TS-07-7 | unit |
| Property 1 | TS-07-P1 | property |
| Property 2 | TS-07-P2 | property |
| Property 3 | TS-07-P3 | property |
| Property 4 | TS-07-P4 | property |
| Path 1 | TS-07-SMOKE-1 | integration |
