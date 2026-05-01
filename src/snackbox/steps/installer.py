"""Build Inno Setup installer."""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from jinja2 import Template

from snackbox.cache import CacheManager
from snackbox.config import Config
from snackbox.errors import BuildError
from snackbox.steps.python import _is_cross_compile, _wine_path
from snackbox.templates import read_template
from snackbox.toolchain import get_iscc


def build_installer(
    config: Config,
    release_dir: Path,
    version: str,
    echo: Callable[[str], None] = print,
) -> Path:
    """Build Inno Setup installer.

    Args:
        config: Snackbox configuration
        release_dir: Path to the release directory
        version: Version string for the installer
        echo: Function to print status messages

    Returns:
        Path to the built installer

    Raises:
        BuildError: If build fails
    """
    if not config.installer.enabled:
        echo("Installer disabled in config")
        return None

    echo("Building installer...")

    # Get ISCC (auto-downloads Inno Setup if needed)
    cache = CacheManager()
    iscc = get_iscc(cache, echo)

    # Prepare output directory
    output_dir = config.resolve_path(config.installer.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate .iss file
    iss_path = output_dir / f"{config.app.slug}.iss"

    if config.installer.template:
        # Use custom template
        custom_template_path = config.resolve_path(config.installer.template)
        if not custom_template_path.exists():
            raise BuildError(f"Custom installer template not found: {custom_template_path}")
        template_content = custom_template_path.read_text()
    else:
        # Use default template
        template_content = read_template("installer.iss")

    # Render template
    template = Template(template_content)

    # Resolve icon path if provided
    icon_path = None
    if config.app.icon:
        icon_full = config.resolve_path(config.app.icon)
        if icon_full.exists():
            icon_path = str(icon_full)

    # Convert paths to Wine format if cross-compiling
    if _is_cross_compile():
        iss_output_dir = _wine_path(output_dir.resolve())
        iss_release_dir = _wine_path(release_dir.resolve())
    else:
        iss_output_dir = str(output_dir.resolve())
        iss_release_dir = str(release_dir.resolve())

    # Resolve license path if provided
    license_path = None
    if config.installer.license:
        license_full = config.resolve_path(config.installer.license)
        if license_full.exists():
            license_path = str(license_full)

    iss_content = template.render(
        app_name=config.app.name,
        slug=config.app.slug,
        version=version,
        app_guid=config.installer.app_guid,
        publisher=config.installer.publisher,
        url=config.installer.url,
        license_path=license_path,
        install_dir=config.installer.install_dir,
        output_dir=iss_output_dir,
        release_dir=iss_release_dir,
        icon_path=icon_path,
        add_to_path=config.installer.add_to_path,
        desktop_shortcut=config.installer.desktop_shortcut,
        start_menu=config.installer.start_menu,
        run_after_install=config.installer.run_after_install,
    )

    iss_path.write_text(iss_content)
    echo(f"  Generated: {iss_path.name}")

    # Run ISCC
    echo("  Compiling installer...")
    installer_path = _run_iscc(iscc, iss_path, config.app.slug, version, output_dir)

    echo(f"  Built: {installer_path.name}")
    return installer_path


def _run_iscc(
    iscc: str,
    iss_path: Path,
    slug: str,
    version: str,
    output_dir: Path,
) -> Path:
    """Run ISCC to compile the installer."""
    try:
        if _is_cross_compile():
            # Use Wine to run ISCC on Linux
            wine_iss = _wine_path(iss_path.resolve())
            cmd = ["wine", iscc, wine_iss]
            env = os.environ.copy()
            env["WINEDEBUG"] = "-all"
        else:
            cmd = [iscc, str(iss_path)]
            env = None

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise BuildError(f"ISCC failed:\n{result.stdout}\n{result.stderr}")
    except FileNotFoundError as e:
        raise BuildError(f"ISCC not found at: {iscc}") from e
    except OSError as e:
        raise BuildError(f"Failed to run ISCC: {e}") from e

    # Return path to the generated installer
    installer_name = f"{slug}-{version}-setup.exe"
    installer_path = output_dir / installer_name

    if not installer_path.exists():
        raise BuildError(f"Installer not found after build: {installer_path}")

    return installer_path
