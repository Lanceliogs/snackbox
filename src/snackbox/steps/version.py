"""Version stamping for releases."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from snackbox.config import Config
from snackbox.errors import BuildError


def stamp_version(
    config: Config,
    release_dir: Path,
    echo: Callable[[str], None] = print,
) -> str:
    """Generate version string and write version.txt.

    Args:
        config: Snackbox configuration
        release_dir: Path to the release directory
        echo: Function to print status messages

    Returns:
        The full version string

    Raises:
        BuildError: If version stamping fails
    """
    project_root = config.project_root

    # Get base version from git tags or pyproject.toml
    version_from = config.app.version_from
    if version_from == "git":
        base_version = _get_version_from_git_tag(project_root)
        if not base_version:
            raise BuildError("No git tags found (version_from is 'git')")
    else:
        base_version = _read_pyproject_version(project_root, version_from, echo)

    version_parts = [base_version]

    # Append git hash if configured
    if config.version.git_hash:
        git_hash = _get_git_hash(project_root)
        if git_hash:
            version_parts.append(git_hash)

    # Check if dirty and append flag if configured
    is_dirty = _is_git_dirty(project_root)
    if is_dirty and config.version.dirty_flag:
        version_parts.append("dirty")

    # Build final version string
    version = ".".join(version_parts)

    echo(f"Version: {version}")

    # Write version.txt
    version_file = release_dir / "version.txt"
    version_file.write_text(version + "\n")

    # Save dirty patch if configured
    if is_dirty and config.version.save_patch:
        _save_dirty_patch(project_root, release_dir, echo)

    return version


def _read_pyproject_version(
    project_root: Path,
    version_from: str,
    echo: Callable[[str], None] = print,
) -> str:
    """Read version from a TOML file (e.g. pyproject.toml)."""
    pyproject_path = project_root / version_from

    if not pyproject_path.exists():
        raise BuildError(f"Version source not found: {pyproject_path}")

    content = pyproject_path.read_text()

    for line in content.splitlines():
        line = line.strip()
        if line.startswith("version") and "=" in line:
            _, value = line.split("=", 1)
            value = value.strip()
            for quote in ('"', "'"):
                if value.startswith(quote):
                    end = value.index(quote, 1)
                    return value[1:end]
            return value

    raise BuildError(f"Could not find version in {version_from}")


def _get_version_from_git_tag(project_root: Path) -> str | None:
    """Get the version from git tags.

    Uses `git describe --tags` to get the tag and distance.
    - On a tag: returns "X.Y.Z"
    - After a tag: returns "X.Y.Z.postN" where N is commits since tag
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--long"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # Format: v0.1.0-3-gabcdef1 (tag-distance-ghash)
            desc = result.stdout.strip()
            parts = desc.rsplit("-", 2)
            if len(parts) == 3:
                tag, distance, _ = parts
                base = tag.lstrip("v")
                if int(distance) > 0:
                    return f"{base}.post{distance}"
                return base
    except (OSError, FileNotFoundError):
        pass
    return None


def _get_git_hash(project_root: Path) -> str | None:
    """Get short git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, FileNotFoundError):
        pass
    return None


def _is_git_dirty(project_root: Path) -> bool:
    """Check if git working directory has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return bool(result.stdout.strip())
    except (OSError, FileNotFoundError):
        pass
    return False


def _save_dirty_patch(
    project_root: Path,
    release_dir: Path,
    echo: Callable[[str], None],
) -> None:
    """Save uncommitted changes as a patch file."""
    try:
        # Get diff of staged and unstaged changes
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            patch_file = release_dir / "dirty.patch"
            patch_file.write_text(result.stdout)
            echo("  Saved dirty.patch")
    except (OSError, FileNotFoundError):
        pass
