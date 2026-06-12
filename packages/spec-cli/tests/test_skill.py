"""Tests for skill file content and structure.

Test Spec Entries: TS-05-1 through TS-05-13, TS-05-19 through TS-05-21,
TS-05-E4 through TS-05-E9, TS-05-P1, TS-05-P3.
"""

from __future__ import annotations

import re

# ===================================================================
# Helper: extract fenced code blocks from markdown
# ===================================================================


def _extract_fenced_code_blocks(content: str) -> list[str]:
    """Extract all fenced code block bodies from markdown content."""
    pattern = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
    return [m.group(1) for m in pattern.finditer(content)]


# ===================================================================
# TS-05-1: Skill file exists in package
# Requirement: 05-REQ-1.1
# ===================================================================


class TestSkillFileExists:
    """TS-05-1: Verify the skill file exists at the expected package path."""

    def test_skill_file_exists(self) -> None:
        """SKILL_FILE_PATH points to an existing, non-empty file."""
        from spec_cli.skill import SKILL_FILE_PATH

        assert SKILL_FILE_PATH.exists(), (
            f"Skill file must exist at {SKILL_FILE_PATH}"
        )
        assert SKILL_FILE_PATH.stat().st_size > 0, "Skill file must be non-empty"


# ===================================================================
# TS-05-2: Skill file has header section
# Requirement: 05-REQ-1.2
# ===================================================================


class TestSkillHeader:
    """TS-05-2: Verify skill file includes header with name and trigger."""

    def test_skill_header_has_name(self) -> None:
        """Skill file contains a top-level heading with 'spec'."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        # Check for a markdown heading containing spec (case-insensitive)
        assert re.search(r"^#\s+.*spec", content, re.IGNORECASE | re.MULTILINE), (
            "Skill file must contain a top-level heading with 'spec'"
        )

    def test_skill_header_has_trigger(self) -> None:
        """Skill file contains a 'Trigger' section or subsection."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        assert "trigger" in content.lower(), (
            "Skill file must contain a 'Trigger' section"
        )


# ===================================================================
# TS-05-3: Skill file documents all required commands
# Requirement: 05-REQ-1.3
# ===================================================================


class TestDocumentsAllCommands:
    """TS-05-3: Verify the skill file mentions all required spec CLI commands."""

    def test_documents_all_commands(self) -> None:
        """Skill file references all required spec commands."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        required_commands = [
            "spec init",
            "spec new",
            "spec assess",
            "spec refine",
            "spec accept",
            "spec generate",
            "spec status",
            "spec validate",
            "spec render",
        ]
        for cmd in required_commands:
            assert cmd in content, (
                f"Skill file must reference '{cmd}'"
            )


# ===================================================================
# TS-05-4: Skill file includes command examples
# Requirement: 05-REQ-1.4
# ===================================================================


class TestCommandExamples:
    """TS-05-4: Verify skill file includes usage examples per command."""

    def test_command_examples_in_code_blocks(self) -> None:
        """At least one code block example per required command."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        code_blocks = _extract_fenced_code_blocks(content)
        required_commands = [
            "init", "new", "assess", "refine", "accept",
            "generate", "status", "validate", "render",
        ]
        for cmd in required_commands:
            assert any(f"spec {cmd}" in block for block in code_blocks), (
                f"Skill file must include a code block example for 'spec {cmd}'"
            )


# ===================================================================
# TS-05-5: Skill file is valid markdown
# Requirement: 05-REQ-1.5
# ===================================================================


class TestValidMarkdown:
    """TS-05-5: Verify the skill file can be parsed as valid markdown."""

    def test_valid_markdown_fences(self) -> None:
        """All fenced code blocks are properly closed."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        fence_count = len(re.findall(r"^```", content, re.MULTILINE))
        assert fence_count % 2 == 0, (
            f"Unclosed code fences: found {fence_count} fence markers (must be even)"
        )


# ===================================================================
# TS-05-6: Interactive workflow described
# Requirement: 05-REQ-2.1
# ===================================================================


class TestInteractiveWorkflow:
    """TS-05-6: Verify the skill file describes the interactive workflow steps."""

    def test_interactive_workflow_described(self) -> None:
        """Skill file describes the interactive workflow with all key steps."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        assert "interactive" in content, "Must mention 'interactive'"
        assert "campaign" in content, "Must mention 'campaign'"
        assert "assess" in content, "Must mention 'assess'"
        assert "refine" in content, "Must mention 'refine'"
        assert "accept" in content, "Must mention 'accept'"
        assert "generate" in content, "Must mention 'generate'"


