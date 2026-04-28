"""CLI entry point for snackbox."""

from pathlib import Path

import typer

from snackbox import __version__
from snackbox.cache import CacheManager, get_cache_dir
from snackbox.cache.manager import format_size
from snackbox.config import Config, load_config
from snackbox.errors import BuildError, ConfigError
from snackbox.steps import (
    build_installer,
    build_launcher,
    build_wheel,
    copy_assets,
    install_deps,
    setup_python,
    stamp_version,
)
from snackbox.templates import read_template

app = typer.Typer(
    name="snackbox",
    help="Release pipeline for Python apps on Windows.",
    no_args_is_help=True,
)

cache_app = typer.Typer(help="Manage the download cache.")
app.add_typer(cache_app, name="cache")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"snackbox {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Snackbox - Release pipeline for Python apps on Windows."""
    pass


def _run_build(config: Config, clean: bool, force: bool) -> tuple[Path, str]:
    """Run the build pipeline and return (release_dir, version)."""
    release_dir = config.project_root / f"{config.app.slug}-release"

    # Show cache location
    cache_dir = get_cache_dir()
    if _is_docker():
        typer.echo(f"Using Docker cache: {cache_dir}")
    else:
        typer.echo(f"Using cache: {cache_dir}")

    # Step 1: Setup embedded Python
    setup_python(config, release_dir, clean=clean, echo=typer.echo)

    # Step 2: Build wheel
    wheel_path = build_wheel(config, echo=typer.echo)

    # Step 3: Install dependencies
    install_deps(config, release_dir, wheel_path, force=force, echo=typer.echo)

    # Step 4: Build launcher
    build_launcher(config, release_dir, echo=typer.echo)

    # Step 5: Copy assets
    copy_assets(config, release_dir, echo=typer.echo)

    # Step 6: Stamp version
    version = stamp_version(config, release_dir, echo=typer.echo)

    return release_dir, version


@app.command()
def build(
    config_file: Path | None = typer.Option(
        None, "--file", "-f", help="Path to snackbox.yaml config file."
    ),
    clean: bool = typer.Option(False, "--clean", help="Rebuild embedded Python from scratch."),
    force: bool = typer.Option(False, "--force", help="Force reinstall the app wheel (keep deps)."),
) -> None:
    """Build release folder."""
    try:
        config = load_config(config_file)
    except ConfigError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

    typer.echo(f"Building {config.app.name} ({config.app.slug})...")

    try:
        release_dir, _ = _run_build(config, clean, force)

        typer.echo("\nBuild complete!")
        typer.echo(f"Release folder: {release_dir}")

    except BuildError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def installer(
    config_file: Path | None = typer.Option(
        None, "--file", "-f", help="Path to snackbox.yaml config file."
    ),
    clean: bool = typer.Option(False, "--clean", help="Rebuild embedded Python from scratch."),
    force: bool = typer.Option(False, "--force", help="Force reinstall the app wheel (keep deps)."),
) -> None:
    """Build release folder and Inno Setup installer."""
    try:
        config = load_config(config_file)
    except ConfigError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

    typer.echo(f"Building {config.app.name} ({config.app.slug})...")

    try:
        release_dir, version = _run_build(config, clean, force)

        # Step 7: Build installer
        installer_path = build_installer(config, release_dir, version, echo=typer.echo)

        typer.echo("\nBuild complete!")
        typer.echo(f"Release folder: {release_dir}")
        if installer_path:
            typer.echo(f"Installer: {installer_path}")

    except BuildError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing snackbox.yaml."),
) -> None:
    """Generate a starter snackbox.yaml in the current directory."""
    config_path = Path.cwd() / "snackbox.yaml"

    if config_path.exists() and not force:
        typer.echo(f"Error: {config_path} already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    template_content = read_template("snackbox.yaml")
    config_path.write_text(template_content)
    typer.echo(f"Created {config_path}")
    typer.echo("Edit the file to match your project, then run: snackbox build")


def _is_docker() -> bool:
    """Check if running inside a Docker container."""
    return Path("/.dockerenv").exists()


@cache_app.command("show")
def cache_show() -> None:
    """Show cache location and contents."""
    if _is_docker():
        typer.echo(
            "Note: Running in Docker. This shows the container's cache, not your host cache."
        )
        typer.echo("      Cache commands are intended for local (pipx) installs.\n")

    cache = CacheManager()
    cache_dir = get_cache_dir()

    typer.echo(f"Cache directory: {cache_dir}")

    if not cache_dir.exists():
        typer.echo("Cache is empty.")
        return

    items = cache.list_cached_items()
    total_size = cache.get_cache_size()

    has_items = False
    for category, files in items.items():
        if files:
            has_items = True
            typer.echo(f"\n{category}/")
            for f in files:
                typer.echo(f"  {f}")

    if has_items:
        typer.echo(f"\nTotal size: {format_size(total_size)}")
    else:
        typer.echo("Cache is empty.")


@cache_app.command("clean")
def cache_clean(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
) -> None:
    """Wipe the download cache."""
    if _is_docker():
        typer.echo("Note: Running in Docker. This only cleans the container's ephemeral cache.")
        typer.echo("      The container cache is discarded when the container exits anyway.")
        typer.echo("      Cache commands are intended for local (pipx) installs.")
        return

    cache = CacheManager()
    cache_dir = get_cache_dir()

    if not cache_dir.exists():
        typer.echo("Cache is already empty.")
        return

    total_size = cache.get_cache_size()
    if total_size == 0:
        typer.echo("Cache is already empty.")
        return

    if not force:
        typer.confirm(
            f"Delete {format_size(total_size)} from {cache_dir}?",
            abort=True,
        )

    cache.clean()
    typer.echo("Cache cleared.")
