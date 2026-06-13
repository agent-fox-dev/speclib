"""CLI entry point for the coder tool.

.. note::
    Full implementation provided by task group 5.
"""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """Coder: spec-driven coding agent with multi-LLM provider support."""


@cli.command()
@click.argument("campaign_dir")
@click.option("--model", default=None, help="Model name to use.")
@click.option(
    "--repo",
    default=None,
    help="Target repository path.",
)
def run(
    campaign_dir: str,
    model: str | None,
    repo: str | None,
) -> None:
    """Run the coding agent on a campaign directory."""
    raise NotImplementedError(
        "coder run not yet implemented (task group 5)"
    )


@cli.command()
def models() -> None:
    """List available models and their providers."""
    raise NotImplementedError(
        "coder models not yet implemented (task group 5)"
    )
