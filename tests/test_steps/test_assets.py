"""Tests for asset copying step."""

from pathlib import Path

import pytest

from snackbox.config import load_config
from snackbox.errors import BuildError
from snackbox.steps.assets import copy_assets


class TestCopyAssets:
    def test_no_assets(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        messages = []
        copy_assets(config, release_dir, echo=messages.append)

        # Should not print anything when no assets
        assert messages == []

    def test_copy_single_file(self, tmp_project: Path):
        # Create a source file
        (tmp_project / "source.txt").write_text("content")

        # Update config to include asset
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace("assets: []", 'assets:\n  - "source.txt:dest.txt"')
        config_file.write_text(content)

        config = load_config(config_file)
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        messages = []
        copy_assets(config, release_dir, echo=messages.append)

        assert (release_dir / "dest.txt").exists()
        assert (release_dir / "dest.txt").read_text() == "content"

    def test_copy_directory(self, tmp_project: Path):
        # Create source directory with files
        src_dir = tmp_project / "src_dir"
        src_dir.mkdir()
        (src_dir / "file1.txt").write_text("content1")
        (src_dir / "subdir").mkdir()
        (src_dir / "subdir" / "file2.txt").write_text("content2")

        # Update config
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace("assets: []", 'assets:\n  - "src_dir:dst_dir"')
        config_file.write_text(content)

        config = load_config(config_file)
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        copy_assets(config, release_dir, echo=lambda x: None)

        assert (release_dir / "dst_dir" / "file1.txt").exists()
        assert (release_dir / "dst_dir" / "subdir" / "file2.txt").exists()

    def test_asset_not_found(self, tmp_project: Path):
        # Update config to include non-existent asset
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace("assets: []", 'assets:\n  - "nonexistent.txt"')
        config_file.write_text(content)

        config = load_config(config_file)
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        with pytest.raises(BuildError, match="Asset not found"):
            copy_assets(config, release_dir, echo=lambda x: None)

    def test_copy_to_nested_destination(self, tmp_project: Path):
        # Create source file
        (tmp_project / "file.txt").write_text("content")

        # Update config with nested destination
        config_file = tmp_project / "snackbox.yaml"
        content = config_file.read_text()
        content = content.replace("assets: []", 'assets:\n  - "file.txt:subdir/nested/file.txt"')
        config_file.write_text(content)

        config = load_config(config_file)
        release_dir = tmp_project / "release"
        release_dir.mkdir()

        copy_assets(config, release_dir, echo=lambda x: None)

        assert (release_dir / "subdir" / "nested" / "file.txt").exists()
