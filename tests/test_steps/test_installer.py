"""Tests for installer template rendering."""

from jinja2 import Template

from snackbox.templates import read_template


def _render_template(**kwargs):
    """Helper to render the installer template with defaults."""
    defaults = {
        "app_name": "Test App",
        "slug": "testapp",
        "version": "1.0.0",
        "app_guid": None,
        "publisher": "Test Publisher",
        "url": "https://example.com",
        "license_path": None,
        "install_dir": "{localappdata}\\TestApp",
        "output_dir": "build",
        "release_dir": "release",
        "icon_path": None,
        "add_to_path": False,
        "desktop_shortcut": False,
        "start_menu": True,
        "run_after_install": True,
    }
    defaults.update(kwargs)
    template_content = read_template("installer.iss")
    template = Template(template_content)
    return template.render(**defaults)


class TestInstallerTemplate:
    def test_app_guid_renders_with_escaped_brace(self):
        result = _render_template(app_guid="{61E7BD3B-F815-4BA5-B8AD-AFF42431A546}")
        assert "AppId={{61E7BD3B-F815-4BA5-B8AD-AFF42431A546}" in result

    def test_no_app_guid_omits_line(self):
        result = _render_template(app_guid=None)
        assert "AppId=" not in result

    def test_license_path_renders(self):
        result = _render_template(license_path="C:\\project\\LICENSE.txt")
        assert "LicenseFile=C:\\project\\LICENSE.txt" in result

    def test_no_license_omits_line(self):
        result = _render_template(license_path=None)
        assert "LicenseFile=" not in result

    def test_start_menu_checked_by_default(self):
        result = _render_template(start_menu=True)
        assert 'Name: "startmenu"' in result
        # Should NOT have unchecked flag
        for line in result.splitlines():
            if '"startmenu"' in line:
                assert "unchecked" not in line
                break

    def test_start_menu_unchecked(self):
        result = _render_template(start_menu=False)
        for line in result.splitlines():
            if '"startmenu"' in line:
                assert "Flags: unchecked" in line
                break
        else:
            raise AssertionError("startmenu task not found")

    def test_desktop_shortcut_unchecked_by_default(self):
        result = _render_template(desktop_shortcut=False)
        for line in result.splitlines():
            if '"desktopicon"' in line:
                assert "Flags: unchecked" in line
                break
        else:
            raise AssertionError("desktopicon task not found")

    def test_desktop_shortcut_checked(self):
        result = _render_template(desktop_shortcut=True)
        for line in result.splitlines():
            if '"desktopicon"' in line:
                assert "unchecked" not in line
                break
        else:
            raise AssertionError("desktopicon task not found")

    def test_run_after_install_checked_by_default(self):
        result = _render_template(run_after_install=True)
        assert "Launch Test App" in result
        assert "postinstall skipifsilent unchecked" not in result

    def test_run_after_install_unchecked(self):
        result = _render_template(run_after_install=False)
        assert "postinstall skipifsilent unchecked" in result
