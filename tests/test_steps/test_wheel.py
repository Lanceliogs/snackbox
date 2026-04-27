"""Tests for wheel building step."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from snackbox.config import load_config
from snackbox.errors import BuildError
from snackbox.steps.wheel import (
    _run_custom_command,
    _run_hatch_build,
    _run_pip_build,
    _run_poetry_build,
    build_wheel,
)


class TestRunPoetryBuild:
    def test_success(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            _run_poetry_build(tmp_path)
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert cmd == ["poetry", "build", "-f", "wheel"]

    def test_failure(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="error")
            with pytest.raises(BuildError, match="poetry build failed"):
                _run_poetry_build(tmp_path)

    def test_not_found(self, tmp_path: Path):
        with patch("subprocess.run", side_effect=FileNotFoundError), \
             pytest.raises(BuildError, match="poetry not found"):
            _run_poetry_build(tmp_path)


class TestRunPipBuild:
    def test_success(self, tmp_path: Path):
        (tmp_path / "dist").mkdir()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            _run_pip_build(tmp_path)
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "pip" in cmd
            assert "wheel" in cmd


class TestRunHatchBuild:
    def test_success(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            _run_hatch_build(tmp_path)
            cmd = mock_run.call_args[0][0]
            assert cmd == ["hatch", "build", "-t", "wheel"]


class TestRunCustomCommand:
    def test_success(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            _run_custom_command("python -m build", tmp_path)
            mock_run.assert_called_once()
            assert mock_run.call_args[1]["shell"] is True

    def test_failure(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="error")
            with pytest.raises(BuildError, match="Custom build command failed"):
                _run_custom_command("failing-command", tmp_path)


class TestBuildWheel:
    def test_finds_built_wheel(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        dist_dir = tmp_project / "dist"
        wheel_file = dist_dir / "testapp-1.0.0-py3-none-any.whl"

        def fake_build(project_root):
            # Simulate build creating the wheel
            dist_dir.mkdir(exist_ok=True)
            wheel_file.write_text("fake wheel")

        with patch("snackbox.steps.wheel._run_poetry_build", side_effect=fake_build):
            messages = []
            result = build_wheel(config, echo=messages.append)

        assert result == wheel_file
        assert "Building wheel" in messages[0]

    def test_no_wheel_found(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        
        # Ensure dist dir exists but is empty
        dist_dir = tmp_project / "dist"
        dist_dir.mkdir(exist_ok=True)
        for f in dist_dir.glob("*.whl"):
            f.unlink()

        with patch("snackbox.steps.wheel._run_poetry_build"), \
             pytest.raises(BuildError, match="No wheel found"):
            build_wheel(config, echo=lambda x: None)

    def test_uses_custom_command(self, tmp_project: Path):
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace(
            'backend: "poetry"',
            'backend: "poetry"\n    backend_command: "custom build"'
        )
        config_file.write_text(content)
        
        config = load_config(config_file)
        dist_dir = tmp_project / "dist"
        wheel_file = dist_dir / "test-1.0.0-py3-none-any.whl"

        def fake_custom(cmd, project_root):
            dist_dir.mkdir(exist_ok=True)
            wheel_file.write_text("fake")

        with patch("snackbox.steps.wheel._run_custom_command", side_effect=fake_custom) as mock_custom:
            build_wheel(config, echo=lambda x: None)
            mock_custom.assert_called_once()
