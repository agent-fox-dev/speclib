"""Template loading from filesystem with security validation.

.. note::
    Full implementation provided by task group 4.
"""

from __future__ import annotations

from pathlib import Path


class TemplateLoader:
    """Loads prompt templates from filesystem with security checks.

    .. note::
        Full implementation provided by task group 4.
    """

    def __init__(
        self,
        *,
        project_dir: Path | None = None,
    ) -> None:
        raise NotImplementedError(
            "TemplateLoader not yet implemented (task group 4)"
        )

    def load(self, name: str) -> str:
        """Load and return template content by name."""
        raise NotImplementedError(
            "TemplateLoader.load not yet implemented (task group 4)"
        )
