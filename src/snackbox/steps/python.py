"""Setup embedded Python environment."""

import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from snackbox.cache import CacheManager
from snackbox.config import Config
from snackbox.errors import BuildError

GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


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

    # Bootstrap pip
    echo("Installing pip...")
    _install_pip(python_dir, cache, echo)

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


def _install_pip(python_dir: Path, cache: CacheManager, echo: Callable[[str], None]) -> None:
    """Download and run get-pip.py to install pip."""
    get_pip_path = cache.tools_dir / "get-pip.py"

    if not get_pip_path.exists():
        echo("  Downloading get-pip.py...")
        cache.download(GET_PIP_URL, get_pip_path)

    python_exe = python_dir / "python.exe"
    if not python_exe.exists():
        raise BuildError(f"Python executable not found: {python_exe}")

    # Run get-pip.py
    try:
        result = subprocess.run(
            [str(python_exe), str(get_pip_path), "--no-warn-script-location"],
            capture_output=True,
            text=True,
            cwd=python_dir,
        )
        if result.returncode != 0:
            raise BuildError(f"Failed to install pip:\n{result.stderr}")
    except OSError as e:
        raise BuildError(f"Failed to run Python: {e}") from e

    # Verify pip is installed
    pip_exe = python_dir / "Scripts" / "pip.exe"
    if not pip_exe.exists():
        raise BuildError("pip installation failed - pip.exe not found")
