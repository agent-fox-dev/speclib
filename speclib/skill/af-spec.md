# af-spec — Spec Authoring Skill

A skill for agent CLIs (Claude Code, Gemini CLI) that guides spec authoring
workflows using the `af-spec` command-line tool. This skill enables both
interactive step-by-step spec creation and one-shot generation from a PRD.

## Trigger

Activate this skill when the user:

- Asks to create, author, or write a specification
- Mentions "spec", "PRD", or "requirements document" authoring
- Wants to refine or assess a product requirements document
- Requests help with the `af-spec` tool

If a referenced command is not available or not supported in the current
`af-spec` version, inform the user and report which command is unsupported
rather than failing silently.

## Command Reference

All commands are invoked as `af-spec <command> [options] [arguments]`.
Before running any command, use `af-spec status` to check the current
session state and avoid illegal state transitions.

### af-spec init

Create a new campaign working directory.

```bash
af-spec init ./my-campaign --name "Project Alpha"
```

**Expected output:** Confirmation message with the created campaign path.

### af-spec new

Create a new spec from a PRD file.

```bash
af-spec new ./prd.md --name my_feature
```

For one-shot mode (skip interactive refinement):

```bash
af-spec new ./prd.md --one-shot --name my_feature
```

**Expected output:** Confirmation with the created spec directory name.

### af-spec assess

Run or re-run PRD assessment on a spec. Produces a quality summary,
suggestions for improvement, and questions for the author.

```bash
af-spec assess my_feature
```

**Expected output:** Quality rating, summary, gaps, and numbered questions
with Question IDs (e.g., `Q1`, `Q2`).

### af-spec refine

Submit answers to assessment questions and update the PRD. Requires a JSON
file mapping Question IDs to answer text.

```bash
af-spec refine my_feature --answers answers.json
```

The `--answers` flag accepts a path to a JSON file containing a mapping of
Question ID to answer text, for example:

```json
{"Q1": "The target audience is enterprise developers.", "Q2": "We need OAuth2 support."}
```

**Expected output:** Updated assessment with new quality rating.

### af-spec accept

Accept the PRD, ending the refinement loop and locking the document.

```bash
af-spec accept my_feature
```

**Expected output:** Confirmation that the PRD is accepted with new state.

### af-spec generate

Generate specification artifacts (requirements, design, test spec, tasks)
from the accepted PRD.

```bash
af-spec generate my_feature
```

**Expected output:** List of generated artifact files.

### af-spec status

Print session state for a spec or list all specs in the campaign.

```bash
af-spec status my_feature
```

List all specs:

```bash
af-spec status
```

**Expected output:** Spec name, current state, mode, assessment count, and
artifact list.

### af-spec validate

Run schema and cross-file validation checks on generated artifacts.

```bash
af-spec validate my_feature
```

**Expected output:** "Validation passed" or a table of validation errors
with file, path, and message columns.

### af-spec render

Render spec artifacts as markdown for review.

```bash
af-spec render my_feature
```

Render as a single combined document:

```bash
af-spec render my_feature --combined
```

**Expected output:** Rendered markdown content of all spec artifacts.

## Interactive Workflow

Follow these numbered steps for interactive spec authoring:

1. **Open or create campaign.** If no campaign exists, create one with
   `af-spec init <path>`. Otherwise, navigate to the existing campaign
   directory.

2. **Create a new spec from a PRD.** Run `af-spec new --prd <path> <name>`
   to start a new spec session in interactive mode.

3. **Run assessment.** Execute `af-spec assess <spec>` to evaluate the PRD
   quality.

4. **Present assessment to user.** After running the assessment, present the
   full assessment result to the user in a readable format — including the
   quality rating, summary, identified gaps, and all questions.

5. **Present questions to user.** Parse the question output, extracting each
   Question ID (e.g., `Q1`, `Q2`) and its text. Present questions to the
   user in natural language, numbering them for readability but omitting
   internal Question IDs from the user-facing presentation.

6. **Collect answers.** Accept user answers in natural language — full
   sentences, partial answers, or grouped responses to multiple questions.
   Map each answer back to its corresponding Question ID.

7. **Refine the PRD.** Pass the mapped answers to `af-spec refine <spec>
   --answers <file>` using a JSON file that maps Question IDs to answer
   text.

8. **Repeat or accept.** After each refinement round, ask the user whether
   to accept the PRD or continue refining. If the user wants to continue,
   go back to step 3 (re-assess). If satisfied, proceed to step 9.

9. **Accept the PRD.** Run `af-spec accept <spec>` to lock the PRD.

10. **Generate the spec.** Run `af-spec generate <spec>` to produce the
    full specification artifacts. Present the generated artifacts to the
    user for review.

### Zero-Questions Case

If the assessment produces no questions (all requirements are clear), inform
the user that the PRD is ready and proceed directly to the accept step.

## One-Shot Workflow

For immediate spec generation without interactive refinement:

1. Run `af-spec new <prd-file> --one-shot --name <spec-name>`. This
   automatically runs assess, accept, and generate in a single pass.

2. After one-shot generation completes, present the final generated spec
   to the user for review.

### One-Shot Failure

If one-shot generation fails (non-zero exit code from any step), report the
error to the user and suggest falling back to interactive mode for
step-by-step refinement.

## Question Handling

### Parsing Questions

After running `af-spec assess`, parse the output to extract each question's
ID and text. Questions appear in the format:

```
Q1: What is the target audience?
Q2: Are there performance requirements?
```

### Presenting Questions

Present questions to the user in a conversational, natural language style.
Number them for reference but omit the internal Question IDs:

> Here are some questions about your PRD:
>
> 1. What is the target audience for this feature?
> 2. Are there specific performance requirements?

### Mapping Answers

When the user provides answers:

1. Match each answer to its corresponding Question ID based on the
   question number or contextual relevance.
2. If an answer cannot be clearly mapped to any question, ask for
   clarification about which question the user is addressing.
3. If the user answers only some questions, pass the partial answers to
   `af-spec refine` and note which questions remain unanswered.
4. Format the answer mapping as JSON and pass it via the `--answers` flag.

## Error Handling

### Common Error Conditions

| Error | Recovery |
|-------|----------|
| `af-spec` is not found on PATH | Tell the user to install speclib (`uv pip install speclib`) and retry. |
| Campaign directory not found | Run `af-spec init <path>` to create a new campaign. |
| Spec not found | Check available specs with `af-spec status` or `af-spec list`. |
| Invalid state transition | Use `af-spec status <spec>` to check the current state before retrying. |
| Assessment failed | Check stderr output and retry `af-spec assess`. |
| JSON parse error in answers | Verify the answers file contains valid JSON. |

### Exit Code Checking

After every `af-spec` command invocation, check the exit code to determine
success or failure:

- **Exit code 0:** Command succeeded. Proceed with the workflow.
- **Non-zero exit code:** Command failed. Read the stderr output and report
  the error to the user with the full error message.

### State Verification

Before attempting any operation, run `af-spec status` to check the current
session state. This prevents illegal state transitions such as:

- Running `accept` before `assess`
- Running `generate` before `accept`
- Running `refine` when the PRD is already accepted
