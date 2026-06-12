# Requirements Document

## Introduction

Extends `SpecSession.refine()` to record the user-provided answers in the
existing `qa_exchanges` field of `_session.json`, creating a complete audit
trail of the assess-refine-accept interaction loop.

## Glossary

- **QA Exchange**: A record of one refine interaction, containing the answers
  the user provided in response to a specific assessment's questions.
- **Assessment History**: The ordered list of assessment snapshots stored in
  `_session.json`, each containing quality, summary, gaps, and questions.
- **Assessment Index**: The zero-based index into `assessment_history`
  identifying which assessment's questions an answer set responds to.

## Requirements

### Requirement 1: Record Answers on Refine

**User Story:** As a user reviewing a refinement session, I want the answers
I provided to be stored in `_session.json`, so that I can audit the full
decision trail that shaped the PRD.

#### Acceptance Criteria

1. [07-REQ-1.1] WHEN `session.refine(answers)` is called successfully, THE
   session SHALL append a QA exchange entry to `qa_exchanges` containing the
   provided `answers` dict, the `assessment_index` of the assessment whose
   questions were answered, and an ISO 8601 UTC `timestamp`.

2. [07-REQ-1.2] WHEN `session.refine(answers)` is called successfully, THE
   persisted `_session.json` SHALL contain the new QA exchange entry in the
   `qa_exchanges` array AND the new assessment in `assessment_history`.

3. [07-REQ-1.3] THE `assessment_index` in each QA exchange entry SHALL equal
   the zero-based index of the assessment in `assessment_history` whose
   questions the answers respond to (i.e., the index of the last assessment
   at the time `refine()` was called, before the new assessment is appended).

#### Edge Cases

1. [07-REQ-1.E1] IF `session.refine(answers)` fails due to an agent error,
   THEN THE session SHALL NOT append any QA exchange entry to `qa_exchanges`.

2. [07-REQ-1.E2] IF `_session.json` is loaded from an existing session with
   an empty `qa_exchanges` array, THEN THE session SHALL function normally
   and accept new QA exchanges without requiring migration.

### Requirement 2: QA Exchange Data Structure

**User Story:** As a developer building tooling on top of the session data,
I want a consistent QA exchange schema, so that I can reliably parse and
display the refinement history.

#### Acceptance Criteria

1. [07-REQ-2.1] THE QA exchange entry SHALL be a JSON object with exactly
   three keys: `assessment_index` (integer), `answers` (object mapping
   question IDs to answer strings), and `timestamp` (ISO 8601 UTC string).

2. [07-REQ-2.2] THE `timestamp` SHALL be generated at the time `refine()` is
   called, before the agent API call, to record when the user submitted
   answers AND the value SHALL be returned by a module-level function so
   tests can patch it.

### Requirement 3: No Side Effects on Existing Interfaces

**User Story:** As a user of `spec refine` and `spec refine` (without
answers), I want the existing behavior to remain unchanged.

#### Acceptance Criteria

1. [07-REQ-3.1] WHEN `spec refine <spec>` is invoked without `--answers`,
   THE CLI SHALL output the same question-export JSON as before, with no
   `qa_exchanges` information included.

2. [07-REQ-3.2] WHEN `session.pending_questions()` is called, THE method
   SHALL return the same result as before, unaffected by any QA exchange
   entries.