# ===================================================================
# TS-05-7: Assessment presentation instructions
# Requirement: 05-REQ-2.2
# ===================================================================


class TestAssessmentPresentation:
    """TS-05-7: Verify skill file instructs presenting assessment results."""

    def test_assessment_presentation_instructions(self) -> None:
        """Skill file instructs presenting assessment output to the user."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        assert "present" in content and "assessment" in content, (
            "Skill file must instruct presenting assessment results to the user"
        )


# ===================================================================
# TS-05-8: Accept-or-refine decision instructions
# Requirement: 05-REQ-2.3
# ===================================================================


class TestAcceptOrRefine:
    """TS-05-8: Verify the skill file instructs asking the user to accept or refine."""

    def test_accept_or_refine_instructions(self) -> None:
        """Skill file instructs asking the user whether to accept or refine."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        assert "accept" in content and "refin" in content, (
            "Skill file must mention both 'accept' and 'refine'"
        )
        has_interaction = "ask" in content or "prompt" in content or "user" in content
        assert has_interaction, (
            "Skill file must instruct agent to interact with user about accept/refine"
        )


# ===================================================================
# TS-05-9: One-shot workflow described
# Requirement: 05-REQ-3.1
# ===================================================================


class TestOneShotWorkflow:
    """TS-05-9: Verify the skill file describes the one-shot workflow."""

    def test_one_shot_workflow_described(self) -> None:
        """Skill file describes one-shot mode with --one-shot flag."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        assert "--one-shot" in content, (
            "Skill file must mention the '--one-shot' flag"
        )


# ===================================================================
# TS-05-10: One-shot result presentation
# Requirement: 05-REQ-3.2
# ===================================================================


class TestOneShotResult:
    """TS-05-10: Verify skill file instructs presenting one-shot result."""

    def test_one_shot_result_presentation(self) -> None:
        """Skill file instructs presenting the result after one-shot generation."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        has_one_shot = "one-shot" in content or "one_shot" in content
        assert has_one_shot, "Skill file must mention 'one-shot'"
        has_presentation = "review" in content or "present" in content
        assert has_presentation, (
            "Skill file must instruct presenting or reviewing the one-shot result"
        )


# ===================================================================
# TS-05-11: Question ID parsing instructions
# Requirement: 05-REQ-4.1
# ===================================================================


class TestQuestionIdParsing:
    """TS-05-11: Verify skill file instructs parsing question IDs."""

    def test_question_id_parsing_instructions(self) -> None:
        """Skill file contains instructions about parsing question IDs."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        assert "question" in content and "id" in content, (
            "Skill file must contain instructions about question IDs"
        )


# ===================================================================
# TS-05-12: Natural language question presentation
# Requirement: 05-REQ-4.2
# ===================================================================


class TestNaturalLanguageQuestions:
    """TS-05-12: Verify the skill file instructs presenting questions naturally."""

    def test_natural_language_question_presentation(self) -> None:
        """Skill file instructs presenting questions in natural language."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        has_style = "natural" in content or "conversational" in content
        assert has_style, (
            "Skill file must mention 'natural' or 'conversational' language"
        )
        assert "question" in content, "Skill file must mention 'question'"


# ===================================================================
# TS-05-13: Answer mapping to Question IDs
# Requirement: 05-REQ-4.3, 05-REQ-4.4
# ===================================================================


class TestAnswerMapping:
    """TS-05-13: Verify the skill file instructs mapping answers to Question IDs."""

    def test_answer_mapping_instructions(self) -> None:
        """Skill file instructs mapping answers with --answers and JSON."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        assert "--answers" in content, (
            "Skill file must mention the '--answers' flag"
        )
        assert "JSON" in content or "json" in content, (
            "Skill file must mention JSON format for answers"
        )


# ===================================================================
# TS-05-19: Error handling section in skill file
# Requirement: 05-REQ-6.1
# ===================================================================


class TestErrorHandlingSection:
    """TS-05-19: Verify the skill file includes an error handling section."""

    def test_error_handling_section(self) -> None:
        """Skill file contains an error handling section."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        assert "error handling" in content, (
            "Skill file must contain an 'Error Handling' section"
        )


# ===================================================================
# TS-05-20: Exit code checking instructions
# Requirement: 05-REQ-6.2
# ===================================================================


