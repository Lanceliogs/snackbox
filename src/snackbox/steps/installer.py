"""Build Inno Setup installer."""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from jinja2 import Template

from snackbox.config import Config
from snackbox.errors import BuildError
from snackbox.templates import read_template


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

    # Find ISCC
    iscc = _find_iscc()

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

    iss_content = template.render(
        app_name=config.app.name,
        slug=config.app.slug,
        version=version,
        publisher=config.installer.publisher,
        url=config.installer.url,
        install_dir=config.installer.install_dir,
        output_dir=str(output_dir),
        release_dir=str(release_dir),
        icon_path=icon_path,
        add_to_path=config.installer.add_to_path,
        desktop_shortcut=config.installer.desktop_shortcut,
        start_menu=config.installer.start_menu,
    )

    iss_path.write_text(iss_content)
    echo(f"  Generated: {iss_path.name}")

    # Run ISCC
    echo("  Compiling installer...")
    installer_path = _run_iscc(iscc, iss_path, config.app.slug, version, output_dir)

    echo(f"  Built: {installer_path.name}")
    return installer_path


def _find_iscc() -> str:
    """Find Inno Setup compiler."""
    # Check environment variable first
    iscc_env = os.environ.get("SNACKBOX_ISCC_PATH")
    if iscc_env:
        return iscc_env

    # Common installation paths on Windows
    common_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]

    for path in common_paths:
        if Path(path).exists():
            return path

    # Try PATH
    try:
        result = subprocess.run(
            ["where", "ISCC"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except (OSError, FileNotFoundError):
        pass

    raise BuildError(
        "Inno Setup not found.\n"
        "Install from https://jrsoftware.org/isinfo.php\n"
        "Or set SNACKBOX_ISCC_PATH environment variable."
    )


def _run_iscc(
    iscc: str,
    iss_path: Path,
    slug: str,
    version: str,
    output_dir: Path,
) -> Path:
    """Run ISCC to compile the installer."""
    try:
        result = subprocess.run(
            [iscc, str(iss_path)],
            capture_output=True,
            text=True,
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
