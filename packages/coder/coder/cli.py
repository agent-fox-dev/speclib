"""CLI entry point for the coder tool.

Provides the ``coder`` command group with ``run`` and ``models``
subcommands. Wires together configuration loading, provider creation,
logging setup, and prompt assembly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from coder.config import load_config
from coder.errors import CoderError
from coder.logging import get_logger, setup_logging
from coder.registry import ProviderRegistry


@click.group()
def cli() -> None:
    """Coder: spec-driven coding agent with multi-LLM provider support."""


@cli.command()
@click.argument("campaign_dir")
@click.option("--model", default=None, help="Model name to use.")
@click.option(
    "--repo",
    default=None,
    help="Target repository path (defaults to current directory).",
)
def run(
    campaign_dir: str,
    model: str | None,
    repo: str | None,
) -> None:
    """Run the coding agent on a campaign directory."""
    logger = get_logger(__name__)

    # Validate campaign directory exists
    campaign_path = Path(campaign_dir)
    if not campaign_path.exists():
        click.echo(
            f"Error: campaign directory does not exist: "
            f"{campaign_dir}",
            err=True,
        )
        sys.exit(1)

    # Load configuration
    try:
        config = load_config()
    except CoderError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    # Set up logging from config
    setup_logging(config)

    # Resolve model name: CLI arg > config default
    resolved_model = model if model is not None else config.model

    # Resolve repo path: CLI arg > current directory
    repo_path = Path(repo) if repo is not None else Path.cwd()

    # Create provider via registry
    try:
        registry = ProviderRegistry()
        provider = registry.resolve(resolved_model)
    except CoderError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    # Log run parameters
    logger.info(
        "coder_run_start",
        campaign_dir=str(campaign_path),
        model=resolved_model,
        repo=str(repo_path),
        provider=type(provider).__name__,
    )

    # Build execution plan from campaign directory
    from coder.planner import build_execution_plan
    from coder.runner import run_campaign

    try:
        plan = build_execution_plan(campaign_path)
    except CoderError as exc:
        click.echo(f"Error building execution plan: {exc}", err=True)
        sys.exit(1)

    if plan.count == 0:
        click.echo("No active specs found in campaign directory.")
        sys.exit(0)

    click.echo(f"Executing {plan.count} spec(s)...")

    # Run the campaign
    config_dict: dict[str, object] = {
        "model": resolved_model,
    }
    results = run_campaign(plan, provider, repo_path, config_dict)

    # Print results summary
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    click.echo(f"\nResults: {passed} passed, {failed} failed")
    for r in results:
        status = "PASS" if r.success else "FAIL"
        click.echo(
            f"  [{status}] {r.spec_name}: "
            f"{r.task_groups_completed}/{r.total_task_groups} groups, "
            f"{r.elapsed_seconds:.1f}s"
        )
        if r.halt_reason:
            click.echo(f"         Reason: {r.halt_reason}")

    if failed > 0:
        sys.exit(1)


@cli.command()
def models() -> None:
    """List available models and their providers."""
    registry = ProviderRegistry()
    model_list = registry.list_models()

    # Print a formatted table
    click.echo(f"{'Pattern':<20} {'Provider':<15} {'Description'}")
    click.echo(f"{'-' * 20} {'-' * 15} {'-' * 40}")
    for info in model_list:
        click.echo(
            f"{info.name:<20} {info.provider:<15} "
            f"{info.description}"
        )
