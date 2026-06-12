# Test Specification: afspec.validate_artifact

## Overview

Tests verify that `validate_artifact` correctly validates artifact dicts
against bundled JSON schemas, raises appropriate errors for invalid content
and unknown names, and that the bundled schemas are loadable.

## Test Cases

### TS-08-1: validate_artifact is exported

**Requirement:** 08-REQ-1.1
**Type:** unit
**Description:** Verifies `validate_artifact` is importable from `afspec`.

**Preconditions:** None.

**Input:**
- `from afspec import validate_artifact`

**Expected:**
- Import succeeds, `validate_artifact` is callable.

**Assertion pseudocode:**
```
from afspec import validate_artifact
ASSERT callable(validate_artifact)
```

### TS-08-2: Valid artifact passes

**Requirement:** 08-REQ-1.2
**Type:** unit
**Description:** Verifies valid content returns None without error.

**Preconditions:** None.

**Input:**
- `artifact_name = "requirements"`
- `content` = a minimal valid requirements dict conforming to schema.

**Expected:**
- Returns None.

**Assertion pseudocode:**
```
result = validate_artifact("requirements", valid_requirements)
ASSERT result IS None
```

### TS-08-3: Invalid artifact raises ValidationError

**Requirement:** 08-REQ-1.3
**Type:** unit
**Description:** Verifies invalid content raises ValidationError with details.

**Preconditions:** None.

**Input:**
- `artifact_name = "requirements"`
- `content = {"wrong_key": 42}` (missing required fields).

**Expected:**
- Raises `ValidationError`.
- Exception message includes "requirements".

**Assertion pseudocode:**
```
with pytest.raises(ValidationError) as exc_info:
    validate_artifact("requirements", {"wrong_key": 42})
ASSERT "requirements" IN str(exc_info.value)
```

### TS-08-4: All three artifact names accepted

**Requirement:** 08-REQ-1.4
**Type:** unit
**Description:** Verifies all three artifact names are recognized.

**Preconditions:** None.

**Input:**
- Call `validate_artifact` with each of `requirements`, `test_spec`, `tasks`
  and valid content for each.

**Expected:**
- All three calls succeed without error.

**Assertion pseudocode:**
```
FOR name IN ["requirements", "test_spec", "tasks"]:
    validate_artifact(name, valid_content_for(name))  # no exception
```

### TS-08-5: Schemas are loadable

**Requirement:** 08-REQ-2.1, 08-REQ-2.2
**Type:** unit
**Description:** Verifies bundled schema files exist and parse as valid JSON.

**Preconditions:** None.

**Input:**
- Load each schema file via `importlib.resources`.

**Expected:**
- All three files exist.
- All three parse as valid JSON dicts.

**Assertion pseudocode:**
```
FOR name IN ["requirements.v1.json", "test_spec.v1.json", "tasks.v1.json"]:
    data = importlib.resources.files("afspec.schemas").joinpath(name).read_text()
    schema = json.loads(data)
    ASSERT isinstance(schema, dict)
```

### TS-08-6: Agent wrapper calls afspec directly

**Requirement:** 08-REQ-3.1
**Type:** unit
**Description:** Verifies `speclib/agent.py:validate_artifact` calls
`afspec.validate_artifact` without a `getattr` fallback.

**Preconditions:** None.

**Input:**
- Read source of `speclib.agent.validate_artifact`.

**Expected:**
- Contains `afspec.validate_artifact(` call.
- Does NOT contain `getattr(afspec`.

**Assertion pseudocode:**
```
source = inspect.getsource(speclib.agent.validate_artifact)
ASSERT "afspec.validate_artifact(" IN source
ASSERT "getattr" NOT IN source
```

### TS-08-7: ValidationError has correct attributes

**Requirement:** 08-REQ-4.1, 08-REQ-4.2
**Type:** unit
**Description:** Verifies ValidationError has artifact_name and errors attrs.

**Preconditions:** None.

**Input:**
- Trigger a validation failure.

**Expected:**
- Exception has `artifact_name` attribute matching the name.
- Exception has `errors` attribute that is a non-empty list of strings.

**Assertion pseudocode:**
```
with pytest.raises(ValidationError) as exc_info:
    validate_artifact("requirements", {})
exc = exc_info.value
ASSERT exc.artifact_name == "requirements"
ASSERT isinstance(exc.errors, list)
ASSERT len(exc.errors) > 0
ASSERT all(isinstance(e, str) for e in exc.errors)
```

## Edge Case Tests

### TS-08-E1: Unknown artifact name

**Requirement:** 08-REQ-1.E1
**Type:** unit
**Description:** Verifies ValueError for unrecognized artifact name.

**Preconditions:** None.

**Input:**
- `validate_artifact("unknown", {})`

**Expected:**
- Raises `ValueError`.
- Message lists valid names.

