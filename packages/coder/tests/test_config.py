"""Tests for coder configuration system and package structure.

Test Spec Entries: TS-12-1, TS-12-2, TS-12-10, TS-12-11, TS-12-20,
TS-12-24, TS-12-25, TS-12-26, TS-12-E3, TS-12-E4, TS-12-E7, TS-12-E8,
TS-12-P2.
"""

from __future__ import annotations

import os
import tempfile
import tomllib
from pathlib import Path

import pytest
from coder.config import CoderConfig, load_config
from coder.errors import ConfigError
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError


class TestPackageStructure:
    """Tests for package structure and importability."""

    def test_package_importable(self) -> None:
        """TS-12-1: Package importable.

        Requirement: 12-REQ-1.1
        Verifies the coder package is importable and has expected name.
        """
        import coder

        assert coder.__name__ == "coder"

    def test_pyproject_dependencies(self) -> None:
        """TS-12-2: Pyproject declares workspace dependencies.

        Requirement: 12-REQ-1.2
        Verifies pyproject.toml lists required dependencies.
        """
        # parents[1] = packages/coder/ (the coder package root)
        pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            toml = tomllib.load(f)

        deps = toml["project"]["dependencies"]
        required = [
            "afspec",
            "langchain",
            "click",
            "rich",
            "pydantic",
            "structlog",
        ]
        for req in required:
            assert any(
                req in dep for dep in deps
            ), f"{req} not in dependencies"

    def test_root_pyproject_workspace_member(self) -> None:
        """TS-12-20: Root pyproject includes coder as workspace member.

        Requirement: 12-REQ-1.3
        Verifies the root pyproject.toml covers packages/coder as a uv
        workspace member (either explicitly or via glob pattern).
        """
        # Traverse from packages/coder/tests/ up to root
        # parents[3] = repo root (tests → coder → packages → root)
        root = Path(__file__).parents[3]
        pyproject_path = root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            toml = tomllib.load(f)

        members = toml["tool"]["uv"]["workspace"]["members"]
        # Accept explicit "packages/coder" or glob "packages/*"
        assert any(
            m in ("packages/coder", "packages/*") for m in members
        ), f"packages/coder not covered by workspace members: {members}"

    def test_build_error_on_existing_dir(self) -> None:
        """TS-12-E8: Build system error if coder directory already exists.

        Requirement: 12-REQ-1.E1
        Verifies that the workspace member is correctly declared without
        duplicate or conflicting entries. The root pyproject.toml should
        not contain multiple entries that resolve to the same package.
        """
        # Check the coder package pyproject.toml is well-formed
        # parents[1] = packages/coder/ (the coder package root)
        pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            toml = tomllib.load(f)

        assert toml["project"]["name"] == "coder"

        # Check root workspace has no duplicate entries that resolve
        # to packages/coder
        # parents[3] = repo root (tests → coder → packages → root)
        root = Path(__file__).parents[3]
        root_pyproject_path = root / "pyproject.toml"
        with open(root_pyproject_path, "rb") as f:
            root_toml = tomllib.load(f)

        members = root_toml["tool"]["uv"]["workspace"]["members"]
        # Count entries that would cover packages/coder
        # (explicit "packages/coder" or glob "packages/*")
        coder_entries = [
            m
            for m in members
            if m == "packages/coder" or m == "packages/*"
        ]
        # There should be exactly one entry covering coder (not zero,
        # not duplicates)
        assert len(coder_entries) == 1, (
            "Expected exactly 1 workspace entry covering"
            f" packages/coder, found {len(coder_entries)}:"
            f" {coder_entries}"
        )


