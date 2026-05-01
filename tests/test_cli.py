"""Tests for CLI commands."""

import re
from pathlib import Path

from typer.testing import CliRunner

from snackbox.cli import _generate_guid, app

runner = CliRunner()


class TestGenerateGuid:
    def test_format(self):
        guid = _generate_guid()
        # Should be in format {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
        pattern = r"^\{[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\}$"
        assert re.match(pattern, guid), f"GUID format invalid: {guid}"

    def test_uppercase(self):
        guid = _generate_guid()
        # Should be uppercase (excluding the braces and dashes)
        hex_chars = guid.replace("{", "").replace("}", "").replace("-", "")
        assert hex_chars == hex_chars.upper()

    def test_uniqueness(self):
        guids = [_generate_guid() for _ in range(100)]
        assert len(set(guids)) == 100, "GUIDs should be unique"


class TestGuidCommand:
    def test_guid_command(self):
        result = runner.invoke(app, ["guid"])
        assert result.exit_code == 0
        pattern = r"^\{[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\}$"
        assert re.match(pattern, result.output.strip())


class TestInitCommand:
    def test_init_creates_config(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Created" in result.output
        assert (tmp_path / "snackbox.yaml").exists()

    def test_init_with_generate_guid(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--generate-guid"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Generated AppId:" in result.output

        config_content = (tmp_path / "snackbox.yaml").read_text()
        assert "app_guid:" in config_content
        assert "{" in config_content

    def test_init_refuses_overwrite(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "snackbox.yaml").write_text("existing: config")
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_init_force_overwrites(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "snackbox.yaml").write_text("existing: config")
        result = runner.invoke(app, ["init", "--force"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Created" in result.output
