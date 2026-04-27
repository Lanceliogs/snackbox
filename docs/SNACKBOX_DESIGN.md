# snackbox

**A release pipeline tool for Python apps on Windows.**

Packages your Python project into a self-contained Windows release using embedded Python, a compiled launcher stub with custom icon, and an optional Inno Setup installer. No freezing, no bytecode magic — just normal Python, transparently packaged.

- Install: `pipx install snackbox`
- Docker: `docker run ghcr.io/lanceliogs/snackbox`
- Config: `snackbox.yaml` in your project root
- License: MIT (or whatever you prefer)

---

## Reference

The build system this tool generalizes:

- **build.py**: https://github.com/Lanceliogs/midi-event-handler/blob/main/tools/build.py
- **launcher stub (C)**: https://github.com/Lanceliogs/midi-event-handler/tree/main/tools/cli
- **launcher scripts (.bat)**: https://github.com/Lanceliogs/midi-event-handler/tree/main/tools/scripts

---

## Distribution

### pipx (recommended for dev machines)

```
pipx install snackbox
```

On first run, snackbox downloads and caches:
- Embeddable Python (from python.org)
- MinGW-w64 GCC toolchain (for compiling the launcher stub)
- Inno Setup portable (for building installers)

Everything is cached in `~/.snackbox/cache/` so subsequent runs are fast.

### Docker (recommended for CI/CD and cross-packing from Linux/macOS)

```
docker run --rm -v $(pwd):/project ghcr.io/lanceliogs/snackbox build
```

The Docker image ships with everything pre-baked:
- Embeddable Python zips for supported versions
- MinGW-w64 cross-compiler (cross-compiles the launcher .exe from Linux)
- Inno Setup running under Wine (builds Windows installers from Linux)
- snackbox itself

This is the **cross-packing** story: a Linux or macOS developer can produce
a full Windows release (launcher .exe + embedded Python + Inno Setup installer)
without ever touching a Windows machine. The entire toolchain runs inside the
container.

Supported scenarios:
- Linux dev machine → `docker run snackbox build` → Windows release folder
- Linux dev machine → `docker run snackbox installer` → Windows .exe installer
- GitHub Actions (ubuntu runner) → same Docker command → publish installer as release artifact
- Windows dev machine → `pipx install snackbox` → native build (no Docker needed)

---

## CLI

```
snackbox build              # Build release folder
snackbox build --clean      # Rebuild embedded Python from scratch
snackbox build --force      # Force-reinstall the app wheel (keep deps)
snackbox installer          # Build release + Inno Setup installer
snackbox init               # Generate a starter snackbox.yaml
snackbox cache clean        # Wipe the download cache
snackbox cache show         # Show cache location and contents
snackbox --version          # Print snackbox version
```

---

## Config format: snackbox.yaml

```yaml
# -- App identity --
app:
  name: "My App"                        # Display name (used in installer, window title)
  slug: "myapp"                         # Short name for folders, exe, registry keys
  version_from: "pyproject.toml"        # Read version from pyproject.toml (project.version)
  icon: "assets/myapp.ico"              # .ico file for the launcher stub and installer

# -- Python --
python:
  version: "3.12.10"                    # Embeddable Python version to use
  # arch: "amd64"                       # amd64 (default) or win32

# -- Build --
build:
  wheel:
    # How to build the wheel. Supports "poetry", "pip", "hatch", or a custom command.
    backend: "poetry"
    # backend: "pip"
    # backend: "hatch"
    # backend_command: "python -m build --wheel"    # custom override

  # Extra pip packages to install into the embedded Python (beyond the wheel's deps).
  # Useful for optional dependencies not declared in your pyproject.toml.
  extra_deps: []
    # - "some-optional-package==1.2.3"

# -- Launcher stub --
launcher:
  # Entry point to invoke when the .exe is launched.
  # This is a Python module path, invoked as: python -m <entry_point>
  entry_point: "myapp"

  # If true, the launcher runs as a console app (shows a terminal window).
  # If false, it runs as a GUI app (no console window).
  console: true

  # Optional: environment variables set by the launcher before running Python.
  # env:
  #   MY_VAR: "value"

# -- Assets --
# Files and directories to copy into the release folder alongside python/ and the launcher.
assets:
  - src: "config.yaml"
    dst: "config.yaml"

  - src: "assets/icon.ico"
    dst: "icon.ico"

  # Directories are copied recursively
  - src: "src/myapp/web/static"
    dst: "static"

  - src: "src/myapp/web/templates"
    dst: "templates"

# -- Scripts --
# Optional .bat scripts to include in the release root.
# These are simple launcher shortcuts that call python/ with specific arguments.
scripts:
  - src: "tools/scripts/run.bat"
  - src: "tools/scripts/update.bat"

# -- Versioning --
version:
  # Append short git hash to version string (e.g. 1.0.0.abc1234)
  git_hash: true
  # Mark as dirty if repo has uncommitted changes (e.g. 1.0.0.abc1234.dirty)
  dirty_flag: true
  # Save a dirty.patch file in the release if the repo is dirty
  save_patch: true

# -- Installer (Inno Setup) --
installer:
  enabled: true

  # You can provide your own .iss template, or let snackbox generate one.
  # If omitted, snackbox generates a default .iss from the app settings above.
  # template: "installer.iss"

  # Installer-specific overrides (used when generating the default .iss)
  publisher: "Your Name"
  url: "https://github.com/you/yourproject"
  license: "LICENSE"                    # Path to license file shown during install

  # Where the app gets installed on the user's machine
  install_dir: "{localappdata}\\MyApp"

  # Add the install dir to PATH
  add_to_path: true

  # Create a desktop shortcut
  desktop_shortcut: false

  # Create a start menu entry
  start_menu: true

  # Output directory for the generated installer .exe
  output_dir: "build/installer"
```

