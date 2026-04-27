# snackbox

**A release pipeline tool for Python apps on Windows.**

Packages your Python project into a self-contained Windows release using embedded Python, a compiled launcher stub with custom icon, and an optional Inno Setup installer. No freezing, no bytecode magic — just normal Python, transparently packaged.

## Installation

```bash
pipx install snackbox
```

Or with pip:

```bash
pip install snackbox
```

## Quick Start

```bash
# Generate a starter config
snackbox init

# Edit snackbox.yaml to match your project

# Build a release folder
snackbox build

# Build a release + Inno Setup installer
snackbox installer
```

## What it does

`snackbox build` creates a `release/` folder containing:

```
release/
├── myapp.exe           # Compiled launcher stub (with your icon)
├── version.txt         # Version string (e.g., 1.0.0.abc1234)
├── python/             # Embedded Python environment
│   ├── python.exe
│   ├── Lib/site-packages/
│   │   └── myapp/      # Your installed package
│   └── ...
└── (your assets)       # Config files, data, etc.
```

`snackbox installer` additionally creates an Inno Setup installer `.exe`.

## Configuration

Create `snackbox.yaml` in your project root:

```yaml
app:
  name: "My App"
  slug: "myapp"
  version_from: "pyproject.toml"
  icon: "assets/myapp.ico"  # optional

python:
  version: "3.12.10"

build:
  wheel:
    backend: "poetry"  # or "pip", "hatch"
  extra_deps: []

launcher:
  entry_point: "myapp"    # runs: python -m myapp
  console: "yes"          # "yes", "no", or "attach"

assets:
  - "config.yaml:config.yaml"
  - "data:data"

version:
  git_hash: true
  dirty_flag: true
  save_patch: true

installer:
  enabled: true
  publisher: "Your Name"
  url: "https://github.com/you/myapp"
  install_dir: "{localappdata}\\MyApp"
  add_to_path: true
  start_menu: true
```

## Console Modes

The `launcher.console` setting controls how the launcher behaves:

- **`"yes"`** - Always show console (standard CLI app)
- **`"no"`** - No console window (GUI app)
- **`"attach"`** - Smart mode: attaches to existing terminal if launched from one, otherwise runs headless. Perfect for CLI tools that can also run as background services.

## Commands

```bash
snackbox init              # Generate starter snackbox.yaml
snackbox build             # Build release folder
snackbox build --clean     # Rebuild embedded Python from scratch
snackbox build --force     # Force reinstall the app wheel
snackbox installer         # Build release + Inno Setup installer
snackbox cache show        # Show cache location and contents
snackbox cache clean       # Wipe the download cache
snackbox --version         # Print snackbox version
```

## Requirements

- **Windows**: Native builds work directly
- **GCC**: MinGW-w64 for compiling the launcher (install via MSYS2 or scoop)
- **Inno Setup**: For building installers (optional)

## Cross-compilation (Linux/macOS)

Use the Docker image for cross-compilation:

```bash
docker run --rm -v $(pwd):/project ghcr.io/lanceliogs/snackbox build
docker run --rm -v $(pwd):/project ghcr.io/lanceliogs/snackbox installer
```

## License

MIT
