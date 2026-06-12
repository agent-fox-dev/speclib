# Test Specification: Project Scaffold and Configuration

## Overview

Tests validate the project build system, configuration loading with proper
precedence, and Anthropic client factory autodetection. Test cases map 1:1 to
requirements; property tests verify config precedence invariants.

## Test Cases

### TS-01-1: Package installable via uv

**Requirement:** 01-REQ-1.1
**Type:** integration
**Description:** Verify that `uv pip install .` succeeds and produces the `spec` CLI entry point.

**Preconditions:**
- uv is installed
- Clean virtual environment

**Input:**
- Run `uv pip install .` from the project root

**Expected:**
- Exit code 0
- `spec --help` produces usage output

**Assertion pseudocode:**
```
result = shell("uv pip install .")
ASSERT result.exit_code == 0
result2 = shell("spec --help")
ASSERT result2.exit_code == 0
ASSERT "Usage" in result2.stdout
```

### TS-01-2: pyproject.toml declares required runtime dependencies

**Requirement:** 01-REQ-1.2
**Type:** unit
**Description:** Verify pyproject.toml lists afspec, anthropic, click, and pyyaml as dependencies.

**Preconditions:**
- pyproject.toml exists in project root

**Input:**
- Parse pyproject.toml

**Expected:**
- `[project.dependencies]` contains entries for afspec, anthropic, click, pyyaml

**Assertion pseudocode:**
```
toml = parse_toml("pyproject.toml")
deps = toml["project"]["dependencies"]
ASSERT any("afspec" in d for d in deps)
ASSERT any("anthropic" in d for d in deps)
ASSERT any("click" in d for d in deps)
ASSERT any("pyyaml" in d or "PyYAML" in d for d in deps)
```

### TS-01-3: pyproject.toml declares dev dependencies

**Requirement:** 01-REQ-1.3
**Type:** unit
**Description:** Verify pyproject.toml lists pytest, hypothesis, ruff, and mypy as dev dependencies.

**Preconditions:**
- pyproject.toml exists

**Input:**
- Parse pyproject.toml

**Expected:**
- Dev dependencies include pytest, hypothesis, ruff, mypy

**Assertion pseudocode:**
```
toml = parse_toml("pyproject.toml")
dev_deps = toml["project"]["optional-dependencies"]["dev"]
ASSERT any("pytest" in d for d in dev_deps)
ASSERT any("hypothesis" in d for d in dev_deps)
ASSERT any("ruff" in d for d in dev_deps)
ASSERT any("mypy" in d for d in dev_deps)
```

### TS-01-4: Python version constraint

**Requirement:** 01-REQ-1.4
**Type:** unit
**Description:** Verify pyproject.toml requires Python 3.14+.

**Preconditions:**
- pyproject.toml exists

**Input:**
- Parse pyproject.toml

**Expected:**
- `requires-python` is `">=3.14"`

**Assertion pseudocode:**
```
toml = parse_toml("pyproject.toml")
ASSERT toml["project"]["requires-python"] == ">=3.14"
```

### TS-01-5: make check runs linter and tests

**Requirement:** 01-REQ-1.5
**Type:** integration
**Description:** Verify `make check` runs ruff and pytest in sequence.

**Preconditions:**
- Makefile exists with `check` target

**Input:**
- Read Makefile content

**Expected:**
- `check` target depends on or runs `lint` and `test`

**Assertion pseudocode:**
```
makefile = read("Makefile")
ASSERT "ruff check" in makefile or "lint" in makefile
ASSERT "pytest" in makefile or "test" in makefile
```

### TS-01-6: make test runs pytest

**Requirement:** 01-REQ-1.6
**Type:** integration
**Description:** Verify `make test` runs `uv run pytest -q`.

**Preconditions:**
- Makefile exists with `test` target

**Input:**
- Read Makefile content

**Expected:**
- `test` target runs `uv run pytest`

**Assertion pseudocode:**
```
makefile = read("Makefile")
ASSERT "uv run pytest" in makefile
```

### TS-01-7: Config loads from settings.yaml

