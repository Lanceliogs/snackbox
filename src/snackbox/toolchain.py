"""Toolchain management - auto-download GCC and Inno Setup."""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from snackbox.cache import CacheManager
from snackbox.errors import BuildError

# WinLibs MinGW-w64 - standalone GCC for Windows
# https://github.com/brechtsanders/winlibs_mingw/releases
MINGW_VERSION = "14.2.0"
MINGW_URL = (
    "https://github.com/brechtsanders/winlibs_mingw/releases/download/"
    "14.2.0posix-19.1.7-12.0.0-msvcrt-r3/"
    "winlibs-x86_64-posix-seh-gcc-14.2.0-mingw-w64msvcrt-12.0.0-r3.zip"
)

# Inno Setup portable
# We download the installer and extract just what we need
INNO_VERSION = "6.3.3"
INNO_URL = "https://jrsoftware.org/download.php/is.exe"


def get_gcc(
    cache: CacheManager,
    echo: Callable[[str], None] = print,
) -> str:
    """Get path to GCC, downloading if necessary.

    Returns the path to gcc.exe (or the command if using system GCC).
    """
    # Check environment variable first
    env_gcc = os.environ.get("SNACKBOX_GCC")
    if env_gcc:
        return env_gcc

    # Check if system GCC is available
    if _is_tool_available("gcc"):
        return "gcc"

    # Check cached MinGW
    mingw_dir = cache.tools_dir / "mingw64"
    gcc_exe = mingw_dir / "bin" / "gcc.exe"

    if gcc_exe.exists():
        return str(gcc_exe)

    # Download MinGW
    echo("Downloading MinGW-w64 toolchain (one-time setup)...")
    _download_mingw(cache, echo)

    if not gcc_exe.exists():
        raise BuildError(f"GCC not found after download: {gcc_exe}")

    return str(gcc_exe)


def get_windres(
    cache: CacheManager,
    echo: Callable[[str], None] = print,
) -> str:
    """Get path to windres, downloading MinGW if necessary."""
    # Check environment variable first
    env_windres = os.environ.get("SNACKBOX_WINDRES")
    if env_windres:
        return env_windres

    # Check if system windres is available
    if _is_tool_available("windres"):
        return "windres"

    # Get GCC first (ensures MinGW is downloaded)
    gcc_path = get_gcc(cache, echo)

    # windres is in the same directory as gcc
    if gcc_path == "gcc":
        return "windres"

    gcc_dir = Path(gcc_path).parent
    windres_exe = gcc_dir / "windres.exe"

    if windres_exe.exists():
        return str(windres_exe)

    raise BuildError(f"windres not found: {windres_exe}")


def get_iscc(
    cache: CacheManager,
    echo: Callable[[str], None] = print,
) -> str:
    """Get path to ISCC.exe, downloading if necessary."""
    # Check environment variable first
    env_iscc = os.environ.get("SNACKBOX_ISCC_PATH")
    if env_iscc:
        return env_iscc

    # Check common installation paths
    common_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path

    # Check cached Inno Setup
    inno_dir = cache.tools_dir / "innosetup"
    iscc_exe = inno_dir / "ISCC.exe"

    if iscc_exe.exists():
        return str(iscc_exe)

    # Download Inno Setup
    echo("Downloading Inno Setup (one-time setup)...")
    _download_innosetup(cache, echo)

    if not iscc_exe.exists():
        raise BuildError(f"ISCC.exe not found after download: {iscc_exe}")

    return str(iscc_exe)


def _is_tool_available(tool: str) -> bool:
    """Check if a tool is available in PATH."""
    try:
        result = subprocess.run(
            [tool, "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _download_mingw(cache: CacheManager, echo: Callable[[str], None]) -> None:
    """Download and extract MinGW-w64."""
    cache.ensure_dirs()

    zip_path = cache.tools_dir / "mingw.zip"
    mingw_dir = cache.tools_dir / "mingw64"

    # Download
    echo(f"  Downloading MinGW-w64 {MINGW_VERSION}...")
    cache.download(MINGW_URL, zip_path)

    # Extract
    echo("  Extracting...")
    # The zip contains a mingw64 folder at the root
    cache.extract_zip(zip_path, cache.tools_dir)

    # Cleanup zip
    zip_path.unlink()

    # Verify
    gcc_exe = mingw_dir / "bin" / "gcc.exe"
    if not gcc_exe.exists():
        raise BuildError("MinGW extraction failed - gcc.exe not found")

    echo(f"  Installed MinGW-w64 to {mingw_dir}")


def _download_innosetup(cache: CacheManager, echo: Callable[[str], None]) -> None:
    """Download and extract Inno Setup."""
    cache.ensure_dirs()

    inno_dir = cache.tools_dir / "innosetup"
    inno_dir.mkdir(exist_ok=True)

    # Download the installer
    installer_path = cache.tools_dir / "innosetup-installer.exe"
    echo(f"  Downloading Inno Setup {INNO_VERSION}...")
    cache.download(INNO_URL, installer_path)

    # Extract using innounp or run silent install to a temp location
    # Since innounp may not be available, we'll do a silent install
    echo("  Extracting...")

    try:
        # Run silent install to our cache directory
        result = subprocess.run(
            [
                str(installer_path),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/CURRENTUSER",
                f"/DIR={inno_dir}",
                "/NOICONS",
            ],
            capture_output=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise BuildError(f"Inno Setup installation failed: {result.stderr.decode()}")

    except subprocess.TimeoutExpired:
        raise BuildError("Inno Setup installation timed out")
    finally:
        # Cleanup installer
        if installer_path.exists():
            installer_path.unlink()

    # Verify
    iscc_exe = inno_dir / "ISCC.exe"
    if not iscc_exe.exists():
        raise BuildError("Inno Setup extraction failed - ISCC.exe not found")

    echo(f"  Installed Inno Setup to {inno_dir}")
