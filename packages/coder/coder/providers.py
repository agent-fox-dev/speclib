"""LLM provider abstraction layer.

Defines the LLMProvider interface and concrete implementations for
Anthropic, Google, and Ollama backends.

.. note::
    Implementation is provided by task group 3.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from langchain_core.messages import AIMessage, BaseMessage


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol defining the LLM provider interface.

    All providers must implement model_name, invoke(), and validate().
    """

    @property
    def model_name(self) -> str:
        """The model name this provider was configured with."""
        ...

    def invoke(
        self,
        messages: list[BaseMessage],
        tools: list[Any] | None = None,
    ) -> AIMessage:
        """Send messages to the LLM, optionally with tool definitions.

        Args:
            messages: List of chat messages to send.
            tools: Optional list of tool definitions.

        Returns:
            The AI's response message.
        """
        ...

    def validate(self) -> None:
        """Verify provider is correctly configured.

        Raises:
            ProviderConfigError: If credentials are missing.
            ProviderConnectionError: If the backend is unreachable.
        """
        ...


class AnthropicProvider:
    """LLM provider wrapping ChatAnthropic from langchain-anthropic.

    .. note::
        Full implementation provided by task group 3.
    """

    def __init__(self, model_name: str) -> None:
        raise NotImplementedError(
            "AnthropicProvider not yet implemented (task group 3)"
        )


class GoogleProvider:
    """LLM provider wrapping ChatGoogleGenerativeAI.

    .. note::
        Full implementation provided by task group 3.
    """

    def __init__(self, model_name: str) -> None:
        raise NotImplementedError(
            "GoogleProvider not yet implemented (task group 3)"
        )


class OllamaProvider:
    """LLM provider wrapping ChatOllama from langchain-ollama.

    .. note::
        Full implementation provided by task group 3.
    """

    def __init__(
        self,
        model_name: str,
        *,
        ollama_url: str = "http://localhost:11434",
    ) -> None:
        raise NotImplementedError(
            "OllamaProvider not yet implemented (task group 3)"
        )

    def validate(self) -> None:
        """Validate Ollama connectivity."""
        raise NotImplementedError(
            "OllamaProvider.validate not yet implemented (task group 3)"
        )
