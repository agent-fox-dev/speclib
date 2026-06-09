"""Exception hierarchy for speclib."""


class SpeclibError(Exception):
    """Base exception for all speclib errors."""


class ConfigError(SpeclibError):
    """Configuration and authentication errors."""


class CampaignError(SpeclibError):
    """Raised for campaign directory operation failures."""


class SessionError(SpeclibError):
    """Raised for session state machine or persistence failures."""


class AgentError(SpeclibError):
    """Error during agent communication or response parsing.

    Attributes:
        detail: Human-readable description of what went wrong.
        __cause__: The underlying exception, if any.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail
