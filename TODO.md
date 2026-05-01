# TODO

## Migrate snackbox build system from Poetry to uv

Low priority — Poetry is only used for snackbox's own development and release.
Does not affect users, the Docker image, or runtime behavior.

### pyproject.toml

- Convert `[tool.poetry]` → PEP 621 `[project]` format
- `[tool.poetry.dependencies]` → `[project.dependencies]`
- `[tool.poetry.group.dev.dependencies]` → `[dependency-groups]`
- `[tool.poetry.scripts]` → `[project.scripts]`
- `packages = [{include = "snackbox", from = "src"}]` → `[tool.hatch.build.targets.wheel]` with `packages = ["src/snackbox"]`
- Template files under `src/snackbox/templates/` are auto-included by hatchling (no explicit `include` needed)
- Replace `poetry-dynamic-versioning` → `hatch-vcs` for git tag versioning
- `[build-system]` → `requires = ["hatchling", "hatch-vcs"]`

### CI (`.github/workflows/ci.yml`)

- Remove `snok/install-poetry@v1`
- `pip install uv` → `uv sync` → `uv run pytest` / `uv run ruff`

### Release (`.github/workflows/release.yml`)

- Remove Poetry + poetry-dynamic-versioning steps
- `poetry build` → `uv build`
- Extract version from built wheel filename or `git describe --tags`
- Keep `fetch-depth: 0` (needed by hatch-vcs)

### Dockerfile

- `pip3 install --break-system-packages poetry uv` → drop `poetry`

### Delete

- `poetry.lock`
