# Test Specification: Agent Pipeline

## Overview

Tests validate the agent pipeline: PRD assessment, PRD refinement, artifact
generation, prompt templates, tool definitions, retry logic, and session
integration. All agent tests use a mocked Anthropic client to avoid real API
calls. Property tests verify invariants on assessment quality, question
presence, generation order, and retry bounds.

## Test Cases

### TS-03-1: assess_prd returns Assessment with valid quality

**Requirement:** 03-REQ-1.1, 03-REQ-1.2
**Type:** unit
**Description:** Verify assess_prd sends the PRD to the API and returns an Assessment with a valid quality value.

**Preconditions:**
- Mocked Anthropic client returning a tool_use response with submit_assessment
- Tool input contains quality="needs_refinement"

**Input:**
- Call assess_prd("# My PRD\n\n## Intent\nDo things.", "my_spec")

**Expected:**
- Returns Assessment with quality="needs_refinement"
- Mock client.messages.create was called once
- System message contains assessment instructions

**Assertion pseudocode:**
```
mock_client = mock_anthropic_with_assessment(quality="needs_refinement", summary="Needs work", gaps=["Missing Goals"], questions=[q1])
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
result = await agent.assess_prd("# My PRD\n\n## Intent\nDo things.", "my_spec")
ASSERT result.quality == "needs_refinement"
ASSERT isinstance(result, Assessment)
ASSERT mock_client.messages.create.call_count == 1
```

### TS-03-2: Assessment contains summary

**Requirement:** 03-REQ-1.3
**Type:** unit
**Description:** Verify the returned Assessment has a non-empty summary.

**Preconditions:**
- Mocked client returning assessment with summary="The PRD is incomplete."

**Input:**
- Call assess_prd with valid PRD text

**Expected:**
- result.summary == "The PRD is incomplete."
- len(result.summary) > 0

**Assertion pseudocode:**
```
mock_client = mock_anthropic_with_assessment(summary="The PRD is incomplete.")
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
result = await agent.assess_prd("# PRD content", "test_spec")
ASSERT result.summary == "The PRD is incomplete."
ASSERT len(result.summary) > 0
```

### TS-03-3: Assessment contains gaps list

**Requirement:** 03-REQ-1.4
**Type:** unit
**Description:** Verify the returned Assessment has a gaps list.

**Preconditions:**
- Mocked client returning assessment with gaps=["No Goals section", "Background is vague"]

**Input:**
- Call assess_prd with valid PRD text

**Expected:**
- result.gaps == ["No Goals section", "Background is vague"]

**Assertion pseudocode:**
```
mock_client = mock_anthropic_with_assessment(gaps=["No Goals section", "Background is vague"])
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
result = await agent.assess_prd("# PRD content", "test_spec")
ASSERT result.gaps == ["No Goals section", "Background is vague"]
```

### TS-03-4: Non-ready assessment has questions

**Requirement:** 03-REQ-1.5
**Type:** unit
**Description:** Verify that when quality is not "ready", questions is non-empty.

**Preconditions:**
- Mocked client returning assessment with quality="needs_refinement" and questions=[q1, q2]

**Input:**
- Call assess_prd with valid PRD text

**Expected:**
- len(result.questions) > 0
- Each question has id, text, context, options, required

**Assertion pseudocode:**
```
q1 = {"id": "q1", "text": "What are the goals?", "context": "Goals section is missing", "options": [], "required": True}
mock_client = mock_anthropic_with_assessment(quality="needs_refinement", questions=[q1])
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
result = await agent.assess_prd("# PRD", "test_spec")
ASSERT len(result.questions) > 0
ASSERT result.questions[0].id == "q1"
ASSERT result.questions[0].text == "What are the goals?"
ASSERT result.questions[0].required is True
```

### TS-03-5: Ready assessment may have empty questions

**Requirement:** 03-REQ-1.6
**Type:** unit
**Description:** Verify that when quality is "ready", an empty questions list is valid.

**Preconditions:**
- Mocked client returning assessment with quality="ready" and questions=[]

**Input:**
- Call assess_prd with valid PRD text

**Expected:**
- result.quality == "ready"
- result.questions == []

**Assertion pseudocode:**
```
mock_client = mock_anthropic_with_assessment(quality="ready", questions=[])
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
result = await agent.assess_prd("# PRD\n## Intent\n## Goals\n## Non-Goals\n## Background", "test_spec")
ASSERT result.quality == "ready"
ASSERT result.questions == []
```

### TS-03-6: refine_prd returns updated PRD and new assessment

**Requirement:** 03-REQ-2.1, 03-REQ-2.2
**Type:** unit
**Description:** Verify refine_prd sends answers and returns an updated PRD with a new assessment.

**Preconditions:**
- Mocked client returning both submit_prd_update and submit_assessment tool calls
- Previous assessment with questions [q1]

**Input:**
- Call refine_prd(prd_text, {"q1": "Build a REST API"}, previous_assessment)

**Expected:**
- Returns (updated_prd_text, new_assessment)
- updated_prd_text is a non-empty string
- new_assessment is a valid Assessment

**Assertion pseudocode:**
```
prev = Assessment(quality="needs_refinement", summary="Needs goals", gaps=["No goals"], questions=[q1])
mock_client = mock_anthropic_with_refinement(updated_prd="# Updated PRD\n## Goals\n1. Build REST API", quality="ready")
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
updated, assessment = await agent.refine_prd("# Original PRD", {"q1": "Build a REST API"}, prev)
ASSERT "REST API" in updated
ASSERT isinstance(assessment, Assessment)
ASSERT assessment.quality == "ready"
```

### TS-03-7: refine_prd answers dict maps question IDs to strings

**Requirement:** 03-REQ-2.3
**Type:** unit
**Description:** Verify the answers parameter is a dict[str, str].

**Preconditions:**
- Valid previous assessment with questions [q1, q2]

**Input:**
- Call refine_prd with answers={"q1": "Answer 1", "q2": "Answer 2"}

