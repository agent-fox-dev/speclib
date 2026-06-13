"""Provider registry mapping model names to LLM providers.

.. note::
    Full implementation provided by task group 3.
"""

from __future__ import annotations

from typing import Any


class ProviderRegistry:
    """Maps model name patterns to provider constructors.

    .. note::
        Full implementation provided by task group 3.
    """

    def resolve(self, model_name: str) -> Any:
        """Create a provider for the given model name."""
        raise NotImplementedError(
            "ProviderRegistry.resolve not yet implemented (task group 3)"
        )

    def register(
        self, prefix: str, constructor: Any
    ) -> None:
        """Register a custom prefix-to-provider mapping."""
        raise NotImplementedError(
            "ProviderRegistry.register not yet implemented (task group 3)"
        )

    def list_models(self) -> list[Any]:
        """Return all known model patterns."""
        raise NotImplementedError(
            "ProviderRegistry.list_models not yet implemented (task group 3)"
        )