**Requirement:** 01-REQ-2.1
**Type:** unit
**Description:** Verify load_config reads spec_tool section from settings.yaml.

**Preconditions:**
- Temp directory with a settings.yaml containing spec_tool.model = "claude-opus-4-6"

**Input:**
- Call load_config() with the temp settings path

**Expected:**
- config.model == "claude-opus-4-6"

**Assertion pseudocode:**
```
write("~/.af/settings.yaml", "spec_tool:\n  model: claude-opus-4-6\n")
config = load_config()
ASSERT config.model == "claude-opus-4-6"
```

### TS-01-8: Env vars override settings.yaml

**Requirement:** 01-REQ-2.2
**Type:** unit
**Description:** Verify environment variables take precedence over YAML values.

**Preconditions:**
- settings.yaml has model: "claude-opus-4-6"
- AF_SPEC_MODEL env var set to "claude-haiku-4-5-20251001"

**Input:**
- Call load_config()

**Expected:**
- config.model == "claude-haiku-4-5-20251001"

**Assertion pseudocode:**
```
write("settings.yaml", "spec_tool:\n  model: claude-opus-4-6\n")
os.environ["AF_SPEC_MODEL"] = "claude-haiku-4-5-20251001"
config = load_config()
ASSERT config.model == "claude-haiku-4-5-20251001"
```

### TS-01-9: SpecToolConfig has required fields

**Requirement:** 01-REQ-2.3
**Type:** unit
**Description:** Verify SpecToolConfig has model, auth_method, and api_key fields.

**Preconditions:**
- None

**Input:**
- Instantiate SpecToolConfig

**Expected:**
- Has model, auth_method, api_key attributes

**Assertion pseudocode:**
```
config = SpecToolConfig()
ASSERT hasattr(config, "model")
ASSERT hasattr(config, "auth_method")
ASSERT hasattr(config, "api_key")
```

### TS-01-10: Default config values

**Requirement:** 01-REQ-2.4
**Type:** unit
**Description:** Verify defaults when no config file or env vars exist.

**Preconditions:**
- No ~/.af/settings.yaml
- No relevant env vars set

**Input:**
- Call load_config()

**Expected:**
- model="claude-sonnet-4-6", auth_method="api_key", api_key=None

**Assertion pseudocode:**
```
config = load_config()
ASSERT config.model == "claude-sonnet-4-6"
ASSERT config.auth_method == "api_key"
ASSERT config.api_key is None
```

### TS-01-11: API key auth creates Anthropic client

**Requirement:** 01-REQ-3.1
**Type:** unit
**Description:** Verify create_client returns Anthropic instance when using api_key auth.

**Preconditions:**
- ANTHROPIC_API_KEY is set

**Input:**
- Call create_client() with api_key config

**Expected:**
- Returns (anthropic.Anthropic instance, model_name)

**Assertion pseudocode:**
```
os.environ["ANTHROPIC_API_KEY"] = "test-key"
client, model = create_client()
ASSERT isinstance(client, anthropic.Anthropic)
ASSERT model == "claude-sonnet-4-6"
```

### TS-01-12: Bedrock auth creates AnthropicBedrock client

**Requirement:** 01-REQ-3.2
**Type:** unit
**Description:** Verify create_client returns AnthropicBedrock instance for bedrock auth.

**Preconditions:**
- AF_SPEC_AUTH=bedrock
- AWS credentials available

**Input:**
- Call create_client() with bedrock config

**Expected:**
- Returns (anthropic.AnthropicBedrock instance, model_name)

**Assertion pseudocode:**
```
os.environ["AF_SPEC_AUTH"] = "bedrock"
client, model = create_client()
ASSERT isinstance(client, anthropic.AnthropicBedrock)
```

### TS-01-13: Vertex auth creates AnthropicVertex client

**Requirement:** 01-REQ-3.3
**Type:** unit
**Description:** Verify create_client returns AnthropicVertex instance for vertex auth.

**Preconditions:**
- AF_SPEC_AUTH=vertex
- AF_SPEC_VERTEX_PROJECT and AF_SPEC_VERTEX_REGION set

**Input:**
- Call create_client() with vertex config

