# Requirements Document

## Introduction

Extends the `spec refine` CLI command and the `SpecSession` library class to
support question export: when `refine` is called without `--answers`, it outputs
the pending assessment questions as structured JSON to stdout.

## Glossary

- **Assessment**: A structured evaluation of a PRD produced by `SpecAgent`,
  containing quality rating, summary, gaps, and questions.
- **Question**: A structured prompt in an assessment asking the user for
  clarification, with id, text, context, options, and required flag.
- **Answer template**: A JSON object mapping question IDs to empty strings,
  ready for the user to fill in and pass back via `--answers`.
- **Pending questions**: The questions from the most recent assessment in the
  session's assessment history.

## Requirements

### Requirement 1: Question Export on Refine Without Answers

**User Story:** As a user or automation agent, I want to run `spec refine`
without `--answers` to get the pending questions as JSON, so that I can easily
create the expected answer file.

#### Acceptance Criteria

1. [06-REQ-1.1] WHEN `spec refine <spec>` is invoked without `--answers`,
   THE CLI SHALL output a JSON object to stdout containing the pending
   assessment questions and an answer template, AND exit with code 0.

2. [06-REQ-1.2] WHEN `spec refine <spec>` is invoked without `--answers`,
   THE CLI SHALL include a `questions` key in the JSON output whose value is an
   array of question objects, each containing keys `id`, `text`, `context`,
   `options`, and `required`.

3. [06-REQ-1.3] WHEN `spec refine <spec>` is invoked without `--answers`,
   THE CLI SHALL include an `answers` key in the JSON output whose value is a
   JSON object mapping each question ID to an empty string.

4. [06-REQ-1.4] WHEN `spec refine <spec> --answers <file>` is invoked,
   THE CLI SHALL continue to submit answers and update the PRD exactly as
   before (no behavioral change to existing path).

#### Edge Cases

1. [06-REQ-1.E1] IF `spec refine <spec>` is invoked without `--answers` and
   the session has no assessment (empty assessment history), THEN THE CLI SHALL
   print an error message to stderr indicating no assessment exists and exit
   with code 1.

2. [06-REQ-1.E2] IF `spec refine <spec>` is invoked without `--answers` and
   the latest assessment contains zero questions, THEN THE CLI SHALL output a
   JSON object with an empty `questions` array and an empty `answers` object,
   AND exit with code 0.

### Requirement 2: Session Pending Questions Method

**User Story:** As a library consumer, I want to call `session.pending_questions()`
to get the pending assessment questions as a serializable data structure, so that
I can build tooling around question inspection without parsing `_session.json`
directly.

#### Acceptance Criteria

1. [06-REQ-2.1] THE `SpecSession` class SHALL expose a `pending_questions()`
   method that returns a list of dicts, each containing keys `id`, `text`,
   `context`, `options`, and `required`, corresponding to the questions in the
   latest assessment.

2. [06-REQ-2.2] WHEN the session has no assessment history,
   `pending_questions()` SHALL return an empty list.

3. [06-REQ-2.3] THE `pending_questions()` method SHALL be callable without
   triggering a state transition (read-only operation).

#### Edge Cases

1. [06-REQ-2.E1] IF the latest assessment contains questions with missing
   optional fields (`options`, `required`), THEN `pending_questions()` SHALL
   use default values (empty list for `options`, `False` for `required`).