**Expected:**
- The user message sent to the API contains both question IDs and answers

**Assertion pseudocode:**
```
prev = Assessment(quality="needs_refinement", summary="", gaps=[], questions=[q1, q2])
mock_client = mock_anthropic_with_refinement(updated_prd="Updated", quality="ready")
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
await agent.refine_prd("# PRD", {"q1": "A1", "q2": "A2"}, prev)
call_args = mock_client.messages.create.call_args
user_msg = call_args.kwargs["messages"][-1]["content"]
ASSERT "q1" in user_msg and "A1" in user_msg
ASSERT "q2" in user_msg and "A2" in user_msg
```

### TS-03-8: refine_prd preserves frontmatter

**Requirement:** 03-REQ-2.4
**Type:** unit
**Description:** Verify the updated PRD preserves frontmatter.

**Preconditions:**
- Mocked client returning submit_prd_update with body-only content

**Input:**
- Call refine_prd with a PRD that has frontmatter

**Expected:**
- The refinement prompt instructs the model to return body-only content
- The submit_prd_update tool schema describes body-only content

**Assertion pseudocode:**
```
mock_client = mock_anthropic_with_refinement(updated_prd="## Intent\nUpdated body", quality="ready")
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
updated, _ = await agent.refine_prd("---\nspec_id: 01\n---\n## Intent\nOriginal", {"q1": "answer"}, prev)
ASSERT "Updated body" in updated
# The caller (SpecSession) is responsible for re-attaching frontmatter
```

### TS-03-9: generate_artifacts produces three artifacts in order

**Requirement:** 03-REQ-3.1, 03-REQ-3.2
**Type:** unit
**Description:** Verify generate_artifacts makes three API calls and returns all three artifacts.

**Preconditions:**
- Mocked client returning valid submit_artifact tool calls for each artifact

**Input:**
- Call generate_artifacts("# Accepted PRD", "03", "agent_pipeline")

**Expected:**
- Three API calls made (one per artifact)
- Returns dict with keys "requirements", "test_spec", "tasks"

**Assertion pseudocode:**
```
mock_client = mock_anthropic_sequential_artifacts(req_json, test_json, task_json)
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
result = await agent.generate_artifacts("# Accepted PRD", "03", "agent_pipeline")
ASSERT set(result.keys()) == {"requirements", "test_spec", "tasks"}
ASSERT mock_client.messages.create.call_count == 3
```

### TS-03-10: generate_artifacts returns parsed JSON content

**Requirement:** 03-REQ-3.3
**Type:** unit
**Description:** Verify each artifact value is parsed JSON (dict), not a raw string.

**Preconditions:**
- Mocked client returning valid artifact JSON

**Input:**
- Call generate_artifacts with valid PRD

**Expected:**
- Each value in the returned dict is a dict (parsed JSON)

**Assertion pseudocode:**
```
result = await agent.generate_artifacts("# PRD", "03", "test")
for name, content in result.items():
    ASSERT isinstance(content, dict)
```

### TS-03-11: Each artifact validated before next generation

**Requirement:** 03-REQ-3.4
**Type:** unit
**Description:** Verify each artifact is validated against its schema before the next is generated.

**Preconditions:**
- Mocked client returning artifacts sequentially
- Mocked afspec.validate_artifact

**Input:**
- Call generate_artifacts

**Expected:**
- validate_artifact called after each artifact generation, before the next API call
- Call order: generate req -> validate req -> generate test -> validate test -> generate tasks -> validate tasks

**Assertion pseudocode:**
```
call_log = []
mock_validate = Mock(side_effect=lambda name, content: call_log.append(("validate", name)))
mock_client = mock_sequential(side_effect=lambda **kw: call_log.append(("generate", extract_artifact_name(kw))))
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with patch("afspec.validate_artifact", mock_validate):
    await agent.generate_artifacts("# PRD", "03", "test")
ASSERT call_log == [
    ("generate", "requirements"), ("validate", "requirements"),
    ("generate", "test_spec"), ("validate", "test_spec"),
    ("generate", "tasks"), ("validate", "tasks"),
]
```

### TS-03-12: Validation failure aborts generation

**Requirement:** 03-REQ-3.5
**Type:** unit
**Description:** Verify generation stops and raises AgentError if an artifact fails validation.

**Preconditions:**
- Mocked client returning requirements artifact
- Mocked afspec validation that rejects requirements

**Input:**
- Call generate_artifacts

**Expected:**
- AgentError raised after first artifact
- Only one API call made (requirements only)

**Assertion pseudocode:**
```
mock_client = mock_sequential_artifacts(req_json, test_json, task_json)
mock_validate = Mock(side_effect=ValidationError("schema mismatch"))
with patch("afspec.validate_artifact", mock_validate):
    ASSERT raises(AgentError, agent.generate_artifacts, "# PRD", "03", "test")
ASSERT mock_client.messages.create.call_count == 1
```

### TS-03-13: test_spec generation includes requirements context

**Requirement:** 03-REQ-3.6
**Type:** unit
**Description:** Verify the test_spec generation prompt includes the generated requirements.

**Preconditions:**
- Mocked client returning sequential artifacts

**Input:**
- Call generate_artifacts

**Expected:**
- The second API call's user message contains the requirements JSON content

**Assertion pseudocode:**
```
await agent.generate_artifacts("# PRD", "03", "test")
second_call = mock_client.messages.create.call_args_list[1]
user_msg = second_call.kwargs["messages"][-1]["content"]
ASSERT "requirements" in user_msg  # contains prior artifact
```

### TS-03-14: tasks generation includes requirements and test_spec context

**Requirement:** 03-REQ-3.7
**Type:** unit
**Description:** Verify the tasks generation prompt includes both prior artifacts.

**Preconditions:**
- Mocked client returning sequential artifacts

**Input:**
- Call generate_artifacts

**Expected:**
- The third API call's user message contains both requirements and test_spec content

