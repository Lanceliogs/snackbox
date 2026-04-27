# Snackbox Implementation Plan

This document outlines the implementation phases for snackbox. Each phase builds on the previous one, with the goal of having a working prototype as early as possible.

---

## Phase 1: Project Skeleton

Set up the basic project structure and CLI scaffolding.

- [ ] Create `pyproject.toml` with dependencies (click, pyyaml, jinja2)
- [ ] Create package structure: `src/snackbox/`
- [ ] Implement `__init__.py` with version
- [ ] Implement `__main__.py` for `python -m snackbox`
- [ ] Implement basic `cli.py` with click commands (stubs):
  - `snackbox build`
  - `snackbox installer`
  - `snackbox init`
  - `snackbox cache clean`
  - `snackbox cache show`
  - `snackbox --version`
- [ ] Create `errors.py` with custom exceptions

**Milestone:** `snackbox --help` works.

---

## Phase 2: Config System

Load and validate `snackbox.yaml`.

- [ ] Implement `config.py`:
  - Load YAML from project root
  - Validate required fields
  - Apply defaults for optional fields
  - Resolve paths relative to project root
- [ ] Create starter template `templates/snackbox.yaml`
- [ ] Implement `snackbox init` to copy the template

**Milestone:** `snackbox init` generates a config, config loads without errors.

---

## Phase 3: Cache Manager

Handle downloading and caching of external dependencies.

- [ ] Implement `cache/manager.py`:
  - Determine cache directory (`~/.snackbox/cache/` or `SNACKBOX_CACHE_DIR`)
  - Download files with progress indication
  - Extract zip archives
  - Track cached items
- [ ] Implement `snackbox cache show` and `snackbox cache clean`

**Milestone:** Can download and cache embeddable Python zip.

---

## Phase 4: Embedded Python Setup

Download and prepare the embedded Python environment.

- [ ] Implement `steps/python.py`:
  - Download embeddable Python from python.org
  - Extract to `release/python/`
  - Patch `python3XX._pth` to enable site-packages
  - Bootstrap pip via `get-pip.py`
- [ ] Wire into `snackbox build`

**Milestone:** `snackbox build` creates `release/python/` with working pip.

---

## Phase 5: Wheel Building

Build the user's project as a wheel.

- [ ] Implement `steps/wheel.py`:
  - Support `poetry build -f wheel`
  - Support `pip wheel . --no-deps`
  - Support `hatch build -t wheel`
  - Support custom `backend_command`
  - Locate the built `.whl` file

**Milestone:** `snackbox build` produces a wheel in `dist/`.

---

## Phase 6: Dependency Installation

Install the wheel and dependencies into embedded Python.

- [ ] Implement `steps/deps.py`:
  - Run `python/python.exe -m pip install <wheel>`
  - Install `extra_deps` from config
  - Handle `--force` flag for reinstall

**Milestone:** `snackbox build` installs the app into `release/python/Lib/site-packages/`.

---

## Phase 7: Launcher Stub

Compile the C launcher with GCC.

- [ ] Create `templates/launcher.c` (with `{{ entry_point }}` placeholder)
- [ ] Create `templates/launcher.rc` (for icon embedding)
- [ ] Implement `steps/launcher.py`:
  - Render templates with Jinja2
  - Detect GCC (native or MinGW cross-compiler)
  - Compile `.rc` to `.o` with windres
  - Compile and link `.exe` with gcc
  - Support `console: true/false` (`-mconsole` vs `-mwindows`)

**Milestone:** `snackbox build` produces `release/<slug>.exe` that launches the app.

---

## Phase 8: Assets and Scripts

Copy user files into the release.

- [ ] Implement `steps/assets.py`:
  - Copy files and directories from `assets:` config
  - Copy `.bat` scripts from `scripts:` config

**Milestone:** Release folder contains all configured assets.

---

## Phase 9: Version Stamping

Generate version metadata.

- [ ] Implement `steps/version.py`:
  - Read base version from `pyproject.toml`
  - Append git short hash if `git_hash: true`
  - Append `.dirty` if `dirty_flag: true` and repo is dirty
  - Write `version.txt` to release folder
  - Save `dirty.patch` if `save_patch: true`

**Milestone:** `release/version.txt` contains full version string.

---

## Phase 10: Inno Setup Installer

Generate and build the Windows installer.

- [ ] Create `templates/installer.iss` (Jinja2 template)
- [ ] Implement `steps/installer.py`:
  - Render `.iss` template with config values
  - Detect ISCC.exe (native or Wine)
  - Run ISCC to build installer
- [ ] Wire into `snackbox installer`

**Milestone:** `snackbox installer` produces a working `.exe` installer.

---

## Phase 11: Docker Image

Enable cross-platform builds.

- [ ] Create `Dockerfile`:
  - Ubuntu base with Python, MinGW, Wine
  - Install Inno Setup under Wine
  - Pre-cache common Python versions
  - Install snackbox
- [ ] Create `docker-compose.yml` for local testing
- [ ] Test full build pipeline in container

**Milestone:** `docker run snackbox build` works on Linux/macOS.

---

## Phase 12: Polish and Testing

Harden the tool for real-world use.

- [ ] Add comprehensive error messages
- [ ] Add `--verbose` / `--quiet` flags
- [ ] Add `--clean` flag to rebuild Python env from scratch
- [ ] Write unit tests for config parsing
- [ ] Write integration tests with a sample project
- [ ] Create `tests/fixtures/sample_project/`

**Milestone:** Test suite passes, tool handles edge cases gracefully.

---

## Implementation Order (Suggested)

For a working prototype as fast as possible:

1. **Phase 1** - Get CLI running
2. **Phase 2** - Config loading
3. **Phase 3** - Cache manager
4. **Phase 4** - Embedded Python (this is the core)
5. **Phase 6** - Dep installation (skip wheel build initially, test with a pre-built wheel)
6. **Phase 7** - Launcher stub (now you have a working release)
7. **Phase 5** - Wheel building (automate what you did manually)
8. **Phase 8** - Assets
9. **Phase 9** - Version stamping
10. **Phase 10** - Installer
11. **Phase 11** - Docker
12. **Phase 12** - Tests and polish

---

## Dependencies

External tools required:

| Tool | Windows | Linux (Docker) |
|------|---------|----------------|
| GCC | MinGW-w64 or MSVC | `x86_64-w64-mingw32-gcc` |
| windres | MinGW-w64 | `x86_64-w64-mingw32-windres` |
| Inno Setup | ISCC.exe | Wine + ISCC.exe |

Python dependencies (for snackbox itself):

- `click` - CLI framework
- `pyyaml` - Config parsing
- `jinja2` - Template rendering
- `requests` - Downloads (or use urllib)

---

## Notes

- Start with Windows-only support, add Docker/cross-compile later
- Use environment variables for tool paths (`SNACKBOX_GCC`, `SNACKBOX_ISCC_PATH`, etc.)
- Keep each step module independent — should be testable in isolation
- Print clear progress messages during build
