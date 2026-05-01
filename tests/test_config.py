"""Tests for config loading and validation."""

from pathlib import Path

import pytest

from snackbox.config import (
    _parse_app,
    _parse_assets,
    _parse_build,
    _parse_installer,
    _parse_launcher,
    _parse_python,
    _parse_version,
    load_config,
)
from snackbox.errors import ConfigError


class TestParseApp:
    def test_valid_app(self):
        data = {"app": {"name": "My App", "slug": "myapp"}}
        app = _parse_app(data)
        assert app.name == "My App"
        assert app.slug == "myapp"
        assert app.version_from == "pyproject.toml"
        assert app.icon is None

    def test_with_icon(self):
        data = {"app": {"name": "My App", "slug": "myapp", "icon": "icon.ico"}}
        app = _parse_app(data)
        assert app.icon == "icon.ico"

    def test_missing_app_section(self):
        with pytest.raises(ConfigError, match="Missing required 'app' section"):
            _parse_app({})

    def test_missing_name(self):
        with pytest.raises(ConfigError, match="Missing required field 'name'"):
            _parse_app({"app": {"slug": "myapp"}})

    def test_missing_slug(self):
        with pytest.raises(ConfigError, match="Missing required field 'slug'"):
            _parse_app({"app": {"name": "My App"}})


class TestParsePython:
    def test_defaults(self):
        py = _parse_python({})
        assert py.version == "3.12.10"
        assert py.arch == "amd64"

    def test_custom_values(self):
        data = {"python": {"version": "3.11.5", "arch": "win32"}}
        py = _parse_python(data)
        assert py.version == "3.11.5"
        assert py.arch == "win32"


class TestParseBuild:
    def test_defaults(self):
        build = _parse_build({})
        assert build.backend == "poetry"
        assert build.backend_command is None
        assert build.extra_deps == []

    def test_custom_backend(self):
        data = {"build": {"wheel": {"backend": "hatch"}}}
        build = _parse_build(data)
        assert build.backend == "hatch"

    def test_extra_deps(self):
        data = {"build": {"extra_deps": ["requests", "click>=8.0"]}}
        build = _parse_build(data)
        assert build.extra_deps == ["requests", "click>=8.0"]


class TestParseLauncher:
    def test_valid_launcher(self):
        data = {"launcher": {"entry_point": "myapp"}}
        launcher = _parse_launcher(data)
        assert launcher.entry_point == "myapp"
        assert launcher.console == "yes"
        assert launcher.env == {}

    def test_console_modes(self):
        for mode in ["yes", "no", "attach"]:
            data = {"launcher": {"entry_point": "myapp", "console": mode}}
            launcher = _parse_launcher(data)
            assert launcher.console == mode

    def test_console_bool_conversion(self):
        data = {"launcher": {"entry_point": "myapp", "console": True}}
        launcher = _parse_launcher(data)
        assert launcher.console == "yes"

        data = {"launcher": {"entry_point": "myapp", "console": False}}
        launcher = _parse_launcher(data)
        assert launcher.console == "no"

    def test_invalid_console_mode(self):
        data = {"launcher": {"entry_point": "myapp", "console": "invalid"}}
        with pytest.raises(ConfigError, match="Invalid console mode"):
            _parse_launcher(data)

    def test_env_vars(self):
        data = {"launcher": {"entry_point": "myapp", "env": {"DEBUG": "1"}}}
        launcher = _parse_launcher(data)
        assert launcher.env == {"DEBUG": "1"}

    def test_missing_launcher_section(self):
        with pytest.raises(ConfigError, match="Missing required 'launcher' section"):
            _parse_launcher({})


class TestParseAssets:
    def test_empty_assets(self):
        assets = _parse_assets({})
        assert assets == []

    def test_short_format_with_colon(self):
        data = {"assets": ["src/file.txt:dest/file.txt"]}
        assets = _parse_assets(data)
        assert len(assets) == 1
        assert assets[0].src == "src/file.txt"
        assert assets[0].dst == "dest/file.txt"

    def test_short_format_without_colon(self):
        data = {"assets": ["README.md"]}
        assets = _parse_assets(data)
        assert len(assets) == 1
        assert assets[0].src == "README.md"
        assert assets[0].dst == "README.md"

    def test_long_format(self):
        data = {"assets": [{"src": "a.txt", "dst": "b.txt"}]}
        assets = _parse_assets(data)
        assert len(assets) == 1
        assert assets[0].src == "a.txt"
        assert assets[0].dst == "b.txt"

    def test_mixed_formats(self):
        data = {
            "assets": [
                "file1.txt:dest1.txt",
                {"src": "file2.txt", "dst": "dest2.txt"},
                "file3.txt",
            ]
        }
        assets = _parse_assets(data)
        assert len(assets) == 3


class TestParseVersion:
    def test_defaults(self):
        ver = _parse_version({})
        assert ver.git_hash is True
        assert ver.dirty_flag is True
        assert ver.save_patch is True

    def test_all_disabled(self):
        data = {"version": {"git_hash": False, "dirty_flag": False, "save_patch": False}}
        ver = _parse_version(data)
        assert ver.git_hash is False
        assert ver.dirty_flag is False
        assert ver.save_patch is False


class TestParseInstaller:
    def test_defaults(self):
        inst = _parse_installer({})
        assert inst.enabled is True
        assert inst.app_guid is None
        assert inst.license is None
        assert inst.add_to_path is True
        assert inst.desktop_shortcut is False
        assert inst.start_menu is True
        assert inst.run_after_install is True

    def test_custom_values(self):
        data = {
            "installer": {
                "enabled": False,
                "publisher": "Test",
                "url": "https://test.com",
            }
        }
        inst = _parse_installer(data)
        assert inst.enabled is False
        assert inst.publisher == "Test"
        assert inst.url == "https://test.com"

    def test_app_guid(self):
        data = {
            "installer": {
                "app_guid": "{61E7BD3B-F815-4BA5-B8AD-AFF42431A546}",
            }
        }
        inst = _parse_installer(data)
        assert inst.app_guid == "{61E7BD3B-F815-4BA5-B8AD-AFF42431A546}"

    def test_license(self):
        data = {
            "installer": {
                "license": "LICENSE.txt",
            }
        }
        inst = _parse_installer(data)
        assert inst.license == "LICENSE.txt"

    def test_checkbox_defaults(self):
        data = {
            "installer": {
                "start_menu": False,
                "desktop_shortcut": True,
                "run_after_install": False,
            }
        }
        inst = _parse_installer(data)
        assert inst.start_menu is False
        assert inst.desktop_shortcut is True
        assert inst.run_after_install is False


class TestLoadConfig:
    def test_load_valid_config(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        assert config.app.name == "Test App"
        assert config.app.slug == "testapp"
        assert config.project_root == tmp_project

    def test_file_not_found(self, tmp_path: Path):
        with pytest.raises(ConfigError, match="Config file not found"):
            load_config(tmp_path / "nonexistent.yaml")

    def test_invalid_yaml(self, tmp_path: Path):
        config_file = tmp_path / "snackbox.yaml"
        config_file.write_text("invalid: yaml: content: [")
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(config_file)

    def test_resolve_path(self, tmp_project: Path):
        config = load_config(tmp_project / "snackbox.yaml")
        resolved = config.resolve_path("subdir/file.txt")
        assert resolved == tmp_project / "subdir" / "file.txt"