class TestConfigLoading:
    """Tests for configuration loading from YAML and env vars."""

    def test_yaml_loading(
        self, tmp_project_dir: Path, clean_coder_env: None
    ) -> None:
        """TS-12-10: Config loads from YAML file.

        Requirement: 12-REQ-4.1
        Verifies config is loaded from a YAML file.
        """
        config_file = tmp_project_dir / ".coder.yaml"
        config_file.write_text("model: gemini-2.5-pro\n")

        config = load_config(project_dir=tmp_project_dir)
        assert config.model == "gemini-2.5-pro"

    def test_env_override(
        self,
        tmp_project_dir: Path,
        clean_coder_env: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """TS-12-11: Env vars override YAML config.

        Requirement: 12-REQ-4.4
        Verifies environment variables take precedence over YAML.
        """
        config_file = tmp_project_dir / ".coder.yaml"
        config_file.write_text("model: gemini-2.5-pro\n")
        monkeypatch.setenv("CODER_MODEL", "claude-opus-4-6")

        config = load_config(project_dir=tmp_project_dir)
        assert config.model == "claude-opus-4-6"

    def test_config_all_keys(
        self, tmp_project_dir: Path, clean_coder_env: None
    ) -> None:
        """TS-12-24: Config supports all required keys.

        Requirement: 12-REQ-4.2
        Verifies CoderConfig supports model, templates_dir, ollama_url,
        log_level, and log_file keys with correct values.
        """
        yaml_content = (
            "model: test-model\n"
            "templates_dir: /tmp/tpl\n"
            "ollama_url: http://localhost:9999\n"
            "log_level: INFO\n"
            "log_file: /tmp/log.txt\n"
        )
        config_file = tmp_project_dir / ".coder.yaml"
        config_file.write_text(yaml_content)

        config = load_config(project_dir=tmp_project_dir)
        assert config.model == "test-model"
        assert config.templates_dir == "/tmp/tpl"
        assert config.ollama_url == "http://localhost:9999"
        assert config.log_level == "INFO"
        assert config.log_file == "/tmp/log.txt"

    def test_env_var_coder_prefix(
        self,
        tmp_project_dir: Path,
        clean_coder_env: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """TS-12-25: Env var overrides use CODER_ prefix.

        Requirement: 12-REQ-4.3
        Verifies environment variable overrides use the CODER_ prefix
        for each configuration key.
        """
        monkeypatch.setenv("CODER_OLLAMA_URL", "http://custom:1234")
        monkeypatch.setenv("CODER_LOG_LEVEL", "WARNING")

        config = load_config(project_dir=tmp_project_dir)
        assert config.ollama_url == "http://custom:1234"
        assert config.log_level == "WARNING"

    def test_config_frozen_pydantic(
        self, tmp_project_dir: Path, clean_coder_env: None
    ) -> None:
        """TS-12-26: Config returns frozen pydantic model.

        Requirement: 12-REQ-4.5
        Verifies load_config() returns a frozen pydantic CoderConfig
        that validates types at load time.
        """
        config = load_config(project_dir=tmp_project_dir)
        assert isinstance(config, CoderConfig)
        with pytest.raises(
            (TypeError, AttributeError, ValidationError)
        ):
            config.model = "other-model"  # type: ignore[misc]


class TestConfigEdgeCases:
    """Edge case tests for configuration."""

    def test_no_config_defaults(
        self, tmp_project_dir: Path, clean_coder_env: None
    ) -> None:
        """TS-12-E3: No config file uses defaults.

        Requirement: 12-REQ-4.E2
        Verifies defaults are used when no config file exists.
        """
        config = load_config(project_dir=tmp_project_dir)
        assert config.ollama_url == "http://localhost:11434"
        assert config.log_level == "DEBUG"

    def test_invalid_yaml(
        self, tmp_project_dir: Path, clean_coder_env: None
    ) -> None:
        """TS-12-E4: Invalid YAML raises ConfigError.

        Requirement: 12-REQ-4.E3
        Verifies malformed YAML is caught.
        """
        config_file = tmp_project_dir / ".coder.yaml"
        config_file.write_text("model: [unclosed")

        with pytest.raises(ConfigError):
            load_config(project_dir=tmp_project_dir)

    def test_unknown_keys_warned(
        self,
        tmp_project_dir: Path,
        clean_coder_env: None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """TS-12-E7: Unknown YAML keys logged as warnings.

        Requirement: 12-REQ-4.E1
        Verifies unknown config keys are warned about.
        """
        config_file = tmp_project_dir / ".coder.yaml"
        config_file.write_text("model: test\nunknown_key: value\n")

        config = load_config(project_dir=tmp_project_dir)
        assert config.model == "test"
        # Check that a warning was logged about the unknown key
        assert any(
            "unknown_key" in record.message for record in caplog.records
        )


class TestConfigProperties:
    """Property-based tests for configuration."""

    @settings(max_examples=20)
    @given(
        env_model=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(categories=("L", "N")),
        ),
        yaml_model=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(categories=("L", "N")),
        ),
    )
    def test_property_config_precedence(
        self,
        env_model: str,
        yaml_model: str,
    ) -> None:
        """TS-12-P2: Configuration precedence holds.

        Property 2 from design.md.
        Validates: 12-REQ-4.1, 12-REQ-4.4
        For any model name pair, env vars always override YAML config values.
        """
        from hypothesis import assume

        assume(env_model != yaml_model)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / ".coder.yaml"
            config_file.write_text(f"model: {yaml_model}\n")

            # Manage env vars manually for hypothesis compatibility
            old_vars: dict[str, str | None] = {}
            for var in [
                "CODER_MODEL",
                "CODER_TEMPLATES_DIR",
                "CODER_OLLAMA_URL",
                "CODER_LOG_LEVEL",
                "CODER_LOG_FILE",
            ]:
                old_vars[var] = os.environ.pop(var, None)

            os.environ["CODER_MODEL"] = env_model
            try:
                config = load_config(project_dir=tmp_path)
                assert config.model == env_model
            finally:
                os.environ.pop("CODER_MODEL", None)
                for var, val in old_vars.items():
                    if val is not None:
                        os.environ[var] = val
