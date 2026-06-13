"""Layered prompt assembly.

.. note::
    Full implementation provided by task group 4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from coder.templates import TemplateLoader


class PromptAssembler:
    """Composes system prompts from multiple template layers.

    .. note::
        Full implementation provided by task group 4.
    """

    def __init__(self, loader: TemplateLoader) -> None:
        raise NotImplementedError(
            "PromptAssembler not yet implemented (task group 4)"
        )

    def assemble(
        self,
        *,
        persona: str,
        task_context: str,
        variables: dict[str, str] | None = None,
    ) -> str:
        """Compose 3-layer prompt from base + persona + context."""
        raise NotImplementedError(
            "PromptAssembler.assemble not yet implemented (task group 4)"
        )
