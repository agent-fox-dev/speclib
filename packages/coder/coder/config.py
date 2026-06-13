"""Configuration system for the coder package.

Loads configuration from multiple sources with precedence:
  1. Environment variables (CODER_* prefix) — highest
  2. Project-level .coder.yaml
  3. User-level ~/.coder/config.yaml
  4. Built-in defaults — lowest

Returns a frozen pydantic CoderConfig model with validated types.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml
from pydantic import BaseModel

from coder.errors import ConfigError

logger = logging.getLogger(__name__)

# Mapping from CoderConfig field names to CODER_* env var names
_ENV_VAR_MAP: dict[str, str] = {
    "model": "CODER_MODEL",
    "templates_dir": "CODER_TEMPLATES_DIR",
    "ollama_url": "CODER_OLLAMA_URL",
    "log_level": "CODER_LOG_LEVEL",
    "log_file": "CODER_LOG_FILE",
}

# Known configuration keys (field names of CoderConfig)
_KNOWN_KEYS: frozenset[str] = frozenset(
    _ENV_VAR_MAP.keys()
)


class CoderConfig(BaseModel, frozen=True):
    """Frozen pydantic configuration model for the coder tool.

    All fields have sensible defaults. The model is frozen (immutable)
    after construction to prevent accidental mutation.
    """

    model: str = "claude-opus-4-6"
    templates_dir: str | None = None
    ollama_url: str = "http://localhost:11434"
    log_level: str = "DEBUG"
    log_file: str | None = None


def _load_yaml_file(path: Path) -> dict[str, object]:
    """Load and parse a YAML config file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed dictionary of configuration values.

    Raises:
        ConfigError: If the file contains invalid YAML syntax.
    """
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigError(
            "Invalid YAML syntax",
            file_path=str(path),
            detail=str(exc),
        ) from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(
            "Config file must contain a YAML mapping",
            file_path=str(path),
        )
    return data  # type: ignore[return-value]


def _warn_unknown_keys(
    data: dict[str, object], source: str
) -> dict[str, object]:
    """Log warnings for unknown configuration keys and return known ones.

    Args:
        data: Raw config dictionary.
        source: Description of the config source for log messages.

    Returns:
        Filtered dictionary containing only known keys.
    """
    known: dict[str, object] = {}
    for key, value in data.items():
        if key in _KNOWN_KEYS:
            known[key] = value
        else:
            logger.warning(
                "Unknown configuration key '%s' in %s (ignored)",
                key,
                source,
            )
    return known


def load_config(
    *,
    project_dir: Path | None = None,
    user_dir: Path | None = None,
) -> CoderConfig:
    """Load configuration with full precedence chain.

    Precedence (highest to lowest):
      1. Environment variables (CODER_*)
      2. Project-level .coder.yaml (in project_dir)
      3. User-level ~/.coder/config.yaml
      4. Built-in defaults

    Args:
        project_dir: Project directory to search for .coder.yaml.
            Defaults to the current working directory.
        user_dir: User config directory. Defaults to ~/.coder/.

    Returns:
        A frozen CoderConfig instance with all resolved values.

    Raises:
        ConfigError: If a config file contains invalid YAML.
    """
    merged: dict[str, object] = {}

    # Layer 4 (lowest): built-in defaults are handled by pydantic

    # Layer 3: user-level config
    if user_dir is None:
        user_dir = Path.home() / ".coder"
    user_config_path = user_dir / "config.yaml"
    if user_config_path.is_file():
        user_data = _load_yaml_file(user_config_path)
        user_data = _warn_unknown_keys(
            user_data, str(user_config_path)
        )
        merged.update(user_data)

    # Layer 2: project-level config
    if project_dir is None:
        project_dir = Path.cwd()
    project_config_path = project_dir / ".coder.yaml"
    if project_config_path.is_file():
        project_data = _load_yaml_file(project_config_path)
        project_data = _warn_unknown_keys(
            project_data, str(project_config_path)
        )
        merged.update(project_data)

    # Layer 1 (highest): environment variables
    for field_name, env_var in _ENV_VAR_MAP.items():
        env_value = os.environ.get(env_var)
        if env_value is not None:
            merged[field_name] = env_value

    return CoderConfig(**merged)  # type: ignore[arg-type]
