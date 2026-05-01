"""Tests for installer template rendering."""

from jinja2 import Template

from snackbox.templates import read_template


class TestInstallerTemplate:
    def test_app_guid_renders_with_escaped_brace(self):
        template_content = read_template("installer.iss")
        template = Template(template_content)

        result = template.render(
            app_name="Test App",
            slug="testapp",
            version="1.0.0",
            app_guid="{61E7BD3B-F815-4BA5-B8AD-AFF42431A546}",
            publisher="Test Publisher",
            url="https://example.com",
            install_dir="{localappdata}\\TestApp",
            output_dir="build",
            release_dir="release",
            icon_path=None,
            add_to_path=False,
            desktop_shortcut=False,
            start_menu=False,
        )

        # Should have double brace for Inno Setup escaping
        assert "AppId={{61E7BD3B-F815-4BA5-B8AD-AFF42431A546}" in result

    def test_no_app_guid_omits_line(self):
        template_content = read_template("installer.iss")
        template = Template(template_content)

        result = template.render(
            app_name="Test App",
            slug="testapp",
            version="1.0.0",
            app_guid=None,
            publisher="Test Publisher",
            url="https://example.com",
            install_dir="{localappdata}\\TestApp",
            output_dir="build",
            release_dir="release",
            icon_path=None,
            add_to_path=False,
            desktop_shortcut=False,
            start_menu=False,
        )

        assert "AppId=" not in result
