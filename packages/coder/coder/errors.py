"""Custom exception types for the coder package.

Provides a hierarchy of domain-specific exceptions for configuration,
provider, and template errors.
"""

from __future__ import annotations


class CoderError(Exception):
    """Base exception for all coder package errors."""


class ConfigError(CoderError):
    """Raised when configuration loading or parsing fails.

    Attributes:
        file_path: Path to the config file that caused the error, if any.
        detail: Additional detail about the parse error.
    """

    def __init__(
        self,
        message: str,
        *,
        file_path: str | None = None,
        detail: str | None = None,
    ) -> None:
        parts = [message]
        if file_path:
            parts.append(f"file: {file_path}")
        if detail:
            parts.append(f"detail: {detail}")
        super().__init__(" | ".join(parts))
        self.file_path = file_path
        self.detail = detail


class ProviderConfigError(CoderError):
    """Raised when a provider cannot be configured.

    Typically caused by missing API keys or invalid credentials.

    Attributes:
        env_var: The expected environment variable name.
    """

    def __init__(
        self,
        message: str,
        *,
        env_var: str | None = None,
    ) -> None:
        super().__init__(message)
        self.env_var = env_var


class ProviderConnectionError(CoderError):
    """Raised when a provider cannot connect to its backend.

    Typically caused by an unreachable Ollama server.

    Attributes:
        url: The URL that was attempted.
    """

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
    ) -> None:
        super().__init__(message)
        self.url = url


class TemplateNotFoundError(CoderError):
    """Raised when a requested template does not exist.

    Attributes:
        name: The template name that was requested.
        searched_paths: The paths that were searched.
    """

    def __init__(
        self,
        name: str,
        *,
        searched_paths: list[str] | None = None,
    ) -> None:
        paths_str = (
            ", ".join(searched_paths) if searched_paths else "none"
        )
        super().__init__(
            f"Template '{name}' not found. Searched: {paths_str}"
        )
        self.name = name
        self.searched_paths = searched_paths or []


class TemplateSecurityError(CoderError):
    """Raised when a template path violates security constraints.

    Triggered by symlinks or path traversal attempts in template names.

    Attributes:
        name: The template name that caused the violation.
        reason: Description of the security violation.
    """

    def __init__(
        self,
        name: str,
        *,
        reason: str = "security violation",
    ) -> None:
        super().__init__(
            f"Template '{name}' rejected: {reason}"
        )
        self.name = name
        self.reason = reason