class TestExitCodeChecking:
    """TS-05-20: Verify the skill file instructs checking exit codes."""

    def test_exit_code_checking_instructions(self) -> None:
        """Skill file instructs checking exit codes or command success."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        has_exit_check = (
            "exit code" in content
            or "exit status" in content
            or "failed" in content
        )
        assert has_exit_check, (
            "Skill file must instruct checking exit codes or handling failures"
        )


# ===================================================================
# TS-05-21: Status check before operations
# Requirement: 05-REQ-6.3
# ===================================================================


class TestStatusCheck:
    """TS-05-21: Verify the skill file instructs checking session state."""

    def test_status_check_before_operations(self) -> None:
        """Skill file instructs using 'spec status' to check state."""
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        assert "spec status" in content, (
            "Skill file must reference 'spec status'"
        )
        has_state_ref = "state" in content.lower() or "status" in content.lower()
        assert has_state_ref, (
            "Skill file must reference session state or status"
        )


# ===================================================================
# Edge Case Tests
# ===================================================================


class TestEdgeCases:
    """Edge case tests for skill file content."""

    def test_ts05_e4_zero_questions(self) -> None:
        """TS-05-E4: Skill file instructs proceeding to accept when no questions exist.

        Requirement: 05-REQ-2.E1
        """
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        has_zero_questions = (
            "no question" in content
            or "zero question" in content
            or "no remaining" in content
        )
        assert has_zero_questions, (
            "Skill file must contain instructions for the zero-questions case"
        )

    def test_ts05_e5_one_shot_fallback(self) -> None:
        """TS-05-E5: Skill file instructs interactive fallback.

        Requirement: 05-REQ-3.E1
        """
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        assert "interactive" in content, "Must mention interactive mode"
        has_failure = "fail" in content or "error" in content
        assert has_failure, (
            "Skill file must mention failure or error in context of one-shot fallback"
        )

    def test_ts05_e6_af_spec_not_on_path(self) -> None:
        """TS-05-E6: Skill file instructs installing speclib.

        Requirement: 05-REQ-6.E1
        """
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        assert "install" in content and "speclib" in content, (
            "Skill file must contain instructions about installing speclib"
        )

    def test_ts05_e7_unsupported_command_handling(self) -> None:
        """TS-05-E7: Skill file instructs reporting unsupported commands to the user.

        Requirement: 05-REQ-1.E1
        """
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        has_unsupported = (
            "unsupported" in content
            or "not supported" in content
            or "not available" in content
        )
        assert has_unsupported, (
            "Skill file must mention unsupported or unavailable commands"
        )
        has_report = "report" in content or "inform" in content or "tell" in content
        assert has_report, (
            "Skill file must instruct agent to report unsupported commands to user"
        )

    def test_ts05_e8_ambiguous_answer_clarification(self) -> None:
        """TS-05-E8: Skill file instructs asking for clarification on ambiguous answers.

        Requirement: 05-REQ-4.E1
        """
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        assert "clarif" in content, (
            "Skill file must mention clarification for ambiguous answers"
        )
        has_mapping = (
            "map" in content
            or "match" in content
            or "which question" in content
        )
        assert has_mapping, (
            "Skill file must mention mapping or matching answers to questions"
        )

    def test_ts05_e9_partial_answers_handling(self) -> None:
        """TS-05-E9: Skill file instructs handling partial answers.

        Requirement: 05-REQ-4.E2
        """
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text().lower()
        has_partial = (
            "partial" in content
            or "some question" in content
            or "unanswered" in content
        )
        assert has_partial, (
            "Skill file must mention partial answers or unanswered questions"
        )


# ===================================================================
# Property Tests
# ===================================================================


class TestProperties:
    """Property tests for skill file."""

    def test_ts05_p1_property_package_complete(self) -> None:
        """TS-05-P1: Skill file is package-complete.

        Property 1 from design.md.
        Validates: 05-REQ-1.1.
        For any import of speclib.skill, SKILL_FILE_PATH exists and is non-empty.
        """
        from spec_cli.skill import SKILL_FILE_PATH

        assert SKILL_FILE_PATH.exists(), (
            f"Skill file must exist at {SKILL_FILE_PATH}"
        )
        assert SKILL_FILE_PATH.stat().st_size > 0, "Skill file must be non-empty"

    def test_ts05_p3_property_all_commands_documented(self) -> None:
        """TS-05-P3: All required commands documented.

        Property 3 from design.md.
        Validates: 05-REQ-1.3, 05-REQ-1.4.
        For any required command, 'spec {command}' appears in the skill file.
        """
        from spec_cli.skill import SKILL_FILE_PATH

        content = SKILL_FILE_PATH.read_text()
        required_commands = [
            "init", "new", "assess", "refine", "accept",
            "generate", "status", "validate", "render",
        ]
        for cmd in required_commands:
            assert f"spec {cmd}" in content, (
                f"Skill file must document 'spec {cmd}'"
            )
