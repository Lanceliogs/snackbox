# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-05-02

### Added
- `uv` as a required dependency — handles wheel building and package installation
- `version_from: "git"` config option — reads version from git tags via `git describe --tags`, decoupled from Poetry
- `uv` added to Docker image
- Docker: `git safe.directory` wildcard for mounted repos in CI

### Fixed
- Cross-compile: ISCC `.iss` file path not converted to Wine format (ISCC showed help instead of compiling)
- Cross-compile: icon and license paths not converted to Wine format (Inno Setup "Path not found" error)
- Cross-compile: Linux pip installed Linux-native packages (`.so` files, `uvloop`, etc.) into Windows bundle, causing ~30% installer bloat
- pipx: snackbox now finds its bundled `uv` binary instead of relying on PATH

### Changed
- Wheel building always uses `uv build --wheel` — removed `build.wheel.backend` and `build.wheel.backend_command` config options
- Dependency installation uses `uv pip install --target` on all platforms (was `pip` on Windows, `pip3 --target` on Linux)
- Pip is no longer bootstrapped into the embedded Python (~10MB saved per build)
- `version_from` no longer checks for `[tool.poetry-dynamic-versioning]` — use `version_from: "git"` instead

## [0.1.1] - 2026-05-01

### Added
- `snackbox guid` command to generate Windows AppId GUIDs
- `--generate-guid` / `-g` flag on `snackbox init`
- `installer.app_guid` config for Inno Setup AppId (required for upgrades)
- `installer.run_after_install` config for "Launch app" checkbox default
- `installer.license` now works (renders `LicenseFile` in installer)
- Installer uses `[Tasks]` section — `start_menu`, `desktop_shortcut`, and `run_after_install` are user-toggleable checkboxes with configurable defaults
- Dynamic versioning support: detects `[tool.poetry-dynamic-versioning]` and reads version from git tags
- Post-tag versioning: commits after a tag produce `X.Y.Z.postN`
- Graceful fallback when git is unavailable (warning + static version)
- CI workflow runs tests on PR only; build/release triggers on merge to main
- Example GitHub workflow and snackbox.yaml in `examples/`
- MIT LICENSE file
- Poetry dynamic versioning for snackbox itself

### Fixed
- Version parser now handles inline TOML comments (`version = "0.0.0"  # comment`)
- `installer.license` config was parsed but never passed to template

### Changed
- Release workflow triggers on push to main (build) and tags (publish to PyPI)
- CI workflow no longer triggers on push to main (only PRs)
- Docker workflow no longer triggers on PRs

## [0.1.1] - 2026-04-28

### Added
- `-f/--file` option to specify custom config file
- Auto-download of MinGW-w64 toolchain (zero manual setup on Windows)
- Auto-download of Inno Setup
- Docker support for cross-compilation from Linux
- Docker volume support for persistent cache (`snackbox-cache`)
- Cache location messages (`Using cache:` / `Using Docker cache:`)
- Warning when running cache commands in Docker

### Changed
- Release folder renamed from `release/` to `{slug}-release/`

### Fixed
- Wine path conversion for Inno Setup cross-compilation
- Xvfb setup for Wine in Docker

## [0.1.0] - 2026-04-27

### Added
- Initial release of snackbox
- `snackbox init` - Generate starter snackbox.yaml
- `snackbox build` - Build release folder with embedded Python and launcher
- `snackbox installer` - Build Inno Setup installer
- `snackbox cache show/clean` - Cache management commands
- Three launcher console modes: `yes`, `no`, `attach`
- Version stamping with git hash and dirty flag
- Asset copying with `src:dst` shorthand syntax
- 78 tests with pytest
- Ruff linting
