"""Install dependencies into embedded Python."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from snackbox.config import Config
from snackbox.errors import BuildError


def install_deps(
    config: Config,
    release_dir: Path,
    wheel_path: Path,
    force: bool = False,
    echo: Callable[[str], None] = print,
) -> None:
    """Install the wheel and extra dependencies into embedded Python.
    
    Args:
        config: Snackbox configuration
        release_dir: Path to the release directory
        wheel_path: Path to the wheel file to install
        force: If True, force reinstall even if already installed
        echo: Function to print status messages
        
    Raises:
        BuildError: If installation fails
    """
    python_exe = release_dir / "python" / "python.exe"
    if not python_exe.exists():
        raise BuildError(f"Python not found at {python_exe}")

    # Install the main wheel
    echo(f"Installing {wheel_path.name}...")
    _pip_install(python_exe, [str(wheel_path)], force=force)

    # Install extra dependencies
    extra_deps = config.build.extra_deps
    if extra_deps:
        echo(f"Installing {len(extra_deps)} extra dependencies...")
        _pip_install(python_exe, extra_deps, force=False)

    echo("Dependencies installed")


def _pip_install(python_exe: Path, packages: list[str], force: bool = False) -> None:
    """Run pip install for the given packages.
    
    Args:
        python_exe: Path to python.exe
        packages: List of packages/wheels to install
        force: If True, add --force-reinstall flag
        
    Raises:
        BuildError: If pip install fails
    """
    cmd = [
        str(python_exe),
        "-m",
        "pip",
        "install",
        "--no-warn-script-location",
    ]

    if force:
        cmd.append("--force-reinstall")

    cmd.extend(packages)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise BuildError(f"pip install failed:\n{result.stderr or result.stdout}")
    except OSError as e:
        raise BuildError(f"Failed to run pip: {e}") from e