**Assertion pseudocode:**
```
await agent.generate_artifacts("# PRD", "03", "test")
third_call = mock_client.messages.create.call_args_list[2]
user_msg = third_call.kwargs["messages"][-1]["content"]
ASSERT "requirements" in user_msg
ASSERT "test_spec" in user_msg
```

### TS-03-15: Assessment prompt template content

**Requirement:** 03-REQ-4.1
**Type:** unit
**Description:** Verify the assessment system prompt references spec-format expectations.

**Preconditions:**
- None

**Input:**
- Call assessment_system_prompt()

**Expected:**
- Returns non-empty string
- Contains references to PRD sections (Intent, Goals, Non-Goals, Background)

**Assertion pseudocode:**
```
prompt = assessment_system_prompt()
ASSERT len(prompt) > 0
ASSERT "Intent" in prompt
ASSERT "Goals" in prompt
ASSERT "Non-Goals" in prompt
ASSERT "Background" in prompt
```

### TS-03-16: Refinement prompt template content

**Requirement:** 03-REQ-4.2
**Type:** unit
**Description:** Verify the refinement system prompt instructs the model to incorporate answers and re-assess.

**Preconditions:**
- None

**Input:**
- Call refinement_system_prompt()

**Expected:**
- Returns non-empty string
- Contains instructions about incorporating answers and updating the PRD

**Assertion pseudocode:**
```
prompt = refinement_system_prompt()
ASSERT len(prompt) > 0
ASSERT "answer" in prompt.lower() or "incorporate" in prompt.lower()
ASSERT "assess" in prompt.lower() or "evaluat" in prompt.lower()
```

### TS-03-17: Generation prompt template content

**Requirement:** 03-REQ-4.3
**Type:** unit
**Description:** Verify the generation system prompt instructs the model to produce a single artifact.

**Preconditions:**
- None

**Input:**
- Call generation_system_prompt()

**Expected:**
- Returns non-empty string
- Contains instructions about JSON schema compliance

**Assertion pseudocode:**
```
prompt = generation_system_prompt()
ASSERT len(prompt) > 0
ASSERT "json" in prompt.lower() or "schema" in prompt.lower()
ASSERT "artifact" in prompt.lower()
```

### TS-03-18: Assessment tool definition structure

**Requirement:** 03-REQ-4.4, 03-REQ-4.5, 03-REQ-4.6
**Type:** unit
**Description:** Verify the submit_assessment tool has correct name, description, and input_schema.

**Preconditions:**
- None

**Input:**
- Call assessment_tools()

**Expected:**
- Returns a list with one tool definition
- Tool has name="submit_assessment"
- input_schema enforces quality enum, summary, gaps, questions

**Assertion pseudocode:**
```
tools = assessment_tools()
ASSERT len(tools) == 1
tool = tools[0]
ASSERT tool["name"] == "submit_assessment"
ASSERT "description" in tool
schema = tool["input_schema"]
ASSERT schema["type"] == "object"
ASSERT "quality" in schema["properties"]
ASSERT schema["properties"]["quality"]["enum"] == ["ready", "needs_refinement", "incomplete"]
ASSERT "summary" in schema["properties"]
ASSERT "gaps" in schema["properties"]
ASSERT "questions" in schema["properties"]
ASSERT set(schema["required"]) == {"quality", "summary", "gaps", "questions"}
```

### TS-03-19: Refinement tool definitions structure

**Requirement:** 03-REQ-4.4, 03-REQ-4.5
**Type:** unit
**Description:** Verify refinement tools include both submit_prd_update and submit_assessment.

**Preconditions:**
- None

**Input:**
- Call refinement_tools()

**Expected:**
- Returns a list with two tool definitions
- One has name="submit_prd_update" with updated_prd field
- One has name="submit_assessment"

**Assertion pseudocode:**
```
tools = refinement_tools()
ASSERT len(tools) == 2
names = {t["name"] for t in tools}
ASSERT names == {"submit_prd_update", "submit_assessment"}
update_tool = next(t for t in tools if t["name"] == "submit_prd_update")
ASSERT "updated_prd" in update_tool["input_schema"]["properties"]
```

### TS-03-20: Artifact tool definition structure

**Requirement:** 03-REQ-4.4, 03-REQ-4.5
**Type:** unit
**Description:** Verify the submit_artifact tool has correct structure.

**Preconditions:**
- None

**Input:**
- Call artifact_tool("requirements")

**Expected:**
- Returns a list with one tool definition
- Tool has name="submit_artifact"
- input_schema has artifact_name and content fields

**Assertion pseudocode:**
```
tools = artifact_tool("requirements")
ASSERT len(tools) == 1
tool = tools[0]
ASSERT tool["name"] == "submit_artifact"
schema = tool["input_schema"]
ASSERT "artifact_name" in schema["properties"]
ASSERT "content" in schema["properties"]
```

### TS-03-21: Retry on 429 with exponential backoff

**Requirement:** 03-REQ-5.1
**Type:** unit
**Description:** Verify the agent retries on HTTP 429 with increasing delays.

**Preconditions:**
- Mocked client that raises RateLimitError on first two calls, succeeds on third

**Input:**
- Call _call_api with messages and tools

**Expected:**
- Three calls made total
- Delays between calls follow exponential backoff (1s, 2s)
- Third call succeeds and returns response

**Assertion pseudocode:**
```
mock_client = Mock()
mock_client.messages.create = AsyncMock(
    side_effect=[RateLimitError(), RateLimitError(), valid_response]
)
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with patch("asyncio.sleep") as mock_sleep:
    result = await agent._call_api(messages, tools)
ASSERT mock_client.messages.create.call_count == 3
ASSERT mock_sleep.call_args_list[0] == call(1.0)
ASSERT mock_sleep.call_args_list[1] == call(2.0)
```

### TS-03-22: Retry on 5xx server error

**Requirement:** 03-REQ-5.1
**Type:** unit
**Description:** Verify the agent retries on 5xx server errors.

**Preconditions:**
- Mocked client raising InternalServerError on first call, succeeds on second

**Input:**
- Call _call_api

