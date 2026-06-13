"""Coder: spec-driven coding agent with multi-LLM provider support."""

from coder.config import CoderConfig, load_config
from coder.errors import (
    CoderError,
    ConfigError,
    DependencyCycleError,
    ProviderConfigError,
    ProviderConnectionError,
    SpecParseError,
    TemplateNotFoundError,
    TemplateSecurityError,
)
from coder.logging import get_logger, setup_logging
from coder.models import ExecutionPlan, ParsedSpec
from coder.planner import build_execution_plan

__all__ = [
    # Config
    "CoderConfig",
    "load_config",
    # Logging
    "setup_logging",
    "get_logger",
    # Models
    "ParsedSpec",
    "ExecutionPlan",
    # Planner
    "build_execution_plan",
    # Exceptions
    "CoderError",
    "ConfigError",
    "DependencyCycleError",
    "ProviderConfigError",
    "ProviderConnectionError",
    "SpecParseError",
    "TemplateNotFoundError",
    "TemplateSecurityError",
]
