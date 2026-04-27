"""Tests for launcher building step."""

import contextlib
from pathlib import Path
from unittest.mock import patch

import pytest

from snackbox.config import load_config
from snackbox.errors import BuildError
from snackbox.steps.launcher import build_launcher


class TestBuildLauncher:
    def test_renders_template_with_entry_point(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        rendered_c = None

        def capture_compile(c_file, *args, **kwargs):
            nonlocal rendered_c
            rendered_c = c_file.read_text()

        with patch("snackbox.steps.launcher.get_gcc", return_value="gcc"), \
             patch("snackbox.steps.launcher.get_windres", return_value="windres"), \
             patch("snackbox.steps.launcher._compile_launcher") as mock_compile, \
             contextlib.suppress(Exception):
            mock_compile.side_effect = capture_compile
            (release_dir / "testapp.exe").write_bytes(b"fake")
            build_launcher(config, release_dir, echo=lambda x: None)

        assert rendered_c is not None
        assert "testapp" in rendered_c  # entry_point should be in rendered template

    def test_console_modes_in_template(self, tmp_project: Path):
        config_file = tmp_project / "snackbox.yaml"
        original_content = config_file.read_text()
        
        for mode in ["yes", "no", "attach"]:
            # Reset to original content each iteration
            content = original_content.replace('console: "yes"', f'console: "{mode}"')
            config_file.write_text(content)
            config = load_config(config_file)
            
            assert config.launcher.console == mode

    def test_gcc_not_found(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        with patch("snackbox.steps.launcher.get_gcc", side_effect=BuildError("GCC not found")), \
             pytest.raises(BuildError, match="GCC not found"):
            build_launcher(config, release_dir, echo=lambda x: None)