---

## Project structure

```
snackbox/
├── pyproject.toml
├── LICENSE
├── README.md
├── Dockerfile
├── docker-compose.yml          # For local testing of the Docker image
│
├── src/
│   └── snackbox/
│       ├── __init__.py         # Package version
│       ├── __main__.py         # python -m snackbox
│       ├── cli.py              # CLI entry point (click or argparse)
│       ├── config.py           # YAML config loader + validation
│       ├── errors.py           # Custom exceptions
│       │
│       ├── cache/
│       │   ├── __init__.py
│       │   └── manager.py      # Download, extract, and cache dependencies
│       │
│       ├── steps/
│       │   ├── __init__.py
│       │   ├── python.py       # Download + setup embedded Python
│       │   ├── wheel.py        # Build wheel (poetry/pip/hatch/custom)
│       │   ├── deps.py         # Install wheel + extra deps into embedded Python
│       │   ├── launcher.py     # Compile C launcher stub with GCC
│       │   ├── assets.py       # Copy assets and scripts into release
│       │   ├── version.py      # Stamp version (git hash, dirty flag, patch)
│       │   └── installer.py    # Generate .iss and run Inno Setup
│       │
│       └── templates/
│           ├── launcher.c      # C template for the launcher stub
│           ├── launcher.rc     # Resource file template (icon embedding)
│           ├── installer.iss   # Default Inno Setup script template
│           └── snackbox.yaml   # Starter config (used by `snackbox init`)
│
├── tests/
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_cache.py
│   ├── test_steps/
│   │   ├── test_python.py
│   │   ├── test_wheel.py
│   │   ├── test_launcher.py
│   │   └── test_version.py
│   └── fixtures/
│       └── sample_project/     # Minimal project for integration tests
│
└── docs/                       # Optional, later
```

---

## Build pipeline

When you run `snackbox build`, the following steps execute in order:

```
1. Load config          Read and validate snackbox.yaml
2. Clean                Remove previous release dir (keep python/ unless --clean)
3. Setup Python         Download + extract embeddable Python, bootstrap pip
4. Build wheel          Run the configured backend (poetry/pip/hatch/custom)
5. Install deps         pip install the wheel into the embedded Python
6. Build launcher       Compile launcher.c with GCC (embed icon via .rc)
7. Copy assets          Copy configured files/dirs into the release folder
8. Copy scripts         Copy .bat scripts into the release root
9. Stamp version        Write version.txt (base version + git hash + dirty)
10. Save patch          If dirty, save dirty.patch for traceability
11. Build installer     (if `snackbox installer`) Generate .iss and run ISCC
```

### Output structure (what the user's customer gets)

```
release/
├── myapp.exe               # Compiled C launcher stub (with icon)
├── config.yaml             # User's config file
├── icon.ico                # App icon
├── version.txt             # e.g. "1.2.0.a3f9bc1"
├── static/                 # Copied assets
├── templates/              # Copied assets
├── run.bat                 # Optional helper scripts
└── python/                 # Embedded Python environment
    ├── python.exe
    ├── python312.dll
    ├── python312.zip        # Stdlib
    ├── python312._pth       # Path config (import site uncommented)
    └── Lib/
        └── site-packages/
            └── myapp/       # The installed wheel
```

---

## Launcher stub: launcher.c template

The C launcher is minimal. It finds `python/python.exe` relative to itself and runs `python -m <entry_point>`. This gives the user a clean `.exe` with a custom icon instead of a `.bat` file.

```c
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    char exe_dir[MAX_PATH];
    GetModuleFileNameA(NULL, exe_dir, MAX_PATH);

    // Strip the exe filename to get the directory
    char *last_sep = strrchr(exe_dir, '\\');
    if (last_sep) *last_sep = '\0';

    char cmd[4096];
    // {{ entry_point }} is replaced at build time by snackbox
    snprintf(cmd, sizeof(cmd),
        "\"%s\\python\\python.exe\" -m {{ entry_point }} %s",
        exe_dir,
        GetCommandLineA()  // forward all arguments
    );

    STARTUPINFOA si = { .cb = sizeof(si) };
    PROCESS_INFORMATION pi;

    if (!CreateProcessA(NULL, cmd, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        fprintf(stderr, "Failed to start python (error %lu)\n", GetLastError());
        return 1;
    }

    WaitForSingleObject(pi.hProcess, INFINITE);

    DWORD exit_code;
    GetExitCodeProcess(pi.hProcess, &exit_code);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return (int)exit_code;
}
```