**Expected:**
- Two calls made total, second succeeds

**Assertion pseudocode:**
```
mock_client.messages.create = AsyncMock(
    side_effect=[InternalServerError(), valid_response]
)
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
result = await agent._call_api(messages, tools)
ASSERT mock_client.messages.create.call_count == 2
```

### TS-03-23: AgentError after retry exhaustion

**Requirement:** 03-REQ-5.2
**Type:** unit
**Description:** Verify AgentError is raised after all retries are exhausted.

**Preconditions:**
- Mocked client raising RateLimitError on all calls

**Input:**
- Call _call_api

**Expected:**
- AgentError raised after 4 total attempts (1 initial + 3 retries)
- Original error is set as __cause__

**Assertion pseudocode:**
```
mock_client.messages.create = AsyncMock(side_effect=RateLimitError())
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with pytest.raises(AgentError) as exc_info:
    await agent._call_api(messages, tools)
ASSERT mock_client.messages.create.call_count == 4
ASSERT exc_info.value.__cause__ is not None
```

### TS-03-24: No retry on 4xx (non-429)

**Requirement:** 03-REQ-5.3
**Type:** unit
**Description:** Verify the agent raises AgentError immediately on 4xx errors other than 429.

**Preconditions:**
- Mocked client raising BadRequestError (400)

**Input:**
- Call _call_api

**Expected:**
- AgentError raised immediately
- Only one API call made

**Assertion pseudocode:**
```
mock_client.messages.create = AsyncMock(side_effect=BadRequestError())
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with pytest.raises(AgentError):
    await agent._call_api(messages, tools)
ASSERT mock_client.messages.create.call_count == 1
```

### TS-03-25: AgentError inherits SpeclibError

**Requirement:** 03-REQ-5.4
**Type:** unit
**Description:** Verify AgentError is a subclass of SpeclibError with __cause__ support.

**Preconditions:**
- None

**Input:**
- Import and inspect AgentError

**Expected:**
- issubclass(AgentError, SpeclibError)
- AgentError can be raised with a cause

**Assertion pseudocode:**
```
from speclib.errors import AgentError, SpeclibError
ASSERT issubclass(AgentError, SpeclibError)
original = ValueError("bad response")
err = AgentError("parsing failed")
err.__cause__ = original
ASSERT err.__cause__ is original
```

### TS-03-26: AgentError on unparseable response

**Requirement:** 03-REQ-5.5
**Type:** unit
**Description:** Verify AgentError is raised when the response cannot be parsed.

**Preconditions:**
- Mocked client returning a text-only response (no tool_use blocks)

**Input:**
- Call assess_prd

**Expected:**
- AgentError raised with parsing failure details

**Assertion pseudocode:**
```
mock_client = mock_anthropic_text_only("I don't know how to use tools")
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with pytest.raises(AgentError, match="structured output"):
    await agent.assess_prd("# PRD", "test")
```

### TS-03-27: Session assess delegates to SpecAgent

**Requirement:** 03-REQ-6.1
**Type:** unit
**Description:** Verify SpecSession.assess() creates a SpecAgent, calls assess_prd, and persists the result.

**Preconditions:**
- SpecSession in "init" state with a PRD file
- Mocked create_client and SpecAgent

**Input:**
- Call session.assess()

**Expected:**
- SpecAgent.assess_prd was called with the PRD text
- Assessment persisted to _session.json
- Session state transitioned to "assessing"

**Assertion pseudocode:**
```
session = create_test_session(state="init", prd="# My PRD")
with patch("speclib.agent.SpecAgent") as MockAgent:
    mock_agent = MockAgent.return_value
    mock_agent.assess_prd = AsyncMock(return_value=assessment)
    await session.assess()
mock_agent.assess_prd.assert_called_once_with("# My PRD", "test_spec")
ASSERT session.state == SessionState.ASSESSING
session_data = json.loads(session.spec_dir / "_session.json").read_text())
ASSERT len(session_data["assessment_history"]) == 1
```

### TS-03-28: Session refine delegates to SpecAgent

**Requirement:** 03-REQ-6.2
**Type:** unit
**Description:** Verify SpecSession.refine() calls SpecAgent.refine_prd, updates PRD file, and persists.

**Preconditions:**
- SpecSession in "assessing" or "refining" state with a previous Assessment

**Input:**
- Call session.refine({"q1": "My answer"})

**Expected:**
- SpecAgent.refine_prd was called with correct arguments
- prd.md updated with returned text
- New Assessment persisted to _session.json

**Assertion pseudocode:**
```
session = create_test_session(state="assessing", assessment=prev_assessment)
with patch("speclib.agent.SpecAgent") as MockAgent:
    mock_agent = MockAgent.return_value
    mock_agent.refine_prd = AsyncMock(return_value=("# Updated", new_assessment))
    await session.refine({"q1": "My answer"})
mock_agent.refine_prd.assert_called_once()
prd_content = (session.spec_dir / "prd.md").read_text()
ASSERT "Updated" in prd_content
```

### TS-03-29: Session generate delegates to SpecAgent and writes files

**Requirement:** 03-REQ-6.3
**Type:** unit
**Description:** Verify SpecSession.generate() calls generate_artifacts, writes files, and validates.

**Preconditions:**
- SpecSession in "prd_accepted" state

**Input:**
- Call session.generate()

**Expected:**
- SpecAgent.generate_artifacts was called
- requirements.json, test_spec.json, tasks.json written to spec directory
- Cross-file validation run via afspec
- Session state transitioned to "generated"

**Assertion pseudocode:**
```
session = create_test_session(state="prd_accepted")
artifacts = {"requirements": req_json, "test_spec": test_json, "tasks": task_json}
with patch("speclib.agent.SpecAgent") as MockAgent:
    mock_agent = MockAgent.return_value
    mock_agent.generate_artifacts = AsyncMock(return_value=artifacts)
    await session.generate()
ASSERT (session.spec_dir / "requirements.json").exists()
ASSERT (session.spec_dir / "test_spec.json").exists()
ASSERT (session.spec_dir / "tasks.json").exists()
ASSERT session.state == SessionState.GENERATED
```

