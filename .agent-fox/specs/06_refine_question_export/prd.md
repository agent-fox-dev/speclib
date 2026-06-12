# PRD: Refine Command Question Export

## Intent

Allow the `spec refine` command to be used without `--answers` to output the
pending assessment questions as structured JSON to stdout, giving users and
agents a convenient way to inspect questions and create the expected answer JSON
object.

## Background

After running `spec assess`, the session's `_session.json` stores a list of
questions that must be answered before the spec can be completed. Currently, to
create the answers file a user must manually read `_session.json`, find the
questions array, and construct a `{"q1": "...", "q2": "..."}` JSON object. This
is error-prone and inconvenient, especially for automation agents.

## Requirements

1. When `spec refine <spec>` is invoked **without** the `--answers` option,
   the CLI SHALL output JSON to stdout containing all questions from the latest
   assessment in the session, along with a pre-filled answer template.

2. The JSON output SHALL include full question details (id, text, context,
   options, required flag) so that the consumer has enough information to
   formulate answers.

3. The JSON output SHALL include an `answers` key containing a dict mapping
   each question ID to an empty string, which the user can fill in and pass
   back via `--answers`.

4. When `spec refine <spec> --answers <file>` is invoked (existing
   behavior), the CLI SHALL continue to work exactly as before.

5. When there is no assessment in the session (no questions to export), the
   CLI SHALL print an error and exit with code 1.

6. The session library SHALL expose a `pending_questions()` method that returns
   the questions from the latest assessment as a serializable data structure.

## Design Decisions

1. The output format is a JSON object with two top-level keys: `questions`
   (array of full question objects) and `answers` (dict template). This lets
   agents read `questions` for context and extract `answers` as a ready-to-fill
   template.

2. The `--answers` option remains optional at the Click level
   (`required=False`). The two behaviors (question export vs. answer
   submission) are distinguished by the presence or absence of `--answers`.

3. The `pending_questions()` method lives on `SpecSession` because the session
   owns the assessment history. It does not require a state transition -- it is
   a read-only query.

## Non-Goals

- Changing the answer submission flow (`--answers` path).
- Auto-answering questions from options.
- Interactive prompting for answers.

## Source

Source: Input provided by user via interactive prompt.
