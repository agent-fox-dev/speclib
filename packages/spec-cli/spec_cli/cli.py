"""CLI entry point for the spec tool.

Provides the ``spec`` command group with subcommands for campaign
management and spec authoring.  Delegates all business logic to speclib's
Campaign and SpecSession classes.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import click
from speclib.campaign import Campaign
from speclib.errors import CampaignError, SessionError, SpeclibError
from speclib.session import SpecSession

from spec_cli.ui import StatusSpinner

_SPEC_DIR_RE = re.compile(r"^(\d{2})_(.+)$")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def resolve_campaign(campaign_dir: Path) -> Campaign:
    """Open a Campaign from the given directory path.

    Wraps :pymethod:`Campaign.open` and appends a ``--campaign-dir``
    hint to ``CampaignError`` messages so the user knows how to fix it.
    """
    try:
        return Campaign.open(campaign_dir)
    except CampaignError as exc:
        msg = (
            f"{exc}\n"
            "Hint: use --campaign-dir to specify the campaign directory."
        )
        raise CampaignError(msg) from exc


def resolve_spec(campaign: Campaign, spec_arg: str) -> Path:
    """Resolve a spec argument to a spec directory path.

    Matches by full directory name first, then by zero-padded numeric
    prefix.  Raises ``CampaignError`` listing available specs on
    mismatch.
    """
    spec_dirs = campaign.specs()

    for spec_dir in spec_dirs:
        if spec_dir.name == spec_arg:
            return spec_dir

    padded = spec_arg.zfill(2)
    for spec_dir in spec_dirs:
        match = _SPEC_DIR_RE.match(spec_dir.name)
        if match and match.group(1) == padded:
            return spec_dir

    if spec_dirs:
        available = "\n".join(f"  {d.name}" for d in spec_dirs)
        msg = f"Spec '{spec_arg}' not found. Available specs:\n{available}"
    else:
        msg = f"Spec '{spec_arg}' not found. The campaign has no specs."
    raise CampaignError(msg)


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format *headers* and *rows* as a plain-text aligned table."""
    if not rows:
        return ""

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    lines: list[str] = []
    lines.append("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    lines.append("  ".join("-" * w for w in widths))
    for row in rows:
        lines.append(
            "  ".join(
                (row[i] if i < len(row) else "").ljust(widths[i])
                for i in range(len(headers))
            )
        )
    return "\n".join(lines)


def format_assessment(assessment: Any) -> str:
    """Format an assessment result for terminal display.

    Handles both dict (from mocks / JSON) and dataclass instances.
    """
    lines: list[str] = []

    if isinstance(assessment, dict):
        quality = assessment.get("quality", "unknown")
        score = assessment.get("score", "")
        summary = assessment.get("summary", "")
        gaps = assessment.get("gaps", [])
        questions = assessment.get("questions", [])
    else:
        quality = getattr(assessment, "quality", "unknown")
        score = getattr(assessment, "score", "")
        summary = getattr(assessment, "summary", "")
        gaps = getattr(assessment, "gaps", [])
        questions = getattr(assessment, "questions", [])

    lines.append(f"Quality: {quality}")
    if score:
        lines.append(f"Score: {score}")
    if summary:
        lines.append(f"Summary: {summary}")

    if gaps:
        lines.append("")
        lines.append("Gaps:")
        for i, gap in enumerate(gaps, 1):
            lines.append(f"  {i}. {gap}")

    if questions:
        lines.append("")
        lines.append("Questions:")
        for q in questions:
            if isinstance(q, dict):
                qid = q.get("id", "?")
                text = q.get("text", "")
            else:
                qid = getattr(q, "id", "?")
                text = getattr(q, "text", "")
            lines.append(f"  {qid}: {text}")

    return "\n".join(lines)


def format_validation_errors(errors: list[dict[str, str]]) -> str:
    """Format validation errors as a file / path / message table."""
    headers = ["File", "Path", "Message"]
    rows = [
        [err.get("file", ""), err.get("path", ""), err.get("message", "")]
        for err in errors
    ]
    return format_table(headers, rows)


def _read_session_data(spec_dir: Path) -> dict[str, Any]:
    """Read raw session data from ``_session.json``."""
    session_file = spec_dir / "_session.json"
    if session_file.exists():
        try:
            data: dict[str, Any] = json.loads(session_file.read_text())
            return data
        except json.JSONDecodeError:
            return {"state": "unknown"}
    return {"state": "unknown"}


def _count_artifacts(spec_dir: Path) -> int:
    """Count non-hidden, non-session files in a spec directory."""
    exclude = {"_session.json"}
    return sum(
        1
        for f in spec_dir.iterdir()
        if f.is_file() and f.name not in exclude and not f.name.startswith(".")
    )


def _derive_spec_name(filename: str) -> str:
    """Derive a snake_case spec name from a PRD filename."""
    stem = Path(filename).stem
    return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@click.group()
@click.option(
    "--campaign-dir",
    "-C",
    type=click.Path(exists=True),
    default=None,
    help="Campaign directory (default: CWD)",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Suppress progress output",
)
@click.version_option(package_name="speclib")
@click.pass_context
def main(ctx: click.Context, campaign_dir: str | None, quiet: bool) -> None:
    """spec: AI-powered spec creation tool."""
    ctx.ensure_object(dict)
    ctx.obj["campaign_dir"] = (
        Path(campaign_dir) if campaign_dir else Path.cwd()
    )
    ctx.obj["quiet"] = quiet


# ---------------------------------------------------------------------------
# Campaign commands
# ---------------------------------------------------------------------------


@main.command("init")
@click.argument("path", type=click.Path())
@click.option(
    "--name",
    default=None,
    help="Campaign name (default: directory basename)",
)
@click.option("--description", default="", help="Campaign description")
def init_cmd(path: str, name: str | None, description: str) -> None:
    """Create a new campaign working directory."""
    try:
        resolved = Path(path).resolve()
        if name is None:
            name = resolved.name
        Campaign.create(resolved, name, description)
        click.echo(f"Campaign created at {resolved}")
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


@main.command("list")
@click.argument("campaign_dir", required=False, type=click.Path(exists=True))
@click.pass_context
def list_cmd(ctx: click.Context, campaign_dir: str | None) -> None:
    """List specs in a campaign directory with their session state."""
    try:
        cd = Path(campaign_dir) if campaign_dir else ctx.obj["campaign_dir"]
        campaign = resolve_campaign(cd)
        spec_dirs = campaign.specs()

        if not spec_dirs:
            click.echo("Campaign is empty. No specs found.")
            return

        headers = ["#", "Name", "State", "Artifacts"]
        rows: list[list[str]] = []
        for spec_dir in spec_dirs:
            match = _SPEC_DIR_RE.match(spec_dir.name)
            if match:
                num, sname = match.group(1), match.group(2)
            else:
                num, sname = "??", spec_dir.name
            data = _read_session_data(spec_dir)
            state = data.get("state", "unknown")
            count = _count_artifacts(spec_dir)
            rows.append([num, sname, state, str(count)])

        click.echo(format_table(headers, rows))
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Spec authoring commands
# ---------------------------------------------------------------------------


@main.command("new")
@click.argument("prd_file", type=click.Path(exists=True))
@click.option(
    "--name",
    default=None,
    help="Spec name (default: derived from filename)",
)
@click.option("--one-shot", is_flag=True, help="Skip interactive refinement")
@click.pass_context
def new_cmd(
    ctx: click.Context,
    prd_file: str,
    name: str | None,
    one_shot: bool,
) -> None:
    """Create a new spec from a PRD."""
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        campaign = resolve_campaign(campaign_dir)

        prd_path = Path(prd_file)
        prd_content = prd_path.read_text()

        if name is None:
            name = _derive_spec_name(prd_path.name)

        mode = "one-shot" if one_shot else "interactive"
        session = campaign.new_spec(name, prd_content, mode=mode)
        click.echo(f"Created spec: {session.spec_dir.name}")
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


@main.command("assess")
@click.argument("spec")
@click.pass_context
def assess_cmd(ctx: click.Context, spec: str) -> None:
    """Run or re-run PRD assessment."""
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        quiet = ctx.obj.get("quiet", False)
        campaign = resolve_campaign(campaign_dir)
        spec_dir = resolve_spec(campaign, spec)
        session = SpecSession.resume(spec_dir)
        with StatusSpinner("Assessing PRD...", quiet=quiet):
            assessment: Any = asyncio.run(session.assess())  # type: ignore[arg-type]
        click.echo(format_assessment(assessment))
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


@main.command("refine")
@click.argument("spec")
@click.option(
    "--answers",
    required=False,
    default=None,
    type=click.Path(exists=True),
    help="JSON file with answers to assessment questions. "
    "Omit to output pending questions as JSON.",
)
@click.pass_context
def refine_cmd(
    ctx: click.Context, spec: str, answers: str | None
) -> None:
    """Submit answers and update PRD.

    Without --answers, outputs pending questions as JSON to stdout.
    """
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        quiet = ctx.obj.get("quiet", False)
        campaign = resolve_campaign(campaign_dir)
        spec_dir = resolve_spec(campaign, spec)
        session = SpecSession.resume(spec_dir)

        if answers is None:
            questions = session.pending_questions()
            if not session._assessment_history:
                click.echo(
                    "Error: No assessment exists for this spec. "
                    "Run 'assess' first.",
                    err=True,
                )
                sys.exit(1)
            output = {
                "questions": questions,
                "answers": {q["id"]: "" for q in questions},
            }
            click.echo(json.dumps(output, indent=2))
            return

        # Validate answers file before calling refine.
        answers_path = Path(answers)
        try:
            answers_data = json.loads(answers_path.read_text())
        except json.JSONDecodeError as exc:
            click.echo(
                f"Error: Invalid JSON in answers file: {exc}", err=True
            )
            sys.exit(1)

        if not isinstance(answers_data, dict):
            click.echo(
                "Error: Answers file must contain a JSON object "
                "mapping question IDs to answer strings.",
                err=True,
            )
            sys.exit(1)

        # Accept the question-export format: unwrap the "answers" key.
        if "answers" in answers_data and isinstance(
            answers_data["answers"], dict
        ):
            answers_data = answers_data["answers"]

        with StatusSpinner("Refining PRD with answers...", quiet=quiet):
            assessment: Any = asyncio.run(session.refine(answers_data))  # type: ignore[arg-type]
        click.echo(format_assessment(assessment))
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


@main.command("accept")
@click.argument("spec")
@click.pass_context
def accept_cmd(ctx: click.Context, spec: str) -> None:
    """Accept the PRD, ending refinement loop."""
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        campaign = resolve_campaign(campaign_dir)
        spec_dir = resolve_spec(campaign, spec)
        session = SpecSession.resume(spec_dir)
        session.accept_prd()
        click.echo("PRD accepted. New state: prd_accepted")
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Spec lifecycle commands
# ---------------------------------------------------------------------------


@main.command("generate")
@click.argument("spec")
@click.pass_context
def generate_cmd(ctx: click.Context, spec: str) -> None:
    """Generate JSON artifacts from accepted PRD."""
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        quiet = ctx.obj.get("quiet", False)
        campaign = resolve_campaign(campaign_dir)
        spec_dir = resolve_spec(campaign, spec)
        session = SpecSession.resume(spec_dir)
        with StatusSpinner("Generating requirements...", quiet=quiet) as spinner:
            gen_result: Any = asyncio.run(session.generate())  # type: ignore[arg-type]

            if isinstance(gen_result, dict):
                artifacts = gen_result.get("artifacts", [])
            else:
                artifacts = gen_result.artifacts

            for artifact in artifacts:
                spinner.log(f"Generated {artifact}")

        click.echo("Generated artifacts:")
        for artifact in artifacts:
            click.echo(f"  - {artifact}")
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


@main.command("validate")
@click.argument("spec")
@click.pass_context
def validate_cmd(ctx: click.Context, spec: str) -> None:
    """Run schema and cross-file checks."""
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        campaign = resolve_campaign(campaign_dir)
        spec_dir = resolve_spec(campaign, spec)
        session = SpecSession.resume(spec_dir)
        try:
            validation = session.validate()
        except (CampaignError, SessionError):
            raise
        except Exception as exc:
            click.echo(f"Error: Validation failed: {exc}", err=True)
            sys.exit(1)

        if validation.valid:
            click.echo("Validation passed. All checks successful.")
            return

        click.echo("Validation errors found:\n")
        errors: list[dict[str, str]] = []
        for err in validation.schema_errors:
            if isinstance(err, dict):
                errors.append(err)
            else:
                errors.append({"file": "", "path": "", "message": str(err)})
        for err in validation.integrity_errors:
            if isinstance(err, dict):
                errors.append(err)
            else:
                errors.append({"file": "", "path": "", "message": str(err)})
        if errors:
            click.echo(format_validation_errors(errors))
        sys.exit(1)
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


@main.command("render")
@click.argument("spec")
@click.option(
    "--combined", is_flag=True, help="Render as single combined document"
)
@click.pass_context
def render_cmd(ctx: click.Context, spec: str, combined: bool) -> None:
    """Render spec as markdown."""
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        campaign = resolve_campaign(campaign_dir)
        spec_dir = resolve_spec(campaign, spec)
        session = SpecSession.resume(spec_dir)
        try:
            result = session.render(combined=combined)
        except (CampaignError, SessionError):
            raise
        except Exception:
            # Fallback: read spec markdown files directly when the
            # afspec rendering backend is unavailable.
            md_files = sorted(
                f
                for f in spec_dir.iterdir()
                if f.is_file()
                and f.suffix == ".md"
                and not f.name.startswith("_")
            )
            if combined:
                result = "\n\n".join(f.read_text() for f in md_files)
            else:
                result = {f.name: f.read_text() for f in md_files}

        if isinstance(result, str):
            click.echo(result)
        else:
            for artifact_name, content in result.items():
                click.echo(f"--- {artifact_name} ---")
                click.echo(content)
                click.echo()
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


@main.command("show")
@click.argument("spec")
@click.option("--artifact", default=None, help="Artifact name to display")
@click.pass_context
def show_cmd(
    ctx: click.Context, spec: str, artifact: str | None
) -> None:
    """Display an artifact or session state."""
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        campaign = resolve_campaign(campaign_dir)
        spec_dir = resolve_spec(campaign, spec)

        if artifact:
            artifact_path = spec_dir / artifact
            if not artifact_path.exists():
                available = sorted(
                    f.name
                    for f in spec_dir.iterdir()
                    if f.is_file() and not f.name.startswith("_")
                )
                click.echo(
                    f"Error: Artifact '{artifact}' not found. "
                    f"Available: {', '.join(available)}",
                    err=True,
                )
                sys.exit(1)
            click.echo(artifact_path.read_text())
        else:
            data = _read_session_data(spec_dir)
            click.echo(f"Spec: {spec_dir.name}")
            click.echo(f"State: {data.get('state', 'unknown')}")
            click.echo(f"Mode: {data.get('mode', 'interactive')}")
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


@main.command("status")
@click.argument("spec", required=False)
@click.pass_context
def status_cmd(ctx: click.Context, spec: str | None) -> None:
    """Print session state."""
    try:
        campaign_dir = ctx.obj["campaign_dir"]
        campaign = resolve_campaign(campaign_dir)

        if spec:
            spec_dir = resolve_spec(campaign, spec)
            data = _read_session_data(spec_dir)
            click.echo(f"Spec: {spec_dir.name}")
            click.echo(f"State: {data.get('state', 'unknown')}")
            click.echo(f"Mode: {data.get('mode', 'interactive')}")
            a_count = data.get(
                "assessment_count",
                len(data.get("assessment_history", [])),
            )
            q_count = data.get(
                "qa_count", len(data.get("qa_exchanges", []))
            )
            click.echo(f"Assessment count: {a_count}")
            click.echo(f"Q&A count: {q_count}")
            artifacts = sorted(
                f.name
                for f in spec_dir.iterdir()
                if f.is_file()
                and not f.name.startswith("_")
                and not f.name.startswith(".")
            )
            click.echo(
                f"Artifacts: {', '.join(artifacts) if artifacts else 'none'}"
            )
        else:
            spec_dirs = campaign.specs()
            if not spec_dirs:
                click.echo("Campaign is empty. No specs found.")
                return

            headers = ["#", "Name", "State"]
            rows: list[list[str]] = []
            for sd in spec_dirs:
                match = _SPEC_DIR_RE.match(sd.name)
                if match:
                    num, sname = match.group(1), match.group(2)
                else:
                    num, sname = "??", sd.name
                data = _read_session_data(sd)
                rows.append([num, sname, data.get("state", "unknown")])

            click.echo(format_table(headers, rows))
    except (CampaignError, SessionError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Internal error: {exc}", err=True)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Skill installation command
# ---------------------------------------------------------------------------


@main.command("install-skill")
@click.option(
    "--target",
    type=click.Choice(["claude", "gemini"]),
    default=None,
    help="Target agent CLI (auto-detected if omitted)",
)
def install_skill(target: str | None) -> None:
    """Install the spec skill to an agent CLI."""
    from spec_cli.skill import AGENT_TARGETS, SKILL_FILE_PATH, detect_agent_cli

    try:
        # Verify source file exists (guards against corrupt installation).
        if not SKILL_FILE_PATH.exists():
            raise SpeclibError(
                f"Skill source file not found at {SKILL_FILE_PATH}. "
                "The speclib package may be incomplete or corrupted."
            )

        # Determine target agent CLI.
        if target is None:
            target = detect_agent_cli()
            if target is None:
                supported = ", ".join(AGENT_TARGETS)
                click.echo(
                    f"Error: No supported agent CLI detected. "
                    f"Supported targets: {supported}\n"
                    f"Use --target to specify one (e.g. "
                    f"--target claude or --target gemini).",
                    err=True,
                )
                sys.exit(1)

        # Resolve destination path.
        home = Path.home()
        skill_dir = home / AGENT_TARGETS[target]
        dest = skill_dir / "spec.md"

        # Create skill directory if needed.
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Determine if this is an update.
        is_update = dest.exists()

        # Copy skill file.
        shutil.copy2(SKILL_FILE_PATH, dest)

        # Report success.
        action = "Updated" if is_update else "Installed"
        click.echo(f"{action} spec skill to {dest}")
    except SpeclibError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


# Alias for test compatibility and alternate import style.
cli = main