**Assertion pseudocode:**
```
with pytest.raises(ValueError) as exc_info:
    validate_artifact("unknown", {})
ASSERT "requirements" IN str(exc_info.value)
ASSERT "test_spec" IN str(exc_info.value)
ASSERT "tasks" IN str(exc_info.value)
```

### TS-08-E2: Empty dict fails required fields

**Requirement:** 08-REQ-1.E2
**Type:** unit
**Description:** Verifies empty dict fails schema validation.

**Preconditions:** None.

**Input:**
- `validate_artifact("requirements", {})`

**Expected:**
- Raises `ValidationError` (schemas have required fields).

**Assertion pseudocode:**
```
with pytest.raises(ValidationError):
    validate_artifact("requirements", {})
```

## Property Test Cases

### TS-08-P1: Valid content passes

**Property:** Property 1 from design.md
**Validates:** 08-REQ-1.2
**Type:** property
**Description:** Any content conforming to the schema passes validation.

**For any:** valid artifact dict generated from schema constraints
**Invariant:** `validate_artifact(name, valid_content)` returns None

**Assertion pseudocode:**
```
FOR ANY name IN ["requirements", "test_spec", "tasks"]:
    content = generate_valid_content(name)
    ASSERT validate_artifact(name, content) IS None
```

### TS-08-P2: Invalid content fails

**Property:** Property 2 from design.md
**Validates:** 08-REQ-1.3
**Type:** property
**Description:** Content with wrong types or missing required fields fails.

**For any:** artifact dict with at least one required field removed or typed wrong
**Invariant:** `validate_artifact(name, invalid_content)` raises ValidationError

**Assertion pseudocode:**
```
FOR ANY name IN ["requirements", "test_spec", "tasks"]:
    FOR ANY mutation IN remove_required_field, wrong_type:
        content = mutate(generate_valid_content(name), mutation)
        with pytest.raises(ValidationError):
            validate_artifact(name, content)
```

### TS-08-P3: Name-schema bijection

**Property:** Property 3 from design.md
**Validates:** 08-REQ-1.4, 08-REQ-1.E1
**Type:** property
**Description:** Valid names succeed, invalid names raise ValueError.

**For any:** string that is or is not in {"requirements", "test_spec", "tasks"}
**Invariant:** valid names do not raise ValueError; invalid names do

**Assertion pseudocode:**
```
FOR ANY name IN text():
    IF name IN {"requirements", "test_spec", "tasks"}:
        # Does not raise ValueError (may raise ValidationError for content)
    ELSE:
        with pytest.raises(ValueError):
            validate_artifact(name, {})
```

### TS-08-P4: Error detail preservation

**Property:** Property 4 from design.md
**Validates:** 08-REQ-4.2
**Type:** property
**Description:** ValidationError always contains artifact name and errors.

**For any:** validation failure from any artifact type
**Invariant:** `exc.artifact_name == name` and `len(exc.errors) >= 1`

**Assertion pseudocode:**
```
FOR ANY name IN ["requirements", "test_spec", "tasks"]:
    with pytest.raises(ValidationError) as exc_info:
        validate_artifact(name, {})
    ASSERT exc_info.value.artifact_name == name
    ASSERT len(exc_info.value.errors) >= 1
```

## Integration Smoke Tests

### TS-08-SMOKE-1: End-to-end validation with real schemas

**Execution Path:** Path 1 from design.md
**Description:** Verifies the full path from `speclib/agent.py` wrapper
through `afspec.validate_artifact` to schema validation, using real bundled
schemas.

**Setup:** No mocking of `afspec` or `validate_artifact`. Use a minimal
valid artifact dict constructed from the actual schema.

**Trigger:** Call `speclib.agent.validate_artifact("requirements", valid_content)`.

**Expected side effects:**
- Returns None (valid content passes).
- No exceptions raised.

**Must NOT satisfy with:** Mocking `afspec.validate_artifact`, patching
`jsonschema`, or skipping schema loading.

**Assertion pseudocode:**
```
from speclib.agent import validate_artifact
result = validate_artifact("requirements", valid_requirements_content)
ASSERT result IS None
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 08-REQ-1.1 | TS-08-1 | unit |
| 08-REQ-1.2 | TS-08-2 | unit |
| 08-REQ-1.3 | TS-08-3 | unit |
| 08-REQ-1.4 | TS-08-4 | unit |
| 08-REQ-1.E1 | TS-08-E1 | unit |
| 08-REQ-1.E2 | TS-08-E2 | unit |
| 08-REQ-2.1 | TS-08-5 | unit |
| 08-REQ-2.2 | TS-08-5 | unit |
| 08-REQ-3.1 | TS-08-6 | unit |
| 08-REQ-4.1 | TS-08-7 | unit |
| 08-REQ-4.2 | TS-08-7 | unit |
| Property 1 | TS-08-P1 | property |
| Property 2 | TS-08-P2 | property |
| Property 3 | TS-08-P3 | property |
| Property 4 | TS-08-P4 | property |
| Path 1 | TS-08-SMOKE-1 | integration |