### TS-03-30: Agent error prevents session state transition

**Requirement:** 03-REQ-6.4
**Type:** unit
**Description:** Verify that AgentError during a session operation prevents state transition.

**Preconditions:**
- SpecSession in "init" state
- SpecAgent.assess_prd raises AgentError

**Input:**
- Call session.assess()

**Expected:**
- AgentError is re-raised
- Session state remains "init"
- Error is persisted in _session.json

**Assertion pseudocode:**
```
session = create_test_session(state="init")
with patch("speclib.agent.SpecAgent") as MockAgent:
    mock_agent = MockAgent.return_value
    mock_agent.assess_prd = AsyncMock(side_effect=AgentError("API failed"))
    with pytest.raises(AgentError):
        await session.assess()
ASSERT session.state == SessionState.INIT
```

### TS-03-31: Assessment history accumulates

**Requirement:** 03-REQ-6.5
**Type:** unit
**Description:** Verify each assess/refine call appends to assessment_history.

**Preconditions:**
- SpecSession with one existing Assessment in history

**Input:**
- Call session.assess() then session.refine() (or equivalent)

**Expected:**
- assessment_history length increases by one for each call

**Assertion pseudocode:**
```
session = create_test_session(state="init")
# First assessment
await session.assess()
ASSERT len(session.assessment_history) == 1
# Refinement adds another
await session.refine({"q1": "answer"})
ASSERT len(session.assessment_history) == 2
```

### TS-03-32: Generation prompt includes glossary instruction

**Requirement:** 03-REQ-3.8
**Type:** unit
**Description:** Verify the generation prompt for requirements instructs the agent to populate the glossary.

**Preconditions:**
- None

**Input:**
- Call generation_user_prompt with artifact_name="requirements"

**Expected:**
- Prompt text contains instruction about populating glossary with backtick-wrapped domain terms

**Assertion pseudocode:**
```
prompt = generation_user_prompt(prd_text="test", artifact_name="requirements", prior_artifacts={})
ASSERT "glossary" in prompt.lower()
ASSERT "backtick" in prompt.lower() or "domain" in prompt.lower()
```

## Property Test Cases

### TS-03-P1: Assessment quality enum is valid

**Property:** Property 1 from design.md
**Validates:** 03-REQ-1.2
**Type:** property
**Description:** For any valid response from the agent, the quality field is always one of the three valid enum values.

**For any:** tool_input dict with quality in {"ready", "needs_refinement", "incomplete"}
**Invariant:** _parse_assessment succeeds; for any quality not in the enum, _parse_assessment raises AgentError

**Assertion pseudocode:**
```
FOR ANY quality IN sampled_from(["ready", "needs_refinement", "incomplete"]):
    tool_input = {"quality": quality, "summary": "ok", "gaps": [], "questions": []}
    assessment = agent._parse_assessment(tool_input)
    ASSERT assessment.quality == quality

FOR ANY quality IN text(min_size=1).filter(lambda q: q not in ["ready", "needs_refinement", "incomplete"]):
    tool_input = {"quality": quality, "summary": "ok", "gaps": [], "questions": []}
    ASSERT raises(AgentError, agent._parse_assessment, tool_input)
```

### TS-03-P2: Non-ready assessments have questions

**Property:** Property 2 from design.md
**Validates:** 03-REQ-1.5
**Type:** property
**Description:** For any Assessment where quality is not "ready", the questions list is non-empty.

**For any:** quality in {"needs_refinement", "incomplete"}
**Invariant:** len(questions) > 0

**Assertion pseudocode:**
```
FOR ANY quality IN sampled_from(["needs_refinement", "incomplete"]):
    FOR ANY questions IN lists(question_strategy, min_size=1):
        tool_input = {"quality": quality, "summary": "s", "gaps": [], "questions": questions}
        assessment = agent._parse_assessment(tool_input)
        ASSERT len(assessment.questions) > 0

# Also verify that empty questions with non-ready quality is rejected
FOR ANY quality IN sampled_from(["needs_refinement", "incomplete"]):
    tool_input = {"quality": quality, "summary": "s", "gaps": [], "questions": []}
    ASSERT raises(AgentError, agent._parse_assessment, tool_input)
```

### TS-03-P3: Artifact generation order is deterministic

**Property:** Property 3 from design.md
**Validates:** 03-REQ-3.1, 03-REQ-3.6, 03-REQ-3.7
**Type:** property
**Description:** For any invocation, artifacts are always generated in the order requirements, test_spec, tasks.

**For any:** valid PRD text, spec_id, spec_name
**Invariant:** API calls are made in the fixed order; each subsequent call includes prior artifacts

**Assertion pseudocode:**
```
FOR ANY prd_text IN text(min_size=10):
    call_order = []
    mock_client = mock_sequential(record_order=call_order)
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    await agent.generate_artifacts(prd_text, "03", "test")
    ASSERT call_order == ["requirements", "test_spec", "tasks"]
```

### TS-03-P4: Retry count is bounded

**Property:** Property 4 from design.md
**Validates:** 03-REQ-5.1, 03-REQ-5.E2
**Type:** property
**Description:** For any sequence of transient errors, the total number of attempts never exceeds 4 (1 initial + 3 retries).

**For any:** number of consecutive transient errors N
**Invariant:** call_count <= 4

**Assertion pseudocode:**
```
FOR ANY n_errors IN integers(min_value=1, max_value=10):
    responses = [RateLimitError()] * n_errors + [valid_response]
    mock_client.messages.create = AsyncMock(side_effect=responses)
    IF n_errors <= 3:
        result = await agent._call_api(messages, tools)
        ASSERT mock_client.messages.create.call_count == n_errors + 1
    ELSE:
        ASSERT raises(AgentError, agent._call_api, messages, tools)
        ASSERT mock_client.messages.create.call_count == 4
```

### TS-03-P5: Failed generation preserves partial artifacts

