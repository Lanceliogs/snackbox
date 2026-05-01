"""Setup embedded Python environment."""

import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from snackbox.cache import CacheManager
from snackbox.config import Config
from snackbox.errors import BuildError


def _is_cross_compile() -> bool:
    """Check if we're cross-compiling (Linux building for Windows)."""
    return sys.platform != "win32"


def _wine_path(path: Path) -> str:
    """Convert a Linux path to Wine path format."""
    return "Z:" + str(path).replace("/", "\\")


def setup_python(
    config: Config,
    release_dir: Path,
    clean: bool = False,
    echo: Callable[[str], None] = print,
) -> Path:
    """Download and setup embedded Python in the release directory.

    Args:
        config: Snackbox configuration
        release_dir: Path to the release directory
        clean: If True, remove existing Python and start fresh
        echo: Function to print status messages

    Returns:
        Path to the python directory (release_dir/python)

    Raises:
        BuildError: If setup fails
    """
    python_dir = release_dir / "python"
    version = config.python.version
    arch = config.python.arch

    # Check if already set up
    python_exe = python_dir / "python.exe"
    if python_exe.exists() and not clean:
        echo(f"Python {version} already set up")
        return python_dir

    # Clean existing if requested
    if python_dir.exists():
        echo("Cleaning existing Python installation...")
        shutil.rmtree(python_dir)

    cache = CacheManager()
    cache.ensure_dirs()

    # Download embeddable Python if not cached
    zip_path = cache.get_python_zip(version, arch)
    if not zip_path.exists():
        url = cache.get_python_url(version, arch)
        echo(f"Downloading Python {version} ({arch})...")
        cache.download(url, zip_path)
        echo("  Download complete")
    else:
        echo(f"Using cached Python {version} ({arch})")

    # Extract to release/python/
    echo("Extracting Python...")
    release_dir.mkdir(parents=True, exist_ok=True)
    cache.extract_zip(zip_path, python_dir)

    # Patch ._pth file to enable site-packages
    echo("Patching Python configuration...")
    _patch_pth_file(python_dir, version)

    echo(f"Python {version} ready")
    return python_dir


def _patch_pth_file(python_dir: Path, version: str) -> None:
    """Patch the python._pth file to enable site-packages.

    The embeddable Python ships with site-packages disabled.
    We need to uncomment 'import site' to enable it.
    """
    # Find the ._pth file (e.g., python312._pth)
    version_nodot = version.replace(".", "")[:3]  # "3.12.10" -> "312"
    pth_file = python_dir / f"python{version_nodot}._pth"

    if not pth_file.exists():
        # Try to find any ._pth file
        pth_files = list(python_dir.glob("python*._pth"))
        if not pth_files:
            raise BuildError(f"Could not find python._pth file in {python_dir}")
        pth_file = pth_files[0]

    content = pth_file.read_text()

    # Uncomment 'import site' if it's commented
    new_content = re.sub(r"^#\s*import site", "import site", content, flags=re.MULTILINE)

    # Also ensure Lib/site-packages is in the path
    if "Lib/site-packages" not in new_content and "Lib\\site-packages" not in new_content:
        new_content += "\nLib/site-packages\n"

    pth_file.write_text(new_content)


