"""Tests for speclib.agent — SpecAgent core methods.

Covers TS-03-1 through TS-03-14 (assessment, refinement, generation),
TS-03-21 through TS-03-26 (retry and error handling).

All tests use a mocked Anthropic client; no real API calls are made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from speclib.agent import SpecAgent

from speclib.errors import AgentError, SpeclibError
from speclib.session import Assessment

from .conftest_agent import (
    SAMPLE_REQUIREMENTS_JSON,
    SAMPLE_TASKS_JSON,
    SAMPLE_TEST_SPEC_JSON,
    make_artifact_response,
    make_assessment_response,
    make_bad_request_error,
    make_internal_server_error,
    make_rate_limit_error,
    make_refinement_response,
    make_text_only_response,
)

# ===================================================================
# TS-03-1: assess_prd returns Assessment with valid quality
# ===================================================================


@pytest.mark.asyncio
async def test_assess_prd_returns_assessment_with_valid_quality(mock_client):
    """TS-03-1: assess_prd sends the PRD to the API and returns an
    Assessment with a valid quality value."""
    mock_client.messages.create.return_value = make_assessment_response(
        quality="needs_refinement",
        summary="Needs work",
        gaps=["Missing Goals"],
        questions=[
            {
                "id": "q1",
                "text": "What are the goals?",
                "context": "Goals section is missing",
                "options": [],
                "required": True,
            }
        ],
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    result = await agent.assess_prd("# My PRD\n\n## Intent\nDo things.", "my_spec")

    assert isinstance(result, Assessment)
    assert result.quality == "needs_refinement"
    assert mock_client.messages.create.call_count == 1


# ===================================================================
# TS-03-2: Assessment contains summary
# ===================================================================


@pytest.mark.asyncio
async def test_assessment_contains_summary(mock_client):
    """TS-03-2: The returned Assessment has a non-empty summary."""
    mock_client.messages.create.return_value = make_assessment_response(
        summary="The PRD is incomplete."
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    result = await agent.assess_prd("# PRD content", "test_spec")

    assert result.summary == "The PRD is incomplete."
    assert len(result.summary) > 0


# ===================================================================
# TS-03-3: Assessment contains gaps list
# ===================================================================


@pytest.mark.asyncio
async def test_assessment_contains_gaps(mock_client):
    """TS-03-3: The returned Assessment has a gaps list."""
    mock_client.messages.create.return_value = make_assessment_response(
        gaps=["No Goals section", "Background is vague"]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    result = await agent.assess_prd("# PRD content", "test_spec")

    assert result.gaps == ["No Goals section", "Background is vague"]


# ===================================================================
# TS-03-4: Non-ready assessment has questions
# ===================================================================


@pytest.mark.asyncio
async def test_non_ready_assessment_has_questions(mock_client):
    """TS-03-4: When quality is not 'ready', questions is non-empty."""
    q1 = {
        "id": "q1",
        "text": "What are the goals?",
        "context": "Goals section is missing",
        "options": [],
        "required": True,
    }
    mock_client.messages.create.return_value = make_assessment_response(
        quality="needs_refinement",
        questions=[q1],
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    result = await agent.assess_prd("# PRD", "test_spec")

    assert len(result.questions) > 0
    assert result.questions[0].id == "q1"
    assert result.questions[0].text == "What are the goals?"
    assert result.questions[0].required is True


# ===================================================================
# TS-03-5: Ready assessment may have empty questions
# ===================================================================


@pytest.mark.asyncio
async def test_ready_assessment_empty_questions(mock_client):
    """TS-03-5: When quality is 'ready', an empty questions list is valid."""
    mock_client.messages.create.return_value = make_assessment_response(
        quality="ready",
        summary="PRD is complete",
        gaps=[],
        questions=[],
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    result = await agent.assess_prd(
        "# PRD\n## Intent\n## Goals\n## Non-Goals\n## Background", "test_spec"
    )

    assert result.quality == "ready"
    assert result.questions == []


# ===================================================================
# TS-03-6: refine_prd returns updated PRD and new assessment
# ===================================================================


@pytest.mark.asyncio
async def test_refine_prd_returns_updated_prd_and_assessment(
    mock_client, sample_assessment
):
    """TS-03-6: refine_prd sends answers and returns an updated PRD
    with a new assessment."""
    mock_client.messages.create.return_value = make_refinement_response(
        updated_prd="# Updated PRD\n## Goals\n1. Build REST API",
        quality="ready",
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    updated, assessment = await agent.refine_prd(
        "# Original PRD", {"q1": "Build a REST API"}, sample_assessment
    )

    assert "REST API" in updated
    assert isinstance(assessment, Assessment)
    assert assessment.quality == "ready"


# ===================================================================
# TS-03-7: refine_prd answers dict maps question IDs to strings
# ===================================================================


@pytest.mark.asyncio
async def test_refine_prd_answers_in_user_message(mock_client, sample_questions):
    """TS-03-7: The answers dict maps question IDs to string answers
    and these appear in the user message sent to the API."""
    prev = Assessment(
        quality="needs_refinement",
        summary="",
        gaps=[],
        questions=sample_questions,
    )
    mock_client.messages.create.return_value = make_refinement_response(
        updated_prd="Updated", quality="ready"
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    await agent.refine_prd("# PRD", {"q1": "A1", "q2": "A2"}, prev)

    call_args = mock_client.messages.create.call_args
    user_msg = call_args.kwargs["messages"][-1]["content"]
    assert "q1" in user_msg and "A1" in user_msg
    assert "q2" in user_msg and "A2" in user_msg


# ===================================================================
# TS-03-8: refine_prd preserves frontmatter
# ===================================================================


@pytest.mark.asyncio
async def test_refine_prd_returns_body_only(mock_client, sample_assessment):
    """TS-03-8: The updated PRD from the agent contains body-only content.
    The caller (SpecSession) is responsible for re-attaching frontmatter."""
    mock_client.messages.create.return_value = make_refinement_response(
        updated_prd="## Intent\nUpdated body", quality="ready"
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")
    updated, _ = await agent.refine_prd(
        "---\nspec_id: 01\n---\n## Intent\nOriginal",
        {"q1": "answer"},
        sample_assessment,
    )

    assert "Updated body" in updated


# ===================================================================
# TS-03-9: generate_artifacts produces three artifacts in order
# ===================================================================


@pytest.mark.asyncio
async def test_generate_three_artifacts_in_order(mock_client):
    """TS-03-9: generate_artifacts makes three API calls and returns
    all three artifacts."""
    mock_client.messages.create = AsyncMock(
        side_effect=[
            make_artifact_response("requirements", SAMPLE_REQUIREMENTS_JSON),
            make_artifact_response("test_spec", SAMPLE_TEST_SPEC_JSON),
            make_artifact_response("tasks", SAMPLE_TASKS_JSON),
        ]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch("speclib.agent.validate_artifact", return_value=None):
        result = await agent.generate_artifacts(
            "# Accepted PRD", "03", "agent_pipeline"
        )

    assert set(result.keys()) == {"requirements", "test_spec", "tasks"}
    assert mock_client.messages.create.call_count == 3


# ===================================================================
# TS-03-10: generate_artifacts returns parsed JSON content
# ===================================================================


@pytest.mark.asyncio
async def test_generate_returns_parsed_json(mock_client):
    """TS-03-10: Each artifact value is parsed JSON (dict), not a raw string."""
    mock_client.messages.create = AsyncMock(
        side_effect=[
            make_artifact_response("requirements", SAMPLE_REQUIREMENTS_JSON),
            make_artifact_response("test_spec", SAMPLE_TEST_SPEC_JSON),
            make_artifact_response("tasks", SAMPLE_TASKS_JSON),
        ]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch("speclib.agent.validate_artifact", return_value=None):
        result = await agent.generate_artifacts("# PRD", "03", "test")

    for name, content in result.items():
        assert isinstance(content, dict), f"{name} should be a dict"


# ===================================================================
# TS-03-11: Each artifact validated before next generation
# ===================================================================


@pytest.mark.asyncio
async def test_validate_before_next_generation(mock_client):
    """TS-03-11: Each artifact is validated against its schema before
    the next artifact is generated."""
    call_log: list[tuple[str, str]] = []
    artifact_order = ["requirements", "test_spec", "tasks"]
    generate_counter = 0

    original_create = AsyncMock(
        side_effect=[
            make_artifact_response("requirements", SAMPLE_REQUIREMENTS_JSON),
            make_artifact_response("test_spec", SAMPLE_TEST_SPEC_JSON),
            make_artifact_response("tasks", SAMPLE_TASKS_JSON),
        ]
    )

    async def tracking_create(**kwargs):
        nonlocal generate_counter
        name = artifact_order[generate_counter]
        generate_counter += 1
        call_log.append(("generate", name))
        return await original_create(**kwargs)

    mock_client.messages.create = AsyncMock(side_effect=tracking_create)

    def tracking_validate(name, content):
        call_log.append(("validate", name))

    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch("speclib.agent.validate_artifact", side_effect=tracking_validate):
        await agent.generate_artifacts("# PRD", "03", "test")

    # Verify interleaved generate/validate pattern
    assert call_log == [
        ("generate", "requirements"),
        ("validate", "requirements"),
        ("generate", "test_spec"),
        ("validate", "test_spec"),
        ("generate", "tasks"),
        ("validate", "tasks"),
    ]


# ===================================================================
# TS-03-12: Validation failure aborts generation
# ===================================================================


@pytest.mark.asyncio
async def test_validation_failure_aborts_generation(mock_client):
    """TS-03-12: Generation stops and raises AgentError if an artifact
    fails validation."""
    mock_client.messages.create = AsyncMock(
        side_effect=[
            make_artifact_response("requirements", SAMPLE_REQUIREMENTS_JSON),
            make_artifact_response("test_spec", SAMPLE_TEST_SPEC_JSON),
            make_artifact_response("tasks", SAMPLE_TASKS_JSON),
        ]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch(
        "speclib.agent.validate_artifact",
        side_effect=Exception("schema mismatch"),
    ):
        with pytest.raises(AgentError):
            await agent.generate_artifacts("# PRD", "03", "test")

    # Only one API call made (requirements only, failed validation)
    assert mock_client.messages.create.call_count == 1


# ===================================================================
# TS-03-13: test_spec generation includes requirements context
# ===================================================================


@pytest.mark.asyncio
async def test_test_spec_includes_requirements_context(mock_client):
    """TS-03-13: The test_spec generation prompt includes the generated
    requirements content."""
    mock_client.messages.create = AsyncMock(
        side_effect=[
            make_artifact_response("requirements", SAMPLE_REQUIREMENTS_JSON),
            make_artifact_response("test_spec", SAMPLE_TEST_SPEC_JSON),
            make_artifact_response("tasks", SAMPLE_TASKS_JSON),
        ]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch("speclib.agent.validate_artifact", return_value=None):
        await agent.generate_artifacts("# PRD", "03", "test")

    # The second API call's user message should contain requirements content
    second_call = mock_client.messages.create.call_args_list[1]
    user_msg = second_call.kwargs["messages"][-1]["content"]
    assert "requirements" in user_msg.lower()


# ===================================================================
# TS-03-14: tasks generation includes both prior artifacts
# ===================================================================


@pytest.mark.asyncio
async def test_tasks_includes_both_prior_artifacts(mock_client):
    """TS-03-14: The tasks generation prompt includes both requirements
    and test_spec content."""
    mock_client.messages.create = AsyncMock(
        side_effect=[
            make_artifact_response("requirements", SAMPLE_REQUIREMENTS_JSON),
            make_artifact_response("test_spec", SAMPLE_TEST_SPEC_JSON),
            make_artifact_response("tasks", SAMPLE_TASKS_JSON),
        ]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch("speclib.agent.validate_artifact", return_value=None):
        await agent.generate_artifacts("# PRD", "03", "test")

    # The third API call's user message should contain both prior artifacts
    third_call = mock_client.messages.create.call_args_list[2]
    user_msg = third_call.kwargs["messages"][-1]["content"]
    assert "requirements" in user_msg.lower()
    assert "test_spec" in user_msg.lower()


# ===================================================================
# TS-03-21: Retry on 429 with exponential backoff
# ===================================================================


@pytest.mark.asyncio
async def test_retry_on_429_with_exponential_backoff(mock_client):
    """TS-03-21: The agent retries on HTTP 429 with increasing delays."""
    mock_client.messages.create = AsyncMock(
        side_effect=[
            make_rate_limit_error(),
            make_rate_limit_error(),
            make_assessment_response(),
        ]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await agent._call_api(
            messages=[{"role": "user", "content": "test"}],
            tools=[],
        )

    assert mock_client.messages.create.call_count == 3
    assert mock_sleep.call_count == 2
    # Verify exponential backoff: 1s, 2s
    assert mock_sleep.call_args_list[0].args[0] == pytest.approx(1.0)
    assert mock_sleep.call_args_list[1].args[0] == pytest.approx(2.0)


# ===================================================================
# TS-03-22: Retry on 5xx server error
# ===================================================================


@pytest.mark.asyncio
async def test_retry_on_5xx_server_error(mock_client):
    """TS-03-22: The agent retries on 5xx server errors."""
    mock_client.messages.create = AsyncMock(
        side_effect=[
            make_internal_server_error(),
            make_assessment_response(),
        ]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await agent._call_api(
            messages=[{"role": "user", "content": "test"}],
            tools=[],
        )

    assert mock_client.messages.create.call_count == 2


# ===================================================================
# TS-03-23: AgentError after retry exhaustion
# ===================================================================


@pytest.mark.asyncio
async def test_agent_error_after_retry_exhaustion(mock_client):
    """TS-03-23: AgentError is raised after all retries are exhausted."""
    # Create a fresh error for each call (side_effect needs callables or list)
    mock_client.messages.create = AsyncMock(
        side_effect=[
            make_rate_limit_error(),
            make_rate_limit_error(),
            make_rate_limit_error(),
            make_rate_limit_error(),
        ]
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(AgentError) as exc_info:
            await agent._call_api(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            )

    assert mock_client.messages.create.call_count == 4  # 1 initial + 3 retries
    assert exc_info.value.__cause__ is not None


# ===================================================================
# TS-03-24: No retry on 4xx (non-429)
# ===================================================================


@pytest.mark.asyncio
async def test_no_retry_on_4xx_non_429(mock_client):
    """TS-03-24: The agent raises AgentError immediately on 4xx errors
    other than 429."""
    mock_client.messages.create = AsyncMock(
        side_effect=make_bad_request_error()
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with pytest.raises(AgentError):
        await agent._call_api(
            messages=[{"role": "user", "content": "test"}],
            tools=[],
        )

    assert mock_client.messages.create.call_count == 1


# ===================================================================
# TS-03-25: AgentError inherits SpeclibError
# ===================================================================


def test_agent_error_inherits_speclib_error():
    """TS-03-25: AgentError is a subclass of SpeclibError with __cause__."""
    assert issubclass(AgentError, SpeclibError)
    original = ValueError("bad response")
    err = AgentError("parsing failed")
    err.__cause__ = original
    assert err.__cause__ is original
    assert err.detail == "parsing failed"


# ===================================================================
# TS-03-26: AgentError on unparseable response
# ===================================================================


@pytest.mark.asyncio
async def test_agent_error_on_unparseable_response(mock_client):
    """TS-03-26: AgentError is raised when the response has no tool_use blocks."""
    mock_client.messages.create.return_value = make_text_only_response(
        "I don't know how to use tools"
    )
    agent = SpecAgent(mock_client, "claude-sonnet-4-6")

    with pytest.raises(AgentError, match="structured output"):
        await agent.assess_prd("# PRD", "test")