**Property:** Property 5 from design.md
**Validates:** 03-REQ-6.E1
**Type:** property
**Description:** For any generation failure at artifact N, artifacts 1..N-1 remain on disk.

**For any:** failure_point in {1, 2, 3} (which artifact fails)
**Invariant:** previously written artifacts exist on disk

**Assertion pseudocode:**
```
artifact_names = ["requirements", "test_spec", "tasks"]
FOR ANY failure_point IN [0, 1, 2]:
    session = create_test_session(state="prd_accepted")
    mock_agent = create_mock_agent_failing_at(failure_point)
    with pytest.raises(AgentError):
        await session.generate()
    for i in range(failure_point):
        ASSERT (session.spec_dir / f"{artifact_names[i]}.json").exists()
    ASSERT session.state != SessionState.GENERATED
```

## Edge Case Tests

### TS-03-E1: Empty PRD raises AgentError

**Requirement:** 03-REQ-1.E1
**Type:** unit
**Description:** Verify assess_prd raises AgentError for empty PRD without making an API call.

**Preconditions:**
- Mocked Anthropic client

**Input:**
- Call assess_prd("", "test") and assess_prd("   ", "test")

**Expected:**
- AgentError raised in both cases
- No API calls made

**Assertion pseudocode:**
```
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with pytest.raises(AgentError):
    await agent.assess_prd("", "test")
with pytest.raises(AgentError):
    await agent.assess_prd("   ", "test")
ASSERT mock_client.messages.create.call_count == 0
```

### TS-03-E2: Malformed assessment tool response

**Requirement:** 03-REQ-1.E2
**Type:** unit
**Description:** Verify AgentError when tool response is missing required fields.

**Preconditions:**
- Mocked client returning tool_use with missing "summary" field

**Input:**
- Call assess_prd

**Expected:**
- AgentError raised with detail about invalid fields

**Assertion pseudocode:**
```
mock_client = mock_anthropic_with_tool_input({"quality": "ready"})  # missing summary, gaps, questions
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with pytest.raises(AgentError, match="summary|fields"):
    await agent.assess_prd("# PRD", "test")
```

### TS-03-E3: No tool_use in response

**Requirement:** 03-REQ-1.E3
**Type:** unit
**Description:** Verify AgentError when model returns only text, no tool call.

**Preconditions:**
- Mocked client returning text-only response

**Input:**
- Call assess_prd

**Expected:**
- AgentError raised indicating no structured output

**Assertion pseudocode:**
```
mock_client = mock_anthropic_text_only("Here is my assessment...")
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with pytest.raises(AgentError, match="structured output"):
    await agent.assess_prd("# PRD", "test")
```

### TS-03-E4: Empty answers in refine_prd

**Requirement:** 03-REQ-2.E1
**Type:** unit
**Description:** Verify AgentError when answers dict is empty.

**Preconditions:**
- Valid previous assessment

**Input:**
- Call refine_prd("# PRD", {}, previous_assessment)

**Expected:**
- AgentError raised
- No API call made

**Assertion pseudocode:**
```
agent = SpecAgent(mock_client, "claude-sonnet-4-6")
with pytest.raises(AgentError, match="no answers"):
    await agent.refine_prd("# PRD", {}, prev_assessment)
ASSERT mock_client.messages.create.call_count == 0
```

### TS-03-E5: Unrecognized question IDs in answers

**Requirement:** 03-REQ-2.E2
**Type:** unit
**Description:** Verify AgentError when answer IDs don't match assessment questions.

**Preconditions:**
- Previous assessment with questions [q1, q2]
- Answers with key "q99" (not in assessment)

**Input:**
- Call refine_prd("# PRD", {"q99": "answer"}, prev_assessment)

**Expected:**
- AgentError raised listing unrecognized IDs

**Assertion pseudocode:**
```
prev = Assessment(quality="needs_refinement", summary="", gaps=[], questions=[q1, q2])
with pytest.raises(AgentError, match="q99"):
    await agent.refine_prd("# PRD", {"q99": "answer"}, prev)
```

### TS-03-E6: Missing assessment in refinement response

**Requirement:** 03-REQ-2.E3
**Type:** unit
**Description:** Verify AgentError when the agent returns a PRD update but no assessment.

**Preconditions:**
- Mocked client returning submit_prd_update but not submit_assessment

**Input:**
- Call refine_prd

**Expected:**
- AgentError raised

**Assertion pseudocode:**
```
mock_client = mock_anthropic_with_tool_calls([("submit_prd_update", {"updated_prd": "new prd"})])
# Missing submit_assessment tool call
with pytest.raises(AgentError):
    await agent.refine_prd("# PRD", {"q1": "a"}, prev)
```

### TS-03-E7: Empty PRD for generation

**Requirement:** 03-REQ-3.E1
**Type:** unit
**Description:** Verify generate_artifacts raises AgentError for empty PRD.

**Preconditions:**
- None

**Input:**
- Call generate_artifacts("", "03", "test")

**Expected:**
- AgentError raised
- No API calls made

**Assertion pseudocode:**
```
with pytest.raises(AgentError):
    await agent.generate_artifacts("", "03", "test")
ASSERT mock_client.messages.create.call_count == 0
```

### TS-03-E8: Artifact tool not invoked by model

**Requirement:** 03-REQ-3.E2
**Type:** unit
**Description:** Verify AgentError when the model doesn't call submit_artifact.

**Preconditions:**
- Mocked client returning text-only response during generation

**Input:**
- Call generate_artifacts

**Expected:**
- AgentError raised

**Assertion pseudocode:**
```
mock_client = mock_anthropic_text_only("Here is the artifact content...")
with pytest.raises(AgentError):
    await agent.generate_artifacts("# PRD", "03", "test")
```

### TS-03-E9: Schema validation failure with detailed error

**Requirement:** 03-REQ-3.E3
**Type:** unit
**Description:** Verify AgentError includes artifact name and validation details.

**Preconditions:**
- Mocked client returning valid JSON that fails afspec schema validation

