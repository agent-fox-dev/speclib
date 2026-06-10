"""Tests for afspec.validate_artifact — spec artifact validation.

Covers TS-08-1 through TS-08-7 (unit tests),
TS-08-E1, TS-08-E2 (edge cases),
TS-08-P1 through TS-08-P4 (property tests),
TS-08-SMOKE-1 (integration smoke test).

All tests are written against the test_spec.md contract.  They are expected
to FAIL until the implementation in task groups 2-3 is complete.
"""

from __future__ import annotations

import importlib
import inspect
import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Minimal valid artifact fixtures (derived from JSON schema required fields)
# ---------------------------------------------------------------------------

VALID_REQUIREMENTS: dict = {
    "spec_id": "test-01",
    "spec_name": "test_spec",
    "schema_version": 1,
    "introduction": "A test requirements artifact.",
}

VALID_TEST_SPEC: dict = {
    "spec_id": "test-01",
    "spec_name": "test_spec",
    "schema_version": 1,
}

VALID_TASKS: dict = {
    "spec_id": "test-01",
    "spec_name": "test_spec",
    "schema_version": 1,
}

VALID_CONTENT_FOR: dict[str, dict] = {
    "requirements": VALID_REQUIREMENTS,
    "test_spec": VALID_TEST_SPEC,
    "tasks": VALID_TASKS,
}

ARTIFACT_NAMES: list[str] = ["requirements", "test_spec", "tasks"]

SCHEMA_FILENAMES: list[str] = [
    "requirements.v1.json",
    "test_spec.v1.json",
    "tasks.v1.json",
]


# ===================================================================
# TS-08-1: validate_artifact is exported
# ===================================================================


def test_validate_artifact_importable():
    """TS-08-1: validate_artifact is importable from afspec."""
    from afspec import validate_artifact

    assert callable(validate_artifact)


# ===================================================================
# TS-08-2: Valid artifact passes
# ===================================================================


def test_valid_artifact_passes():
    """TS-08-2: Valid content returns None without error."""
    from afspec import validate_artifact

    result = validate_artifact("requirements", VALID_REQUIREMENTS)
    assert result is None


# ===================================================================
# TS-08-3: Invalid artifact raises ValidationError
# ===================================================================


def test_invalid_artifact_raises():
    """TS-08-3: Invalid content raises ValidationError with details."""
    from afspec import ValidationError, validate_artifact

    with pytest.raises(ValidationError) as exc_info:
        validate_artifact("requirements", {"wrong_key": 42})
    assert "requirements" in str(exc_info.value)


# ===================================================================
# TS-08-4: All three artifact names accepted
# ===================================================================


@pytest.mark.parametrize("name", ARTIFACT_NAMES)
def test_all_artifact_names_accepted(name: str):
    """TS-08-4: All three artifact names are recognized."""
    from afspec import validate_artifact

    validate_artifact(name, VALID_CONTENT_FOR[name])  # no exception


# ===================================================================
# TS-08-5: Schemas are loadable
# ===================================================================


@pytest.mark.parametrize("filename", SCHEMA_FILENAMES)
def test_schemas_loadable(filename: str):
    """TS-08-5: Bundled schema files exist and parse as valid JSON."""
    schema_files = importlib.resources.files("afspec.schemas")
    data = schema_files.joinpath(filename).read_text(encoding="utf-8")
    schema = json.loads(data)
    assert isinstance(schema, dict)


# ===================================================================
# TS-08-7: ValidationError has correct attributes
# ===================================================================


def test_validation_error_attributes():
    """TS-08-7: ValidationError has artifact_name and errors attrs."""
    from afspec import ValidationError, validate_artifact

    with pytest.raises(ValidationError) as exc_info:
        validate_artifact("requirements", {})
    exc = exc_info.value
    assert exc.artifact_name == "requirements"
    assert isinstance(exc.errors, list)
    assert len(exc.errors) > 0
    assert all(isinstance(e, str) for e in exc.errors)


# ===================================================================
# Edge Case Tests
# ===================================================================

# -------------------------------------------------------------------
# TS-08-E1: Unknown artifact name
# -------------------------------------------------------------------


def test_unknown_artifact_name():
    """TS-08-E1: Unrecognized artifact name raises ValueError."""
    from afspec import validate_artifact

    with pytest.raises(ValueError) as exc_info:
        validate_artifact("unknown", {})
    msg = str(exc_info.value)
    assert "requirements" in msg
    assert "test_spec" in msg
    assert "tasks" in msg