The `launcher.rc` template for embedding the icon:

```rc
1 ICON "{{ icon_path }}"
```

---

## Inno Setup template

snackbox generates a default `.iss` file from the config if the user doesn't provide their own. The template uses Jinja2-style placeholders filled from `snackbox.yaml`:

```iss
[Setup]
AppName={{ app.name }}
AppVersion={{ version }}
AppPublisher={{ installer.publisher }}
AppPublisherURL={{ installer.url }}
DefaultDirName={{ installer.install_dir }}
DefaultGroupName={{ app.name }}
OutputDir={{ installer.output_dir }}
OutputBaseFilename={{ app.slug }}-{{ version }}-setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
{% if installer.start_menu %}
Name: "{group}\{{ app.name }}"; Filename: "{app}\{{ app.slug }}.exe"; IconFilename: "{app}\{{ icon_filename }}"
{% endif %}
{% if installer.desktop_shortcut %}
Name: "{commondesktop}\{{ app.name }}"; Filename: "{app}\{{ app.slug }}.exe"; IconFilename: "{app}\{{ icon_filename }}"
{% endif %}

{% if installer.add_to_path %}
[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{app}"; Check: NeedsAddPath('{app}')

[Code]
function NeedsAddPath(Param: string): Boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', OrigPath) then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
{% endif %}
```

---

## Docker image

```dockerfile
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    mingw-w64 \
    wine64 \
    wget unzip git \
    && rm -rf /var/lib/apt/lists/*

# Install Inno Setup under Wine
RUN wget -q https://jrsoftware.org/download.php/is.exe -O /tmp/is.exe \
    && wine /tmp/is.exe /VERYSILENT /DIR="C:\\InnoSetup" \
    && rm /tmp/is.exe

# Pre-cache common embeddable Python versions
RUN mkdir -p /snackbox/cache/python \
    && for v in 3.11.12 3.12.10 3.13.5; do \
        wget -q "https://www.python.org/ftp/python/${v}/python-${v}-embed-amd64.zip" \
            -O "/snackbox/cache/python/python-${v}-embed-amd64.zip"; \
    done

# Install snackbox
COPY . /snackbox/src
RUN pip install /snackbox/src

ENV SNACKBOX_CACHE_DIR=/snackbox/cache
ENV SNACKBOX_ISCC_PATH="wine C:\\InnoSetup\\ISCC.exe"
ENV SNACKBOX_GCC=x86_64-w64-mingw32-gcc
ENV SNACKBOX_WINDRES=x86_64-w64-mingw32-windres

WORKDIR /project
ENTRYPOINT ["snackbox"]
```

---

## pyproject.toml (for snackbox itself)

```toml
[project]
name = "snackbox"
version = "0.1.0"
description = "Release pipeline for Python apps on Windows — embedded Python, launcher stub, Inno Setup installer."
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
dependencies = [
    "click",
    "pyyaml",
    "jinja2",
]

[project.scripts]
snackbox = "snackbox.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Minimal usage example

1. Install snackbox:
   ```
   pipx install snackbox
   ```

2. Create a config in your project:
   ```
   snackbox init
   ```

3. Edit `snackbox.yaml` to match your project.

4. Build a release:
   ```
   snackbox build
   ```

5. Build an installer:
   ```
   snackbox installer
   ```

---

## Platform matrix

| Host OS | Install method | Launcher .exe | Installer .exe | How |
|---------|---------------|---------------|----------------|-----|
| Windows | `pipx install snackbox` | gcc (native) | ISCC.exe (native) | Direct |
| Linux   | `docker run snackbox` | x86_64-w64-mingw32-gcc | Wine + ISCC.exe | Cross-compile |
| macOS   | `docker run snackbox` | x86_64-w64-mingw32-gcc | Wine + ISCC.exe | Cross-compile |
| Any CI  | Docker image | x86_64-w64-mingw32-gcc | Wine + ISCC.exe | Cross-compile |

The pip-installed version detects the host OS and refuses to run on non-Windows
with a clear message pointing the user to the Docker image instead.

---

## Open questions / future ideas

- **Config validation**: use pydantic or a JSON schema to validate snackbox.yaml with clear error messages.
- **Hooks**: pre-build and post-build hooks (arbitrary commands) for custom steps.
- **Multiple entry points**: support building multiple .exe stubs from one config.
- **GUI launcher variant**: `console: false` compiles with `-mwindows` to hide the console.
- **Auto-updater**: bake in a lightweight update check mechanism.
- **Plugin system**: let users write Python plugins for custom build steps.
