"""Pytest fixtures for snackbox tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with minimal structure."""
    # Create pyproject.toml
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""[tool.poetry]
name = "testapp"
version = "1.2.3"
description = "Test application"

[tool.poetry.dependencies]
python = ">=3.10"
""")

    # Create snackbox.yaml
    config = tmp_path / "snackbox.yaml"
    config.write_text("""app:
  name: "Test App"
  slug: "testapp"
  version_from: "pyproject.toml"

python:
  version: "3.12.10"

build:
  extra_deps: []

launcher:
  entry_point: "testapp"
  console: "yes"

assets: []

version:
  git_hash: false
  dirty_flag: false
  save_patch: false

installer:
  enabled: false
""")

    return tmp_path


@pytest.fixture
def tmp_cache(tmp_path: Path) -> Path:
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def sample_config_yaml() -> str:
    """Return a sample snackbox.yaml content."""
    return """app:
  name: "Sample App"
  slug: "sampleapp"
  version_from: "pyproject.toml"
  icon: "icon.ico"

python:
  version: "3.12.10"
  arch: "amd64"

build:
  extra_deps:
    - "requests>=2.0"

launcher:
  entry_point: "sampleapp.main"
  console: "attach"
  env:
    DEBUG: "1"

assets:
  - "README.md:README.md"
  - "config.yaml"

version:
  git_hash: true
  dirty_flag: true
  save_patch: true

installer:
  enabled: true
  publisher: "Test Publisher"
  url: "https://example.com"
  install_dir: "{localappdata}\\\\SampleApp"
  add_to_path: true
  desktop_shortcut: false
  start_menu: true
  output_dir: "build/installer"
"""