# -------------------------------------------------------------------
# TS-08-E2: Empty dict fails required fields
# -------------------------------------------------------------------


def test_empty_dict_fails():
    """TS-08-E2: Empty dict fails schema validation."""
    from afspec import ValidationError, validate_artifact

    with pytest.raises(ValidationError):
        validate_artifact("requirements", {})


# ===================================================================
# Property Tests
# ===================================================================

# -------------------------------------------------------------------
# TS-08-P1: Valid content passes
# -------------------------------------------------------------------


@given(
    name=st.sampled_from(ARTIFACT_NAMES),
    extra_id=st.text(min_size=1, max_size=20),
)
@settings(max_examples=30)
def test_valid_content_property(name: str, extra_id: str):
    """TS-08-P1: Any content conforming to the schema passes validation."""
    from afspec import validate_artifact

    # Build a valid artifact dict with a varying spec_id
    content = dict(VALID_CONTENT_FOR[name])
    content["spec_id"] = extra_id if extra_id.strip() else "x"
    result = validate_artifact(name, content)
    assert result is None


# -------------------------------------------------------------------
# TS-08-P2: Invalid content fails
# -------------------------------------------------------------------


@given(name=st.sampled_from(ARTIFACT_NAMES))
@settings(max_examples=15)
def test_invalid_content_property(name: str):
    """TS-08-P2: Content with required fields removed fails validation."""
    from afspec import ValidationError, validate_artifact

    # Remove all required fields -> guaranteed schema violation
    with pytest.raises(ValidationError):
        validate_artifact(name, {"not_a_real_field": True})


@given(name=st.sampled_from(ARTIFACT_NAMES))
@settings(max_examples=15)
def test_invalid_content_wrong_type(name: str):
    """TS-08-P2 (variant): Content with wrong types fails validation."""
    from afspec import ValidationError, validate_artifact

    # schema_version must be an integer with const value 1
    content = dict(VALID_CONTENT_FOR[name])
    content["schema_version"] = "not_an_int"
    with pytest.raises(ValidationError):
        validate_artifact(name, content)


# -------------------------------------------------------------------
# TS-08-P3: Name-schema bijection
# -------------------------------------------------------------------


@given(name=st.text(min_size=1, max_size=30))
@settings(max_examples=50)
def test_name_schema_bijection(name: str):
    """TS-08-P3: Valid names succeed, invalid names raise ValueError."""
    from afspec import validate_artifact

    valid_names = {"requirements", "test_spec", "tasks"}
    if name in valid_names:
        # Should NOT raise ValueError (may raise ValidationError for content)
        try:
            validate_artifact(name, VALID_CONTENT_FOR[name])
        except ValueError:
            pytest.fail(f"Valid name {name!r} raised ValueError")
    else:
        with pytest.raises(ValueError):
            validate_artifact(name, {})


# -------------------------------------------------------------------
# TS-08-P4: Error detail preservation
# -------------------------------------------------------------------


@given(name=st.sampled_from(ARTIFACT_NAMES))
@settings(max_examples=15)
def test_error_detail_preservation(name: str):
    """TS-08-P4: ValidationError always contains artifact name and errors."""
    from afspec import ValidationError, validate_artifact

    with pytest.raises(ValidationError) as exc_info:
        validate_artifact(name, {})
    exc = exc_info.value
    assert exc.artifact_name == name
    assert len(exc.errors) >= 1


# ===================================================================
# TS-08-6: Agent wrapper calls afspec directly
# ===================================================================


def test_agent_wrapper_direct_call():
    """TS-08-6: speclib/agent.py validate_artifact calls afspec directly."""
    from speclib.agent import validate_artifact as agent_validate

    source = inspect.getsource(agent_validate)
    assert "afspec.validate_artifact(" in source
    assert "getattr" not in source


# ===================================================================
# TS-08-SMOKE-1: End-to-end validation with real schemas
# ===================================================================


def test_validate_artifact_smoke():
    """TS-08-SMOKE-1: End-to-end validation using real bundled schemas."""
    from speclib.agent import validate_artifact

    result = validate_artifact("requirements", VALID_REQUIREMENTS)
    assert result is None
