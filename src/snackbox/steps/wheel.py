"""Build project wheel."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from snackbox.config import Config
from snackbox.errors import BuildError
from snackbox.steps.deps import _get_uv


def build_wheel(
    config: Config,
    echo: Callable[[str], None] = print,
) -> Path:
    """Build the project wheel using uv.

    Args:
        config: Snackbox configuration
        echo: Function to print status messages

    Returns:
        Path to the built wheel file

    Raises:
        BuildError: If build fails
    """
    project_root = config.project_root
    dist_dir = project_root / "dist"

    # Clean old wheels
    if dist_dir.exists():
        for old_wheel in dist_dir.glob("*.whl"):
            old_wheel.unlink()

    echo("Building wheel...")

    uv = _get_uv()
    try:
        result = subprocess.run(
            [uv, "build", "--wheel"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise BuildError(f"Wheel build failed:\n{result.stderr or result.stdout}")
    except OSError as e:
        raise BuildError(f"Failed to run uv: {e}") from e

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
