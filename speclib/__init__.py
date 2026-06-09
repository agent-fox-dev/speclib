"""speclib — AI-powered spec creation tool.

Re-exports key types from submodules for convenient access.
"""

from __future__ import annotations

from speclib.auth import create_client
from speclib.campaign import Campaign, CampaignMetadata
from speclib.config import SpecToolConfig, load_config
from speclib.errors import CampaignError, ConfigError, SessionError, SpeclibError
from speclib.session import (
    Assessment,
    GenerateResult,
    Question,
    RepairSuggestion,
    SessionState,
    SpecSession,
    ValidationResult,
)

__all__ = [
    "Assessment",
    "Campaign",
    "CampaignError",
    "CampaignMetadata",
    "ConfigError",
    "GenerateResult",
    "Question",
    "RepairSuggestion",
    "SessionError",
    "SessionState",
    "SpeclibError",
    "SpecSession",
    "SpecToolConfig",
    "ValidationResult",
    "create_client",
    "load_config",
]
