## Context

The project is a monorepo with two Python packages (`prism-core`, `prism-cli`), each with its own `pyproject.toml` config. Both declare dev dependencies: pytest, ruff, mypy, flake8, pylint, pyright, bandit, pip-audit. All tools are installed in the development environment.

Currently there's no pre-commit enforcement — developers must remember to run each tool manually. This design adds pre-commit hooks using `repo: local` so no additional dependencies or external hook sources are needed.

## Goals / Non-Goals

**Goals:**
- Add `.pre-commit-config.yaml` at repo root with `repo: local` hooks
- Run per-project hooks: lint → format → tests → type check → security → audit
- Each hook uses explicit `--config` pointing to the project's `pyproject.toml`
- Hook order fails fast: quick checks before slow ones

**Non-Goals:**
- Adding new dev dependencies (all tools already declared)
- Adding CI/CD pipeline configuration
- Removing or changing existing flake8/pylint configs
- Changing ruff lint rules — only adding `[tool.ruff.format]` for formatting

## Decisions

**1. `repo: local` for all hooks over external hook repos**
- All tools are already system-installed — no need for pre-commit hook repos (ruff-pre-commit, pyright-python, PyCQA/bandit, etc.)
- Versions always match what's in the dev environment, never drift from external hook revs
- Simpler config, no network fetch during `pre-commit install` or `pre-commit autoupdate`
- Trade-off: must manually keep tool versions in sync with dev deps

**2. Per-project hook instances with `files:` patterns over root-level runs**
- Each hook instance targets `^prism-core/` or `^prism-cli/` so ruff/pyright/bandit auto-scope to the right directory
- Explicit `--config` flags ensure each tool reads the correct `pyproject.toml`
- Scales cleanly as more projects join the monorepo — just append hook instances with new paths

**3. Hook ordering: lint → format → tests → type check → security → audit**
- ruff check --fix (fastest, ~0.3s): catches lint errors, sorts imports
- ruff format (~0.1s): lays out code cleanly after fixes
- pytest -x -q (~5-10s): fails fast on broken tests before slow checks
- pyright (~3-5s): type checks a known-good codebase
- bandit (~1s): security scan on already-valid code
- pip-audit (~2s): dependency scan, runs last since it's independent of code changes

**4. `always_run: true` for pyright, pytest, pip-audit**
- pyright, pytest, pip-audit need to see the full project, not just staged files
- `pass_filenames: false` + `always_run: true` ensures they run on the full codebase

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Pre-commit hooks are slow enough to annoy developers (~15-20s total) | Order fails fast; `ruff check --fix` + `ruff format` are sub-second; only pyright and pytest are the bottlenecks |
| pip-audit false positives on every commit | Developer can `SKIP=pip-audit git commit` as escape hatch; address upstream false positives as they arise |
| Tool version drift between dev deps and installed system tools | Since hooks use `language: system`, what you run is what you have installed. `pip install -e ".[dev]"` keeps them in sync |
| `ruff check --fix` modifies files; combined with `ruff format` could conflict | Ruff is designed for this: `check --fix` normalizes (imports, lint), then `format` normalizes layout. Pre-commit stages intermediate changes |
| pytest in pre-commit can be brittle with state (temp vaults, filesystem) | Tests already use pytest tmp_path fixtures; should be hermetic. If slow, can move to CI-only later |