**Expected:**
- Returns (anthropic.AnthropicVertex instance, model_name)

**Assertion pseudocode:**
```
os.environ["AF_SPEC_AUTH"] = "vertex"
os.environ["AF_SPEC_VERTEX_PROJECT"] = "test-project"
os.environ["AF_SPEC_VERTEX_REGION"] = "us-east5"
client, model = create_client()
ASSERT isinstance(client, anthropic.AnthropicVertex)
```

### TS-01-14: create_client uses config fallback

**Requirement:** 01-REQ-3.4
**Type:** unit
**Description:** Verify create_client falls back to SpecToolConfig when env vars unset.

**Preconditions:**
- No AF_SPEC_AUTH env var
- SpecToolConfig has auth_method="api_key", api_key="test"

**Input:**
- Call create_client(config=SpecToolConfig(auth_method="api_key", api_key="test"))

**Expected:**
- Returns (Anthropic instance, model_name)

**Assertion pseudocode:**
```
config = SpecToolConfig(auth_method="api_key", api_key="test-key")
client, model = create_client(config)
ASSERT isinstance(client, anthropic.Anthropic)
```

### TS-01-15: Settings.yaml auth_method used when no env var

**Requirement:** 01-REQ-3.5
**Type:** unit
**Description:** Verify settings.yaml auth method is used when AF_SPEC_AUTH is not set.

**Preconditions:**
- settings.yaml has spec_tool.auth.method: bedrock
- No AF_SPEC_AUTH env var

**Input:**
- Call load_config(), then create_client()

**Expected:**
- config.auth_method == "bedrock"

**Assertion pseudocode:**
```
write("settings.yaml", "spec_tool:\n  auth:\n    method: bedrock\n")
config = load_config()
ASSERT config.auth_method == "bedrock"
```

### TS-01-16: SpeclibError base exception

**Requirement:** 01-REQ-4.1
**Type:** unit
**Description:** Verify SpeclibError is defined and inherits from Exception.

**Preconditions:**
- None

**Input:**
- Import SpeclibError

**Expected:**
- issubclass(SpeclibError, Exception)

**Assertion pseudocode:**
```
from speclib.errors import SpeclibError
ASSERT issubclass(SpeclibError, Exception)
```

### TS-01-17: ConfigError inherits from SpeclibError

**Requirement:** 01-REQ-4.2
**Type:** unit
**Description:** Verify ConfigError inherits from SpeclibError.

**Preconditions:**
- None

**Input:**
- Import ConfigError

**Expected:**
- issubclass(ConfigError, SpeclibError)

**Assertion pseudocode:**
```
from speclib.errors import ConfigError, SpeclibError
ASSERT issubclass(ConfigError, SpeclibError)
```

## Property Test Cases

### TS-01-P1: Env vars always override YAML

**Property:** Property 1 from design.md
**Validates:** 01-REQ-2.2
**Type:** property
**Description:** For any model string set via AF_SPEC_MODEL, the loaded config uses it regardless of YAML value.

**For any:** model name string (ascii, non-empty)
**Invariant:** load_config().model == env_model when AF_SPEC_MODEL is set

**Assertion pseudocode:**
```
FOR ANY env_model IN text(min_size=1, alphabet=ascii_letters):
    os.environ["AF_SPEC_MODEL"] = env_model
    write("settings.yaml", "spec_tool:\n  model: different-value\n")
    config = load_config()
    ASSERT config.model == env_model
```

### TS-01-P2: Defaults are consistent

**Property:** Property 2 from design.md
**Validates:** 01-REQ-2.4
**Type:** property
**Description:** Without any config source, defaults are always the same.

**For any:** invocation of load_config with no settings file and no env vars
**Invariant:** model is "claude-sonnet-4-6" and auth_method is "api_key"

**Assertion pseudocode:**
```
FOR ANY _ IN range(10):
    clear_all_env_vars()
    remove_settings_file()
    config = load_config()
    ASSERT config.model == "claude-sonnet-4-6"
    ASSERT config.auth_method == "api_key"
```

### TS-01-P3: Client type matches auth method

