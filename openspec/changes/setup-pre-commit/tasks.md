## 1. Create `.pre-commit-config.yaml` at repo root

- [x] 1.1 Create `.pre-commit-config.yaml` with ruff check hooks (prism-core, prism-cli) using `repo: local`, `language: system`, `files: ^prism-core/` and `files: ^prism-cli/`, `args: [check, --fix, --config, <project>/pyproject.toml]`
- [x] 1.2 Add ruff format hooks (prism-core, prism-cli) with `args: [format, --config, <project>/pyproject.toml]` after lint hooks
- [x] 1.3 Add pytest hooks (prism-core, prism-cli) with `pass_filenames: false`, `always_run: true`, `args: [<project>/tests/, -x, -q]`
- [x] 1.4 Add pyright hooks (prism-core, prism-cli) with `pass_filenames: false`, `always_run: true`, `args: [--project, <project>/pyproject.toml]`
- [x] 1.5 Add bandit hooks (prism-core, prism-cli) with `args: [-c, <project>/pyproject.toml]`
- [x] 1.6 Add pip-audit hook with `pass_filenames: false`, `always_run: true`

## 2. Add ruff format config to both pyproject.toml files

- [x] 2.1 Add `[tool.ruff.format]` section with `quote-style = "double"` to `prism-core/pyproject.toml`
- [x] 2.2 Add `[tool.ruff.format]` section with `quote-style = "double"` to `prism-cli/pyproject.toml`

## 3. Install and verify

- [x] 3.1 Run `pip install pre-commit` in the dev environment
- [x] 3.2 Run `pre-commit install` from repo root
- [x] 3.3 Run `pre-commit run --all-files` to verify all hooks pass on the existing codebase
- [x] 3.4 Run `pre-commit run --all-files` individually for each hook to verify isolation
