"""Tests for version stamping step."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from snackbox.config import load_config
from snackbox.errors import BuildError
from snackbox.steps.version import (
    _get_git_hash,
    _get_version_from_git_tag,
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

    def test_version_with_inline_comment(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nversion = "1.2.3"  # some comment\n')

        version = _read_pyproject_version(tmp_path, "pyproject.toml")
        assert version == "1.2.3"

    def test_file_not_found(self, tmp_path: Path):
        with pytest.raises(BuildError, match="Version source not found"):
            _read_pyproject_version(tmp_path, "nonexistent.toml")

    def test_version_not_found(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "test"\n')

        with pytest.raises(BuildError, match="Could not find version"):
            _read_pyproject_version(tmp_path, "pyproject.toml")


class TestGetVersionFromGitTag:
    def test_on_tag_returns_version(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="v1.2.3-0-gabcdef1\n")
            result = _get_version_from_git_tag(tmp_path)
        assert result == "1.2.3"

    def test_after_tag_returns_post_version(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="v1.2.3-5-gabcdef1\n")
            result = _get_version_from_git_tag(tmp_path)
        assert result == "1.2.3.post5"

    def test_strips_v_prefix(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="v0.1.0-0-g1234567\n")
            result = _get_version_from_git_tag(tmp_path)
        assert result == "0.1.0"

    def test_works_without_v_prefix(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="0.1.0-3-g1234567\n")
            result = _get_version_from_git_tag(tmp_path)
        assert result == "0.1.0.post3"

    def test_returns_none_when_no_tags(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stdout="")
            result = _get_version_from_git_tag(tmp_path)
        assert result is None


class TestGetGitHash:
    def test_returns_hash_in_git_repo(self, tmp_path: Path):
        # Mock successful git command
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="abc1234\n")
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
            mock_run.return_value = MagicMock(returncode=0, stdout=" M modified_file.py\n")
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

        with (
            patch("snackbox.steps.version._get_git_hash", return_value="abc1234"),
            patch("snackbox.steps.version._is_git_dirty", return_value=False),
        ):
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

        with (
            patch("snackbox.steps.version._get_git_hash", return_value="abc1234"),
            patch("snackbox.steps.version._is_git_dirty", return_value=True),
            patch("snackbox.steps.version._save_dirty_patch"),
        ):
            version = stamp_version(config, release_dir, echo=lambda x: None)

        assert version == "1.2.3.abc1234.dirty"

    def test_version_from_git(self, tmp_project: Path):
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace('version_from: "pyproject.toml"', 'version_from: "git"')
        config_file.write_text(content)

        config = load_config(config_file)
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        with (
            patch("snackbox.steps.version._get_version_from_git_tag", return_value="2.0.0.post3"),
            patch("snackbox.steps.version._is_git_dirty", return_value=False),
        ):
            version = stamp_version(config, release_dir, echo=lambda x: None)

        assert version == "2.0.0.post3"

    def test_version_from_git_no_tags(self, tmp_project: Path):
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace('version_from: "pyproject.toml"', 'version_from: "git"')
        config_file.write_text(content)

        config = load_config(config_file)
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        with (
            patch("snackbox.steps.version._get_version_from_git_tag", return_value=None),
            pytest.raises(BuildError, match="No git tags found"),
        ):
            stamp_version(config, release_dir, echo=lambda x: None)