**Property:** Property 3 from design.md
**Validates:** 01-REQ-3.1, 01-REQ-3.2, 01-REQ-3.3
**Type:** property
**Description:** The client type returned always matches the auth_method in config.

**For any:** valid auth_method in {"api_key", "bedrock", "vertex"}
**Invariant:** type(client) matches the expected SDK class for that auth method

**Assertion pseudocode:**
```
FOR ANY auth_method IN ["api_key", "bedrock", "vertex"]:
    config = SpecToolConfig(auth_method=auth_method, api_key="key", vertex_project="p", vertex_region="r")
    client, _ = create_client(config)
    IF auth_method == "api_key":
        ASSERT isinstance(client, anthropic.Anthropic)
    ELIF auth_method == "bedrock":
        ASSERT isinstance(client, anthropic.AnthropicBedrock)
    ELIF auth_method == "vertex":
        ASSERT isinstance(client, anthropic.AnthropicVertex)
```

## Edge Case Tests

### TS-01-E1: Invalid YAML in settings file

**Requirement:** 01-REQ-2.E1
**Type:** unit
**Description:** Verify ConfigError raised for malformed YAML.

**Preconditions:**
- settings.yaml contains invalid YAML (e.g., ":::bad")

**Input:**
- Call load_config()

**Expected:**
- ConfigError raised with file path in message

**Assertion pseudocode:**
```
write("settings.yaml", ":::bad yaml")
ASSERT raises(ConfigError, load_config)
```

### TS-01-E2: Missing spec_tool section

**Requirement:** 01-REQ-2.E2
**Type:** unit
**Description:** Verify defaults used when spec_tool section is absent.

**Preconditions:**
- settings.yaml exists with other content but no spec_tool key

**Input:**
- Call load_config()

**Expected:**
- Returns default SpecToolConfig, no error raised

**Assertion pseudocode:**
```
write("settings.yaml", "other_tool:\n  key: value\n")
config = load_config()
ASSERT config.model == "claude-sonnet-4-6"
```

### TS-01-E3: Unknown keys in spec_tool

**Requirement:** 01-REQ-2.E3
**Type:** unit
**Description:** Verify unknown keys are silently ignored.

**Preconditions:**
- settings.yaml has spec_tool.unknown_key: "value"

**Input:**
- Call load_config()

**Expected:**
- Returns config without error, unknown key ignored

**Assertion pseudocode:**
```
write("settings.yaml", "spec_tool:\n  unknown_key: value\n  model: test-model\n")
config = load_config()
ASSERT config.model == "test-model"
```

### TS-01-E4: Unknown AF_SPEC_AUTH value

**Requirement:** 01-REQ-3.E1
**Type:** unit
**Description:** Verify ConfigError for unrecognized auth method.

**Preconditions:**
- AF_SPEC_AUTH="invalid_method"

**Input:**
- Call create_client()

**Expected:**
- ConfigError raised listing valid methods

**Assertion pseudocode:**
```
os.environ["AF_SPEC_AUTH"] = "invalid_method"
ASSERT raises(ConfigError, create_client)
ASSERT "api_key" in str(error) and "bedrock" in str(error) and "vertex" in str(error)
```

### TS-01-E5: API key auth without key

**Requirement:** 01-REQ-3.E2
**Type:** unit
**Description:** Verify ConfigError when api_key auth has no key available.

**Preconditions:**
- No ANTHROPIC_API_KEY env var
- No key in settings.yaml

**Input:**
- Call create_client() with api_key auth method

**Expected:**
- ConfigError raised

**Assertion pseudocode:**
```
config = SpecToolConfig(auth_method="api_key", api_key=None)
ASSERT raises(ConfigError, lambda: create_client(config))
```

### TS-01-E6: Vertex auth without project

**Requirement:** 01-REQ-3.E3
**Type:** unit
**Description:** Verify ConfigError when vertex auth lacks project.

**Preconditions:**
- AF_SPEC_AUTH=vertex
- No AF_SPEC_VERTEX_PROJECT

**Input:**
- Call create_client()

**Expected:**
- ConfigError raised mentioning required variables

