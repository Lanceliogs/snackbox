"""Configuration loader and validation for snackbox.yaml."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from snackbox.errors import ConfigError


@dataclass
class AppConfig:
    name: str
    slug: str
    version_from: str = "pyproject.toml"
    icon: str | None = None


@dataclass
class PythonConfig:
    version: str = "3.12.10"
    arch: str = "amd64"


@dataclass
class BuildConfig:
    backend: str = "poetry"
    backend_command: str | None = None
    extra_deps: list[str] = field(default_factory=list)


@dataclass
class LauncherConfig:
    entry_point: str
    console: str = "yes"  # "yes", "no", or "attach"
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class AssetEntry:
    src: str
    dst: str


@dataclass
class VersionConfig:
    git_hash: bool = True
    dirty_flag: bool = True
    save_patch: bool = True


@dataclass
class InstallerConfig:
    enabled: bool = True
    template: str | None = None
    app_guid: str | None = None  # Windows AppId GUID for upgrades
    publisher: str = ""
    url: str = ""
    license: str | None = None
    install_dir: str = "{localappdata}\\{app.slug}"
    add_to_path: bool = True
    desktop_shortcut: bool = False  # Default checkbox state
    start_menu: bool = True  # Default checkbox state
    run_after_install: bool = True  # Default checkbox state
    output_dir: str = "build/installer"


@dataclass
class Config:
    app: AppConfig
    python: PythonConfig
    build: BuildConfig
    launcher: LauncherConfig
    assets: list[AssetEntry]
    version: VersionConfig
    installer: InstallerConfig
    project_root: Path

    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the project root."""
        return self.project_root / path


def _get_required(data: dict[str, Any], key: str, section: str) -> Any:
    """Get a required field or raise ConfigError."""
    if key not in data:
        raise ConfigError(f"Missing required field '{key}' in '{section}' section")
    return data[key]


def _parse_app(data: dict[str, Any]) -> AppConfig:
    """Parse the app section."""
    if "app" not in data:
        raise ConfigError("Missing required 'app' section")
    app_data = data["app"]
    version_from = app_data.get("version_from", "pyproject.toml")
    if version_from != "git" and not version_from.endswith(".toml"):
        raise ConfigError(f"Invalid version_from '{version_from}'. Use 'git' or a .toml filename")

    return AppConfig(
        name=_get_required(app_data, "name", "app"),
        slug=_get_required(app_data, "slug", "app"),
        version_from=version_from,
        icon=app_data.get("icon"),
    )


def _parse_python(data: dict[str, Any]) -> PythonConfig:
    """Parse the python section."""
    py_data = data.get("python", {})
    return PythonConfig(
        version=py_data.get("version", "3.12.10"),
        arch=py_data.get("arch", "amd64"),
    )


def _parse_build(data: dict[str, Any]) -> BuildConfig:
    """Parse the build section."""
    build_data = data.get("build", {})
    wheel_data = build_data.get("wheel", {})
    return BuildConfig(
        backend=wheel_data.get("backend", "poetry"),
        backend_command=wheel_data.get("backend_command"),
        extra_deps=build_data.get("extra_deps", []),
    )


def _parse_launcher(data: dict[str, Any]) -> LauncherConfig:
    """Parse the launcher section."""
    if "launcher" not in data:
        raise ConfigError("Missing required 'launcher' section")
    launcher_data = data["launcher"]

    console = launcher_data.get("console", "yes")
    # Accept bool for backwards compatibility, convert to string
    if console is True:
        console = "yes"
    elif console is False:
        console = "no"

    valid_modes = ("yes", "no", "attach")
    if console not in valid_modes:
        raise ConfigError(
            f"Invalid console mode '{console}'. Must be one of: {', '.join(valid_modes)}"
        )

    return LauncherConfig(
        entry_point=_get_required(launcher_data, "entry_point", "launcher"),
        console=console,
        env=launcher_data.get("env", {}),
    )


def _parse_assets(data: dict[str, Any]) -> list[AssetEntry]:
    """Parse the assets section.

    Supports two formats:
      - Short: "src:dst" or "src" (dst defaults to basename)
      - Long: {src: "...", dst: "..."}
    """
    assets_data = data.get("assets", [])
    result = []

    for a in assets_data:
        if isinstance(a, str):
            if ":" in a:
                src, dst = a.split(":", 1)
            else:
                src = a
                dst = Path(a).name
            result.append(AssetEntry(src=src.strip(), dst=dst.strip()))
        elif isinstance(a, dict):
            result.append(AssetEntry(src=a["src"], dst=a["dst"]))
        else:
            raise ConfigError(f"Invalid asset entry: {a}")

    return result


def _parse_version(data: dict[str, Any]) -> VersionConfig:
    """Parse the version section."""
    ver_data = data.get("version", {})
    return VersionConfig(
        git_hash=ver_data.get("git_hash", True),
        dirty_flag=ver_data.get("dirty_flag", True),
        save_patch=ver_data.get("save_patch", True),
    )


def _parse_installer(data: dict[str, Any]) -> InstallerConfig:
    """Parse the installer section."""
    inst_data = data.get("installer", {})
    return InstallerConfig(
        enabled=inst_data.get("enabled", True),
        template=inst_data.get("template"),
        app_guid=inst_data.get("app_guid"),
        publisher=inst_data.get("publisher", ""),
        url=inst_data.get("url", ""),
        license=inst_data.get("license"),
        install_dir=inst_data.get("install_dir", "{localappdata}\\{app.slug}"),
        add_to_path=inst_data.get("add_to_path", True),
        desktop_shortcut=inst_data.get("desktop_shortcut", False),
        start_menu=inst_data.get("start_menu", True),
        run_after_install=inst_data.get("run_after_install", True),
        output_dir=inst_data.get("output_dir", "build/installer"),
    )


def load_config(config_path: Path | None = None) -> Config:
    """Load and validate snackbox.yaml from the given path or current directory."""
    if config_path is None:
        config_path = Path.cwd() / "snackbox.yaml"

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    project_root = config_path.parent

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError("Config file must be a YAML mapping")

    return Config(
        app=_parse_app(data),
        python=_parse_python(data),
        build=_parse_build(data),
        launcher=_parse_launcher(data),
        assets=_parse_assets(data),
        version=_parse_version(data),
        installer=_parse_installer(data),
        project_root=project_root,
    )
