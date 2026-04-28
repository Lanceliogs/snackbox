"""Copy assets and scripts into release folder."""

import shutil
from collections.abc import Callable
from pathlib import Path

from snackbox.config import Config
from snackbox.errors import BuildError


def copy_assets(
    config: Config,
    release_dir: Path,
    echo: Callable[[str], None] = print,
) -> None:
    """Copy configured assets into the release folder.

    Args:
        config: Snackbox configuration
        release_dir: Path to the release directory
        echo: Function to print status messages

    Raises:
        BuildError: If copying fails
    """
    assets = config.assets

    if not assets:
        return

    echo("Copying assets...")

    for asset in assets:
        src = config.resolve_path(asset.src)
        dst = release_dir / asset.dst

        if not src.exists():
            raise BuildError(f"Asset not found: {src}")

        try:
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                echo(f"  {asset.src}/ -> {asset.dst}/")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                echo(f"  {asset.src} -> {asset.dst}")
        except OSError as e:
            raise BuildError(f"Failed to copy {src}: {e}") from e
