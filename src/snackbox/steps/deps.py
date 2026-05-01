"""Install dependencies into embedded Python."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from snackbox.config import Config
from snackbox.errors import BuildError
from snackbox.steps.python import _is_cross_compile, _run_windows_python


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
    _pip_install(python_exe, [str(wheel_path)], force=force, python_version=py_version, arch=arch)

    # Install extra dependencies
    extra_deps = config.build.extra_deps
    if extra_deps:
        echo(f"Installing {len(extra_deps)} extra dependencies...")
        _pip_install(python_exe, extra_deps, force=False, python_version=py_version, arch=arch)

    echo("Dependencies installed")


def _pip_install(
    python_exe: Path,
    packages: list[str],
    force: bool = False,
    python_version: str | None = None,
    arch: str = "amd64",
) -> None:
    """Run pip install for the given packages.

    Args:
        python_exe: Path to python.exe
        packages: List of packages/wheels to install
        force: If True, add --force-reinstall flag
        python_version: Target Python version (e.g. "3.12.10")
        arch: Target architecture (e.g. "amd64")

    Raises:
        BuildError: If pip install fails
    """
    if _is_cross_compile():
        site_packages = python_exe.parent / "Lib" / "site-packages"
        major_minor = ".".join(python_version.split(".")[:2]) if python_version else "3.12"
        cmd = [
            "uv",
            "pip",
            "install",
            "--system",
            "--target",
            str(site_packages),
            "--python-platform",
            "windows",
            "--python-version",
            major_minor,
        ]
        if force:
            cmd.append("--reinstall")
        cmd.extend(packages)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "(no output)"
                raise BuildError(f"uv pip install failed:\n{error_msg}")
        except OSError as e:
            raise BuildError(f"Failed to run uv: {e}") from e
    else:
        args = ["-m", "pip", "install", "--no-warn-script-location"]
        if force:
            args.append("--force-reinstall")
        args.extend(packages)

        try:
            result = _run_windows_python(python_exe, args)
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "(no output)"
                raise BuildError(f"pip install failed:\n{error_msg}")
        except OSError as e:
            raise BuildError(f"Failed to run pip: {e}") from e
