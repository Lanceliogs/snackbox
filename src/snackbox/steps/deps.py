"""Install dependencies into embedded Python."""

import subprocess
import sys
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

    py_version = config.python.version
    arch = config.python.arch

    # Install the main wheel
    echo(f"Installing {wheel_path.name}...")
    _uv_install(python_exe, [str(wheel_path)], force=force, python_version=py_version, arch=arch)

    # Install extra dependencies
    extra_deps = config.build.extra_deps
    if extra_deps:
        echo(f"Installing {len(extra_deps)} extra dependencies...")
        _uv_install(python_exe, extra_deps, force=False, python_version=py_version, arch=arch)

    echo("Dependencies installed")


def _uv_install(
    python_exe: Path,
    packages: list[str],
    force: bool = False,
    python_version: str = "3.12.10",
    arch: str = "amd64",
) -> None:
    """Install packages into embedded Python's site-packages using uv.

    Always targets Windows since the embedded Python is a Windows distribution.
    When running on Linux (cross-compile), --python-platform ensures correct
    marker evaluation and wheel selection.

    Args:
        python_exe: Path to the embedded python.exe
        packages: List of packages/wheels to install
        force: If True, force reinstall
        python_version: Target Python version (e.g. "3.12.10")
        arch: Target architecture (e.g. "amd64")

    Raises:
        BuildError: If installation fails
    """
    site_packages = python_exe.parent / "Lib" / "site-packages"
    major_minor = ".".join(python_version.split(".")[:2])

    cmd = [
        "uv",
        "pip",
        "install",
        "--system",
        "--target",
        str(site_packages),
        "--python-version",
        major_minor,
    ]

    if sys.platform != "win32":
        cmd.extend(["--python-platform", "windows"])

    if force:
        cmd.append("--reinstall")

    cmd.extend(packages)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "(no output)"
            raise BuildError(f"uv pip install failed:\n{error_msg}")
    except FileNotFoundError:
        raise BuildError("uv not found. Install it with: pip install uv")
    except OSError as e:
        raise BuildError(f"Failed to run uv: {e}") from e