**Assertion pseudocode:**
```
os.environ["AF_SPEC_AUTH"] = "vertex"
del os.environ["AF_SPEC_VERTEX_PROJECT"]
ASSERT raises(ConfigError, create_client)
```

### TS-01-E7: uv required for installation

**Requirement:** 01-REQ-1.E1
**Type:** unit
**Description:** Verify pyproject.toml does not include pip-based install instructions and the project documents uv as the only supported installer.

**Preconditions:**
- pyproject.toml exists

**Input:**
- Read pyproject.toml and README.md

**Expected:**
- No pip install instructions in README; uv is documented as required

**Assertion pseudocode:**
```
readme = read("README.md")
ASSERT "uv" in readme
ASSERT "pip install" not in readme or "uv pip install" in readme
```

## Integration Smoke Tests

### TS-01-SMOKE-1: Configuration loading end-to-end

**Execution Path:** Path 1 from design.md
**Description:** Full config load from YAML + env var override produces correct SpecToolConfig.

**Setup:** Temp directory with settings.yaml, AF_SPEC_MODEL env var set.

**Trigger:** Call load_config() with temp settings path.

**Expected side effects:**
- Returns SpecToolConfig with env var value for model, YAML value for other fields.

**Must NOT satisfy with:** Mocking load_config internals.

**Assertion pseudocode:**
```
write("settings.yaml", "spec_tool:\n  model: yaml-model\n  auth:\n    method: api_key\n")
os.environ["AF_SPEC_MODEL"] = "env-model"
config = load_config()
ASSERT config.model == "env-model"
ASSERT config.auth_method == "api_key"
```

### TS-01-SMOKE-2: Client creation end-to-end

**Execution Path:** Path 2 from design.md
**Description:** Full path from config load to client creation.

**Setup:** ANTHROPIC_API_KEY set, no other auth env vars.

**Trigger:** Call create_client() with no explicit config.

**Expected side effects:**
- Returns (Anthropic instance, default model name).

**Must NOT satisfy with:** Mocking create_client or load_config.

**Assertion pseudocode:**
```
os.environ["ANTHROPIC_API_KEY"] = "test-key"
client, model = create_client()
ASSERT isinstance(client, anthropic.Anthropic)
ASSERT model == "claude-sonnet-4-6"
```

## Coverage Matrix

| Requirement | Test Spec Entry | Type |
|-------------|-----------------|------|
| 01-REQ-1.1 | TS-01-1 | integration |
| 01-REQ-1.2 | TS-01-2 | unit |
| 01-REQ-1.3 | TS-01-3 | unit |
| 01-REQ-1.4 | TS-01-4 | unit |
| 01-REQ-1.5 | TS-01-5 | integration |
| 01-REQ-1.6 | TS-01-6 | integration |
| 01-REQ-2.1 | TS-01-7 | unit |
| 01-REQ-2.2 | TS-01-8 | unit |
| 01-REQ-2.3 | TS-01-9 | unit |
| 01-REQ-2.4 | TS-01-10 | unit |
| 01-REQ-3.1 | TS-01-11 | unit |
| 01-REQ-3.2 | TS-01-12 | unit |
| 01-REQ-3.3 | TS-01-13 | unit |
| 01-REQ-3.4 | TS-01-14 | unit |
| 01-REQ-3.5 | TS-01-15 | unit |
| 01-REQ-4.1 | TS-01-16 | unit |
| 01-REQ-4.2 | TS-01-17 | unit |
| 01-REQ-1.E1 | TS-01-E7 | unit |
| 01-REQ-2.E1 | TS-01-E1 | unit |
| 01-REQ-2.E2 | TS-01-E2 | unit |
| 01-REQ-2.E3 | TS-01-E3 | unit |
| 01-REQ-3.E1 | TS-01-E4 | unit |
| 01-REQ-3.E2 | TS-01-E5 | unit |
| 01-REQ-3.E3 | TS-01-E6 | unit |
| Property 1 | TS-01-P1 | property |
| Property 2 | TS-01-P2 | property |
| Property 3 | TS-01-P3 | property |
| Path 1 | TS-01-SMOKE-1 | integration |
| Path 2 | TS-01-SMOKE-2 | integration |