**Input:**
- Call generate_artifacts

**Expected:**
- AgentError raised containing artifact name and validation failure detail

**Assertion pseudocode:**
```
with patch("afspec.validate_artifact", side_effect=ValidationError("missing 'introduction'")):
    with pytest.raises(AgentError, match="requirements.*introduction"):
        await agent.generate_artifacts("# PRD", "03", "test")
```

### TS-03-E10: Missing prompt parameter raises ValueError

**Requirement:** 03-REQ-4.E1
**Type:** unit
**Description:** Verify prompt templates raise ValueError for missing parameters.

**Preconditions:**
- None

**Input:**
- Call assessment_user_prompt with empty prd_text

**Expected:**
- ValueError raised

**Assertion pseudocode:**
```
with pytest.raises(ValueError):
    assessment_user_prompt("", "test")
with pytest.raises(ValueError):
    generation_user_prompt("", "requirements")
```

### TS-03-E11: Connection timeout treated as transient

**Requirement:** 03-REQ-5.E1
**Type:** unit
**Description:** Verify connection timeouts are retried.

**Preconditions:**
- Mocked client raising ConnectionError on first call, succeeding on second

**Input:**
- Call _call_api

**Expected:**
- Two calls made, second succeeds

**Assertion pseudocode:**
```
mock_client.messages.create = AsyncMock(
    side_effect=[ConnectionError("timeout"), valid_response]
)
result = await agent._call_api(messages, tools)
ASSERT mock_client.messages.create.call_count == 2
```

### TS-03-E12: Cumulative wait cap

**Requirement:** 03-REQ-5.E2
**Type:** unit
**Description:** Verify retries abandon when cumulative wait would exceed 30 seconds.

**Preconditions:**
- Mocked client always raising RateLimitError
- Backoff delays: 1s, 2s, 4s = 7s total (under 30s, so all 3 retries happen)
- With 4 retries it would be 1+2+4+8=15s, still under. Verify 3 retry max enforced.

**Input:**
- Call _call_api

**Expected:**
- AgentError raised after exactly 4 total attempts

**Assertion pseudocode:**
```
mock_client.messages.create = AsyncMock(side_effect=RateLimitError())
with pytest.raises(AgentError):
    await agent._call_api(messages, tools)
ASSERT mock_client.messages.create.call_count == 4  # 1 initial + 3 retries
```

### TS-03-E13: Partial generation failure preserves artifacts

**Requirement:** 03-REQ-6.E1
**Type:** unit
**Description:** Verify partial artifacts remain on disk after generation failure.

**Preconditions:**
- SpecSession in "prd_accepted" state
- Agent generates requirements successfully, fails on test_spec

**Input:**
- Call session.generate()

**Expected:**
- AgentError raised
- requirements.json exists on disk
- test_spec.json and tasks.json do not exist
- Session state is "generating" (not "generated")

**Assertion pseudocode:**
```
session = create_test_session(state="prd_accepted")
mock_agent = create_mock_agent_failing_at_artifact("test_spec")
with pytest.raises(AgentError):
    await session.generate()
ASSERT (session.spec_dir / "requirements.json").exists()
ASSERT not (session.spec_dir / "test_spec.json").exists()
ASSERT session.state == SessionState.GENERATING
```

### TS-03-E14: Resume after partial generation

**Requirement:** 03-REQ-6.E2
**Type:** unit
**Description:** Verify resumed session detects existing artifacts and generates only missing ones.

**Preconditions:**
- Session in "generating" state with requirements.json already on disk
- No test_spec.json or tasks.json

**Input:**
- Call session.generate() after resume

**Expected:**
- Agent generates only test_spec and tasks (2 API calls, not 3)
- All three artifacts exist after completion

**Assertion pseudocode:**
```
session = resume_test_session(state="generating", existing=["requirements.json"])
mock_agent = create_mock_agent_for_remaining(["test_spec", "tasks"])
await session.generate()
ASSERT mock_client.messages.create.call_count == 2  # only test_spec and tasks
ASSERT (session.spec_dir / "requirements.json").exists()
ASSERT (session.spec_dir / "test_spec.json").exists()
ASSERT (session.spec_dir / "tasks.json").exists()
ASSERT session.state == SessionState.GENERATED
```

## Integration Smoke Tests

### TS-03-SMOKE-1: Full assessment flow

**Execution Path:** Path 1 from design.md
**Description:** Full path from SpecSession.assess() through SpecAgent.assess_prd() to persisted Assessment.

**Setup:**
- Campaign with one spec in "init" state
- Mocked Anthropic client returning valid assessment tool_use response

**Trigger:** Call session.assess()

**Expected side effects:**
- Assessment persisted to _session.json
- Session state is "assessing"
- Assessment has valid quality, summary, gaps, questions

**Must NOT satisfy with:** Bypassing SpecAgent (testing session state machine alone is insufficient).

**Assertion pseudocode:**
```
campaign = create_test_campaign()
session = campaign.new_spec("test_spec", "# My PRD\n## Intent\nBuild something")
with mock_anthropic_assessment_response(quality="needs_refinement"):
    await session.assess()
ASSERT session.state == SessionState.ASSESSING
data = json.loads((session.spec_dir / "_session.json").read_text())
ASSERT data["assessment_history"][-1]["quality"] == "needs_refinement"
```

### TS-03-SMOKE-2: Full refinement flow

**Execution Path:** Path 2 from design.md
**Description:** Full path from SpecSession.refine() through SpecAgent.refine_prd() to updated PRD and new Assessment.

**Setup:**
- Session in "assessing" state with a previous Assessment containing questions
- Mocked Anthropic client returning updated PRD and new assessment

**Trigger:** Call session.refine({"q1": "REST API for users"})

**Expected side effects:**
- prd.md updated with new content
- New Assessment persisted
- Session state transitions appropriately

**Must NOT satisfy with:** Bypassing SpecAgent or only testing state transitions.

