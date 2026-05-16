## Why

The project currently declares `ruff` and `mypy` as dev dependencies and has `[tool.ruff]` / `[tool.mypy]` sections in both `pyproject.toml` files, but neither tool runs on this development platform (Android/Termux, no Rust compilation available). There are no security scanning or dependency auditing tools configured, and the codebase has ~100 lint issues across ~25 files. This change establishes a working, platform-compatible Python toolchain and fixes all identified issues.

## What Changes

- Add `flake8`, `pylint`, `pyright`, `bandit`, `pip-audit` to dev dependencies (both packages)
- Add tool configuration for `flake8`, `pylint`, `pyright`, `bandit` to both `pyproject.toml` files
- Keep existing `ruff`/`mypy` config (hybrid approach — works on standard platforms)
- Fix all `flake8` issues: unused imports (F401), line length (E501), redefined commands (F811), indentation (E127/E128), blank lines (E305/W292/W391), ambiguous names (E741), unused variables (F841)
- Fix all `pylint` issues: `open()` without encoding (W1514), `subprocess.run` without `check=` (W1510), useless try-except-raise (W0706), unused arguments (W0613), unnecessary lambdas (W0108), redefined outer names (W0621), broad-except (W0718), protected access (W0212), missing function args (E1120)
- Fix `bandit` issues: `shell=True` in tutor.py → list-based subprocess, hardcoded `/tmp` in tests → `tempfile`, suppress assert-in-tests
- Configure `pip-audit` workflow for dependency vulnerability scanning
- Generate `requirements.txt` files for both packages to enable `pip-audit`

## Capabilities

### New Capabilities
- `linting`: Run flake8 and pylint on both packages to enforce code quality
- `type-checking`: Run pyright for static type checking with proper import resolution
- `security-scanning`: Run bandit to detect security vulnerabilities in source code
- `dependency-auditing`: Run pip-audit to detect known vulnerabilities in dependencies

### Modified Capabilities
- (none — no existing spec-level behavior is changing)

## Impact

- **pyproject.toml** (both packages): Add dev dependencies (`flake8`, `pylint`, `pyright`, `bandit`, `pip-audit`), add `[tool.*]` sections for each new tool
- **prism-cli/prism_cli/main.py**: Rename Click commands `rm` → `path_rm`/`tag_rm`, `add` → `vault_add` to resolve redefinition conflicts
- **prism-cli/prism_cli/tutor.py**: Fix `shell=True` security issue, fix open() encoding, remove useless try-except-raise wrappers, remove unnecessary lambdas
- **prism-core/tests/test_graph.py**: Replace hardcoded `/tmp` with `tempfile`
- **~20 other files**: Unused import cleanup, line wrapping, indentation fixes
- **New files**: `requirements-prism-core.txt`, `requirements-prism-cli.txt` for pip-audit
