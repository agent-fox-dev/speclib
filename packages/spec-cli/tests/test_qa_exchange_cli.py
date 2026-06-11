"""CLI test for QA exchange question export (TS-07-6).

This test imports from both speclib and spec_cli, so per 10-REQ-4.E1 it
belongs in the spec-cli test directory.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from spec_cli.cli import main
from speclib.campaign import Campaign


class TestQAExchangeQuestionExportCLI:
    """TS-07-6: Question export unchanged — CLI verification."""

    def test_ts07_6_question_export_unchanged(
        self,
        tmp_path: Path,
    ) -> None:
        """TS-07-6: Question export unchanged.

        Requirement: 07-REQ-3.1
        Verifies that refine without --answers still outputs only
        questions and answer template, with no qa_exchanges data.
        """
        # Set up campaign with a spec that has qa_exchanges populated
        camp_dir = tmp_path / "camp_export"
        Campaign.create(camp_dir, "Test", "Desc")
        spec_dir = camp_dir / "01_test_spec"
        spec_dir.mkdir()
        (spec_dir / "prd.md").write_text("# PRD\nContent.")
        (spec_dir / "_session.json").write_text(json.dumps({
            "state": "assessing",
            "prd_path": "prd.md",
            "assessment_history": [
                {
                    "quality": "needs_refinement",
                    "summary": "Needs work",
                    "gaps": [],
                    "questions": [
                        {
                            "id": "q1",
                            "text": "What?",
                            "context": "C",
                            "options": [],
                            "required": True,
                        }
                    ],
                }
            ],
            "qa_exchanges": [
                {
                    "assessment_index": 0,
                    "answers": {"q0": "prev answer"},
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            ],
            "generated_artifacts": [],
            "mode": "interactive",
        }))

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--campaign-dir", str(camp_dir), "refine", "01"],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert set(data.keys()) == {"questions", "answers"}
