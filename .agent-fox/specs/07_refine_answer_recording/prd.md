# PRD: Record Answers in Session During Refinement

## Intent

Persist the answers provided via `spec refine --answers` into
`_session.json` so that the full assess-refine-accept interaction
history is recorded and auditable.

## Background

The `spec` tool implements an iterative refinement loop:

1. `assess` — agent evaluates the PRD, produces questions.
2. `refine --answers` — user provides answers, agent updates PRD and
   re-assesses.
3. Repeat step 2 until quality is "ready".
4. `accept` — user accepts the PRD.

Currently, `_session.json` records each assessment (quality, summary, gaps,
questions) in `assessment_history`, but the answers the user provided between
assessments are discarded. The `qa_exchanges` field was specced in
02-REQ-5.3 and is already present in the persistence schema, but it is never
written to.

This means there is no record of *why* the PRD changed between assessment
rounds. If a user or agent wants to review the decision trail, or replay the
refinement, the answers are lost.

## Requirements

1. When `session.refine(answers)` is called, the session SHALL append the
   provided answers dict to `qa_exchanges` in `_session.json` before
   persisting the new state.

2. Each entry in `qa_exchanges` SHALL record which assessment the answers
   correspond to (by assessment index), the answers dict, and a timestamp.

3. The `pending_questions()` method and question-export JSON output SHALL
   remain unchanged — answers are recorded, not surfaced in the export.

4. Existing sessions with empty `qa_exchanges` SHALL continue to load and
   function without migration.

## Design Decisions

1. **Use existing `qa_exchanges` field.** The field was specced in 02-REQ-5.3
   and already exists in `_session.json`. No schema migration is needed — we
   simply populate it.

2. **Each exchange entry links to its assessment index.** The
   `assessment_index` field records which entry in `assessment_history` the
   answers respond to (i.e., the index of the assessment whose questions were
   answered). This creates a clear pairing: assessment N's questions are
   answered by qa_exchanges entry M where `assessment_index == N`.

3. **Timestamp is ISO 8601 UTC.** Provides a human-readable audit trail
   without timezone ambiguity.

## Non-Goals

- Modifying the CLI interface (no new flags or options).
- Changing the assessment or agent API.
- Adding answer validation beyond what already exists in `SpecAgent.refine_prd`.

## Dependencies

| Spec | From Group | To Group | Relationship |
|------|-----------|----------|--------------|
| 02_campaign_session | 5 | 2 | Uses `_persist()` and `qa_exchanges` field from group 5; group 5 defines the persistence schema |

## Source

Source: Input provided by user via interactive prompt.