**Assertion pseudocode:**
```
session = create_assessed_session(assessment=needs_refinement_assessment)
with mock_anthropic_refinement_response(updated_prd="# Updated", quality="ready"):
    await session.refine({"q1": "REST API for users"})
prd = (session.spec_dir / "prd.md").read_text()
ASSERT "Updated" in prd
data = json.loads((session.spec_dir / "_session.json").read_text())
ASSERT len(data["assessment_history"]) == 2
```

### TS-03-SMOKE-3: Full generation flow

**Execution Path:** Path 3 from design.md
**Description:** Full path from SpecSession.generate() through SpecAgent.generate_artifacts() to written and validated artifact files.

**Setup:**
- Session in "prd_accepted" state
- Mocked Anthropic client returning valid JSON for all three artifacts
- Mocked afspec validation passing

**Trigger:** Call session.generate()

**Expected side effects:**
- requirements.json, test_spec.json, tasks.json written to spec directory
- Each file contains valid JSON matching spec-format schemas
- Session state is "generated"

**Must NOT satisfy with:** Writing files directly without going through SpecAgent.

**Assertion pseudocode:**
```
session = create_accepted_session()
with mock_anthropic_generation_responses(req_json, test_json, task_json):
    await session.generate()
for name in ["requirements.json", "test_spec.json", "tasks.json"]:
    ASSERT (session.spec_dir / name).exists()
    content = json.loads((session.spec_dir / name).read_text())
    ASSERT isinstance(content, dict)
ASSERT session.state == SessionState.GENERATED
```

### TS-03-SMOKE-4: Retry and recovery

**Execution Path:** Path 4 from design.md
**Description:** Full path demonstrating retry on transient error followed by successful completion.

**Setup:**
- Mocked client that returns 429 on first call, then succeeds

**Trigger:** Call session.assess()

**Expected side effects:**
- Assessment succeeds despite the initial 429
- Two API calls made total
- Session state transitions normally

**Must NOT satisfy with:** Skipping the retry mechanism.

**Assertion pseudocode:**
```
session = create_test_session(state="init")
mock_client = mock_anthropic_with_transient_then_success(
    transient_errors=[RateLimitError()],
    success_response=valid_assessment_response
)
await session.assess()
ASSERT mock_client.messages.create.call_count == 2
ASSERT session.state == SessionState.ASSESSING
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 03-REQ-1.1 | TS-03-1 | unit |
| 03-REQ-1.2 | TS-03-1 | unit |
| 03-REQ-1.3 | TS-03-2 | unit |
| 03-REQ-1.4 | TS-03-3 | unit |
| 03-REQ-1.5 | TS-03-4 | unit |
| 03-REQ-1.6 | TS-03-5 | unit |
| 03-REQ-1.E1 | TS-03-E1 | unit |
| 03-REQ-1.E2 | TS-03-E2 | unit |
| 03-REQ-1.E3 | TS-03-E3 | unit |
| 03-REQ-2.1 | TS-03-6 | unit |
| 03-REQ-2.2 | TS-03-6 | unit |
| 03-REQ-2.3 | TS-03-7 | unit |
| 03-REQ-2.4 | TS-03-8 | unit |
| 03-REQ-2.5 | TS-03-6 | unit |
| 03-REQ-2.E1 | TS-03-E4 | unit |
| 03-REQ-2.E2 | TS-03-E5 | unit |
| 03-REQ-2.E3 | TS-03-E6 | unit |
| 03-REQ-3.1 | TS-03-9 | unit |
| 03-REQ-3.2 | TS-03-9 | unit |
| 03-REQ-3.3 | TS-03-10 | unit |
| 03-REQ-3.4 | TS-03-11 | unit |
| 03-REQ-3.5 | TS-03-12 | unit |
| 03-REQ-3.6 | TS-03-13 | unit |
| 03-REQ-3.7 | TS-03-14 | unit |
| 03-REQ-3.8 | TS-03-32 | unit |
| 03-REQ-3.E1 | TS-03-E7 | unit |
| 03-REQ-3.E2 | TS-03-E8 | unit |
| 03-REQ-3.E3 | TS-03-E9 | unit |
| 03-REQ-4.1 | TS-03-15 | unit |
| 03-REQ-4.2 | TS-03-16 | unit |
| 03-REQ-4.3 | TS-03-17 | unit |
| 03-REQ-4.4 | TS-03-18, TS-03-19, TS-03-20 | unit |
| 03-REQ-4.5 | TS-03-18, TS-03-19, TS-03-20 | unit |
| 03-REQ-4.6 | TS-03-18 | unit |
| 03-REQ-4.E1 | TS-03-E10 | unit |
| 03-REQ-5.1 | TS-03-21, TS-03-22 | unit |
| 03-REQ-5.2 | TS-03-23 | unit |
| 03-REQ-5.3 | TS-03-24 | unit |
| 03-REQ-5.4 | TS-03-25 | unit |
| 03-REQ-5.5 | TS-03-26 | unit |
| 03-REQ-5.E1 | TS-03-E11 | unit |
| 03-REQ-5.E2 | TS-03-E12 | unit |
| 03-REQ-6.1 | TS-03-27 | unit |
| 03-REQ-6.2 | TS-03-28 | unit |
| 03-REQ-6.3 | TS-03-29 | unit |
| 03-REQ-6.4 | TS-03-30 | unit |
| 03-REQ-6.5 | TS-03-31 | unit |
| 03-REQ-6.E1 | TS-03-E13 | unit |
| 03-REQ-6.E2 | TS-03-E14 | unit |
| Property 1 | TS-03-P1 | property |
| Property 2 | TS-03-P2 | property |
| Property 3 | TS-03-P3 | property |
| Property 4 | TS-03-P4 | property |
| Property 5 | TS-03-P5 | property |
| Path 1 | TS-03-SMOKE-1 | integration |
| Path 2 | TS-03-SMOKE-2 | integration |
| Path 3 | TS-03-SMOKE-3 | integration |
| Path 4 | TS-03-SMOKE-4 | integration |
