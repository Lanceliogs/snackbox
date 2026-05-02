"""Tests for wheel building step."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from snackbox.config import load_config
from snackbox.errors import BuildError
from snackbox.steps.wheel import build_wheel


class TestBuildWheel:
    def test_finds_built_wheel(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        dist_dir = tmp_project / "dist"
        wheel_file = dist_dir / "testapp-1.0.0-py3-none-any.whl"

        def fake_build(*args, **kwargs):
            dist_dir.mkdir(exist_ok=True)
            wheel_file.write_text("fake wheel")
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=fake_build):
            messages = []
            result = build_wheel(config, echo=messages.append)

        assert result == wheel_file
        assert "Building wheel" in messages[0]

    def test_no_wheel_found(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")

        dist_dir = tmp_project / "dist"
        dist_dir.mkdir(exist_ok=True)
        for f in dist_dir.glob("*.whl"):
            f.unlink()

        with (
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
            pytest.raises(BuildError, match="No wheel found"),
        ):
            build_wheel(config, echo=lambda x: None)

    def test_build_failure(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")

        with (
            patch(
                "subprocess.run", return_value=MagicMock(returncode=1, stderr="error", stdout="")
            ),
            pytest.raises(BuildError, match="Wheel build failed"),
        ):
            build_wheel(config, echo=lambda x: None)
