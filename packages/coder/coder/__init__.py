"""Coder: spec-driven coding agent with multi-LLM provider support."""

from coder.config import CoderConfig, load_config
from coder.errors import (
    CoderError,
    ConfigError,
    ProviderConfigError,
    ProviderConnectionError,
    TemplateNotFoundError,
    TemplateSecurityError,
)
from coder.logging import get_logger, setup_logging

__all__ = [
    # Config
    "CoderConfig",
    "load_config",
    # Logging
    "setup_logging",
    "get_logger",
    # Exceptions
    "CoderError",
    "ConfigError",
    "ProviderConfigError",
    "ProviderConnectionError",
    "TemplateNotFoundError",
    "TemplateSecurityError",
]
