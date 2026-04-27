"""Tests for version stamping step."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from snackbox.config import load_config
from snackbox.errors import BuildError
from snackbox.steps.version import (
    _get_git_hash,
    _is_git_dirty,
    _read_pyproject_version,
    stamp_version,
)


class TestReadPyprojectVersion:
    def test_poetry_format(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nversion = "1.2.3"\n')
        
        version = _read_pyproject_version(tmp_path, "pyproject.toml")
        assert version == "1.2.3"

    def test_pep621_format(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "2.0.0"\n')
        
        version = _read_pyproject_version(tmp_path, "pyproject.toml")
        assert version == "2.0.0"

    def test_file_not_found(self, tmp_path: Path):
        with pytest.raises(BuildError, match="Version source not found"):
            _read_pyproject_version(tmp_path, "nonexistent.toml")

    def test_version_not_found(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "test"\n')
        
        with pytest.raises(BuildError, match="Could not find version"):
            _read_pyproject_version(tmp_path, "pyproject.toml")


class TestGetGitHash:
    def test_returns_hash_in_git_repo(self, tmp_path: Path):
        # Mock successful git command
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc1234\n"
            )
            result = _get_git_hash(tmp_path)
            assert result == "abc1234"

    def test_returns_none_when_not_git_repo(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stdout="")
            result = _get_git_hash(tmp_path)
            assert result is None

    def test_returns_none_on_error(self, tmp_path: Path):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _get_git_hash(tmp_path)
            assert result is None


class TestIsGitDirty:
    def test_clean_repo(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            assert _is_git_dirty(tmp_path) is False

    def test_dirty_repo(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=" M modified_file.py\n"
            )
            assert _is_git_dirty(tmp_path) is True


class TestStampVersion:
    def test_basic_version(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        messages = []
        version = stamp_version(config, release_dir, echo=messages.append)

        assert version == "1.2.3"
        assert (release_dir / "version.txt").read_text().strip() == "1.2.3"

    def test_version_with_git_hash(self, tmp_project: Path):
        # Enable git_hash in config
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace("git_hash: false", "git_hash: true")
        config_file.write_text(content)

        config = load_config(config_file)
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        with patch("snackbox.steps.version._get_git_hash", return_value="abc1234"), \
             patch("snackbox.steps.version._is_git_dirty", return_value=False):
            version = stamp_version(config, release_dir, echo=lambda x: None)

        assert version == "1.2.3.abc1234"

    def test_version_with_dirty_flag(self, tmp_project: Path):
        # Enable dirty_flag in config
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace("git_hash: false", "git_hash: true")
        content = content.replace("dirty_flag: false", "dirty_flag: true")
        config_file.write_text(content)

        config = load_config(config_file)
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        with patch("snackbox.steps.version._get_git_hash", return_value="abc1234"), \
             patch("snackbox.steps.version._is_git_dirty", return_value=True), \
             patch("snackbox.steps.version._save_dirty_patch"):
            version = stamp_version(config, release_dir, echo=lambda x: None)

        assert version == "1.2.3.abc1234.dirty"
