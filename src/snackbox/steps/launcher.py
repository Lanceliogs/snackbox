"""Build the launcher executable."""

import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from jinja2 import Template

from snackbox.cache import CacheManager
from snackbox.config import Config
from snackbox.errors import BuildError
from snackbox.templates import read_template
from snackbox.toolchain import get_gcc, get_windres


def build_launcher(
    config: Config,
    release_dir: Path,
    echo: Callable[[str], None] = print,
) -> Path:
    """Build the launcher executable.

    Args:
        config: Snackbox configuration
        release_dir: Path to the release directory
        echo: Function to print status messages

    Returns:
        Path to the built executable

    Raises:
        BuildError: If build fails
    """
    slug = config.app.slug
    console_mode = config.launcher.console
    entry_point = config.launcher.entry_point
    env_vars = config.launcher.env
    icon_path = config.app.icon

    echo(f"Building launcher (console={console_mode})...")

    # Get GCC and windres (auto-downloads MinGW if needed)
    cache = CacheManager()
    gcc = get_gcc(cache, echo)
    windres = get_windres(cache, echo)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Render launcher.c
        c_template = Template(read_template("launcher.c"))
        c_content = c_template.render(
            slug=slug,
            console_mode=console_mode,
            entry_point=entry_point,
            env_vars=env_vars,
        )
        c_file = tmp / "launcher.c"
        c_file.write_text(c_content)

        # Handle icon if provided
        res_file = None
        if icon_path:
            icon_full_path = config.resolve_path(icon_path)
            if icon_full_path.exists():
                res_file = _compile_resource(tmp, slug, icon_full_path, windres, echo)
            else:
                echo(f"  Warning: icon not found: {icon_full_path}")

        # Compile the launcher
        exe_path = release_dir / f"{slug}.exe"
        _compile_launcher(c_file, exe_path, res_file, console_mode, gcc, echo)

    echo(f"  Built: {exe_path.name}")
    return exe_path


def _compile_resource(
    tmp: Path,
    slug: str,
    icon_path: Path,
    windres: str,
    echo: Callable[[str], None],
) -> Path:
    """Compile the resource file for icon embedding."""
    echo("  Compiling icon resource...")

    # Render launcher.rc
    rc_template = Template(read_template("launcher.rc"))
    rc_content = rc_template.render(
        slug=slug,
        icon_path=str(icon_path).replace("\\", "\\\\"),
    )
    rc_file = tmp / "launcher.rc"
    rc_file.write_text(rc_content)

    # Compile to .res
    res_file = tmp / "launcher.res"
    try:
        result = subprocess.run(
            [windres, str(rc_file), "-O", "coff", "-o", str(res_file)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise BuildError(f"windres failed:\n{result.stderr}")
    except OSError as e:
        raise BuildError(f"Failed to run windres: {e}") from e

    return res_file


def _compile_launcher(
    c_file: Path,
    exe_path: Path,
    res_file: Path | None,
    console_mode: str,
    gcc: str,
    echo: Callable[[str], None],
) -> None:
    """Compile the launcher C file to executable."""
    echo("  Compiling launcher...")

    # Build GCC command
    cmd = [gcc, "-static", "-O2"]

    # Console mode flag
    if console_mode == "no":
        cmd.append("-mwindows")
    else:
        cmd.append("-mconsole")

    # Output
    cmd.extend(["-o", str(exe_path)])

    # Source
    cmd.append(str(c_file))

    # Resource file if present
    if res_file and res_file.exists():
        cmd.append(str(res_file))

    # Link libraries for Windows API
    cmd.extend(["-lkernel32", "-luser32"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise BuildError(f"GCC failed:\n{result.stderr}")
    except OSError as e:
        raise BuildError(f"Failed to run GCC: {e}") from e
