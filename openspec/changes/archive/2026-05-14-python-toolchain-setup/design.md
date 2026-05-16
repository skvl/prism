## Context

The project runs on Android/Termux (arm64, Python 3.13). Rust-based tools (ruff, mypy, black) have no pre-built wheels for this platform and fail to compile. Pure-Python tools (flake8, pylint, bandit, pip-audit) install via pip without issues. pyright works via a bundled Node.js binary.

The current `pyproject.toml` files only declare `ruff` and `mypy` under `[project.optional-dependencies] dev`, neither of which function here. There are no security scanning or dependency auditing tools configured.

The codebase has been audited with available tools (flake8, pylint, bandit, pyright) revealing ~100 issues across ~25 files in both packages.

## Goals / Non-Goals

**Goals:**
- Establish a working linting toolchain (flake8 + pylint) that runs on this platform
- Add type checking with pyright (properly configured for import resolution)
- Add security scanning with bandit
- Add dependency vulnerability auditing with pip-audit
- Fix every detected issue across both packages
- Keep ruff/mypy config intact for developers on standard platforms

**Non-Goals:**
- Replacing ruff's auto-formatting (no formatter will work here — black also requires Rust)
- CI/CD pipeline configuration (pre-commit, GitHub Actions, etc.)
- Changing the project's type system, API, or behavior
- Adding type annotations beyond what's needed to fix pyright issues

## Decisions

**1. Hybrid tool config — ruff/mypy stay, flake8/pylint added**
- ruff/mypy are industry standard for modern Python projects
- Keeping them in `[tool.ruff]` / `[tool.mypy]` sections means no breakage for standard-platform developers
- flake8/pylint are pure Python and work here
- Configurations live in `pyproject.toml` per existing convention

**2. pyright over mypy for type checking on this platform**
- mypy cannot install via pip (Rust dep) or termux (needs root)
- pyright installs as a pure Python package with bundled Node.js — works with `pip install pyright`
- Needs `pyrightconfig.json` or `[tool.pyright]` section for import resolution
- Drawback: pyright catches different issues than mypy; they're complementary, not identical

**3. `shell=True` → list-based `subprocess.run` in tutor.py**
- Bandit flags `shell=True` as HIGH severity (CWE-78: OS command injection)
- The tutor executes `prism` commands as subprocesses — if any argument came from user input, shell injection is possible
- Switching to list-based calls eliminates the vector entirely
- The `command_str` in tutor.py needs to be split or built as a list

**4. Hardcoded `/tmp` → `tempfile` in tests**
- bandit B108: hardcoded temp directories are race-condition-prone
- Using `tempfile.TemporaryDirectory` or `tempfile.mkdtemp()` is the standard fix
- This is test code, so the actual security risk is low, but the fix is trivial and eliminates noise

**5. Click command renames for F811 issues**
- `main.py` uses Click groups: `cli`, `path_cmd`, `tag_cmd`, `vault_cmd`
- `rm` is defined on both `path_cmd` group (line 92) and `tag_cmd` group (line 209)
- `add` is defined on both `vault_cmd` group (line 185) and... actually let me re-check
- flake8 F811 fires because the function name shadows the previous definition
- Rename functions to `path_rm`, `tag_rm`, `vault_add` and pass `name=` to `@click.command()` to preserve CLI interface

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| `pip-audit` can't parse `pyproject.toml` directly | Generate `requirements.txt` from pip freeze / pip-compile |
| Click command renames may break internal callers | Only function names change; CLI names preserved via `@click.command(name=...)` |
| pyright import resolution may still fail | Add `extraPaths` in pyright config pointing to editable installs |
| ruff/mypy config becomes stale since they can't be tested here | Document in AGENTS.md: "unit-tested on standard platforms" |
