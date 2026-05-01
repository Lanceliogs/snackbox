"""Build project wheel."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from snackbox.config import Config
from snackbox.errors import BuildError


def build_wheel(
    config: Config,
    echo: Callable[[str], None] = print,
) -> Path:
    """Build the project wheel using the configured backend.

    Args:
        config: Snackbox configuration
        echo: Function to print status messages

    Returns:
        Path to the built wheel file

    Raises:
        BuildError: If build fails
    """
    backend = config.build.backend
    custom_command = config.build.backend_command
    project_root = config.project_root
    dist_dir = project_root / "dist"

    # Clean old wheels
    if dist_dir.exists():
        for old_wheel in dist_dir.glob("*.whl"):
            old_wheel.unlink()

    echo(f"Building wheel ({backend})...")

    if custom_command:
        _run_custom_command(custom_command, project_root)
    elif backend == "poetry":
        _run_poetry_build(project_root)
    elif backend == "hatch":
        _run_hatch_build(project_root)
    elif backend == "uv":
        _run_uv_build(project_root)
    else:
        raise BuildError(f"Unknown build backend: {backend}")

    # Find the built wheel
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise BuildError(f"No wheel found in {dist_dir} after build")

    if len(wheels) > 1:
        echo("  Warning: multiple wheels found, using newest")
        wheels.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    wheel_path = wheels[0]
    echo(f"  Built: {wheel_path.name}")
    return wheel_path


def _run_command(cmd: list[str], cwd: Path, name: str) -> None:
    """Run a command and handle errors."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise BuildError(f"{name} build failed:\n{result.stderr or result.stdout}")
    except FileNotFoundError as e:
        raise BuildError(f"{name} not found. Is it installed?") from e
    except OSError as e:
        raise BuildError(f"Failed to run {name}: {e}") from e


def _run_poetry_build(project_root: Path) -> None:
    """Build wheel using Poetry."""
    _run_command(
        ["poetry", "build", "-f", "wheel"],
        project_root,
        "poetry",
    )



def _run_hatch_build(project_root: Path) -> None:
    """Build wheel using Hatch."""
    _run_command(
        ["hatch", "build", "-t", "wheel"],
        project_root,
        "hatch",
    )


def _run_uv_build(project_root: Path) -> None:
    """Build wheel using uv."""
    _run_command(
        ["uv", "build", "--wheel"],
        project_root,
        "uv",
    )


def _run_custom_command(command: str, project_root: Path) -> None:
    """Run a custom build command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise BuildError(f"Custom build command failed:\n{result.stderr or result.stdout}")
    except OSError as e:
        raise BuildError(f"Failed to run custom command: {e}") from e
