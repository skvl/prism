## 1. Tool Configuration

- [x] 1.1 Add `flake8`, `pylint`, `pyright`, `bandit`, `pip-audit` to `[project.optional-dependencies] dev` in `prism-core/pyproject.toml`
- [x] 1.2 Add flake8 config under `[tool.flake8]` in `prism-core/pyproject.toml` (max-line-length=100)
- [x] 1.3 Add pylint config under `[tool.pylint]` in `prism-core/pyproject.toml` (max-line-length=100, disable=C,R)
- [x] 1.4 Add pyright config under `[tool.pyright]` in `prism-core/pyproject.toml` (extraPaths for editable installs)
- [x] 1.5 Add bandit config under `[tool.bandit]` in `prism-core/pyproject.toml` (skip B101 in tests, exclude tests)
- [x] 1.6 Add `flake8`, `pylint`, `pyright`, `bandit`, `pip-audit` to `[project.optional-dependencies] dev` in `prism-cli/pyproject.toml`
- [x] 1.7 Add flake8 config under `[tool.flake8]` in `prism-cli/pyproject.toml`
- [x] 1.8 Add pylint config under `[tool.pylint]` in `prism-cli/pyproject.toml`
- [x] 1.9 Add pyright config under `[tool.pyright]` in `prism-cli/pyproject.toml`
- [x] 1.10 Add bandit config under `[tool.bandit]` in `prism-cli/pyproject.toml`
- [x] 1.11 Create `requirements-prism-core.txt` with non-local dependencies for pip-audit
- [x] 1.12 Create `requirements-prism-cli.txt` with non-local dependencies for pip-audit

## 2. Fix Unused Imports (F401)

- [x] 2.1 Remove unused `pathlib.Path` import in `prism-core/prism/graph/links.py`
- [x] 2.2 Remove unused `pathlib.Path` import in `prism-core/prism/node/manager.py`
- [x] 2.3 Remove unused `pathlib.Path` import in `prism-core/prism/node/metadata.py`
- [x] 2.4 Remove unused `pathlib.Path` and other unused imports in `prism-core/prism/node/storage.py`
- [x] 2.5 Remove unused `pathlib.Path` import in `prism-core/prism/path/resolver.py`
- [x] 2.6 Remove unused `json` import in `prism-core/prism/query/engine.py`
- [x] 2.7 Remove unused `typing.Optional` import in `prism-core/prism/query/parser.py`
- [x] 2.8 Remove unused `typing.Optional` import in `prism-core/prism/tracking.py`
- [x] 2.9 Remove unused `os` import in `prism-core/prism/vault/context.py`
- [x] 2.10 Remove unused `os` import in `prism-core/prism/vault/registry.py`
- [x] 2.11 Remove unused `shutil` import in `prism-core/prism/vault/vault.py`
- [x] 2.12 Remove unused imports in test files: `os`, `tempfile`, `pytest` in `test_types.py`; `uuid_to_path` in `test_storage.py`; `TOTAL_LESSONS` in `test_tutor.py`; `complete_path` in `test_completions.py`
- [x] 2.13 Remove unused `typing.Any` import in `prism-cli/prism_cli/commands.py`
- [x] 2.14 Remove unused `dataclasses.field` import in `prism-cli/prism_cli/tutor.py`

## 3. Fix Line Length Issues (E501)

- [x] 3.1 Wrap long lines in `prism-core/prism/node/manager.py` (3 lines)
- [x] 3.2 Wrap long lines in `prism-core/prism/node/__init__.py`
- [x] 3.3 Wrap long lines in `prism-core/prism/tracking.py`
- [x] 3.4 Wrap long lines in `prism-core/prism/types/loader.py` (2 lines)
- [x] 3.5 Wrap long lines in `prism-core/prism/types/validator.py` (2 lines)
- [x] 3.6 Wrap long line in `prism-core/prism/vault/vault.py`
- [x] 3.7 Wrap long lines in `prism-core/prism/path/resolver.py`
- [x] 3.8 Wrap long lines in `prism-core/tests/test_graph.py` (3 lines)
- [x] 3.9 Wrap long lines in `prism-core/tests/test_manager.py`, `test_query.py`, `test_tutor.py`
- [x] 3.10 Wrap long lines in `prism-cli/prism_cli/commands.py` (10 lines)
- [x] 3.11 Wrap long lines in `prism-cli/prism_cli/main.py` (8 lines)
- [x] 3.12 Wrap long lines in `prism-cli/prism_cli/repl.py` (13 lines)
- [x] 3.13 Wrap long lines in `prism-cli/prism_cli/tutor.py`
- [x] 3.14 Wrap long lines in `prism-cli/tests/test_main.py` (12 lines)
- [x] 3.15 Wrap long lines in `prism-cli/tests/test_repl.py` (3 lines)

## 4. Fix Click Command Redefinitions (F811)

- [x] 4.1 Rename `path_cmd` `rm` function to `path_rm`, preserve CLI name with `name="rm"`
- [x] 4.2 Rename `tag_cmd` `rm` function to `tag_rm`, preserve CLI name with `name="rm"`
- [x] 4.3 Rename `vault_cmd` `add` function to `vault_add`, preserve CLI name with `name="add"`

## 5. Fix Indentation and Blank Line Issues (E127/E128/E305/W292/W391/E741/F841)

- [x] 5.1 Fix E128 continuation under-indentation in `prism-cli/prism_cli/tutor.py` (7 occurrences)
- [x] 5.2 Fix E127 continuation over-indentation in `prism-core/tests/test_manager.py` (5 occurrences)
- [x] 5.3 Fix E127 continuation over-indentation in `prism-cli/tests/test_repl.py`
- [x] 5.4 Fix E305 blank lines after class/function in `prism-cli/prism_cli/main.py`
- [x] 5.5 Fix W292 missing newline at end of `prism-cli/prism_cli/__init__.py`
- [x] 5.6 Fix W391 blank line at end of `prism-cli/prism_cli/tutor.py`
- [x] 5.7 Rename ambiguous variable `l` in `prism-core/tests/test_tutor.py`
- [x] 5.8 Remove unused variable `result` in `prism-cli/tests/test_completions.py`

## 6. Fix Pylint Issues

- [x] 6.1 Add `encoding="utf-8"` to `open()` calls in `prism-cli/prism_cli/tutor.py` (2 occurrences)
- [x] 6.2 Add `encoding="utf-8"` to `open()` call in `prism-cli/prism_cli/commands.py`
- [x] 6.3 Add `check=True` to `subprocess.run` in `prism-cli/prism_cli/tutor.py`
- [x] 6.4 Remove useless `try-except-raise` wrappers in `prism-cli/prism_cli/tutor.py` (4 occurrences)
- [x] 6.5 Fix unused argument `vault` in `prism-cli/prism_cli/tutor.py:_setup_vault`
- [x] 6.6 Fix unused arguments `args` in `prism-cli/prism_cli/repl.py` (2 occurrences)
- [x] 6.7 Replace unnecessary lambdas with direct references in `prism-cli/prism_cli/tutor.py` (3 occurrences)
- [x] 6.8 Fix redefined outer name `vault` in `prism-cli/prism_cli/main.py` (3+ occurrences — renamed group to `vault_group` with `name="vault"`)
- [x] 6.9 Replace broad `except Exception` with specific exceptions in `prism-cli/prism_cli/commands.py` (2 occurrences)
- [x] 6.10 Replace broad `except Exception` in `prism-cli/prism_cli/completions.py` (3 occurrences)
- [x] 6.11 Fix protected member access `_all_nodes` / `_find_children` in `prism-cli/prism_cli/commands.py`
- [x] 6.12 Fix missing argument error at `main.py:749` (E1120 — suppressed false positive for Click entry point)

## 7. Fix Security Issues (Bandit)

- [x] 7.1 Add `# nosec` to `shell=True` in `prism-cli/prism_cli/tutor.py` (controlled lesson-plan input, not user-supplied)
- [x] 7.2 Replace hardcoded `/tmp` with `tempfile` in `prism-core/tests/test_graph.py` (5 occurrences)
- [x] 7.3 Add bandit configuration to skip B101 (assert_used) in test files

## 8. Verify

- [x] 8.1 Run `flake8 --max-line-length=100` on both packages — **zero issues**
- [x] 8.2 Run `pylint --max-line-length=100 --disable=C,R` on both packages — **prism-cli: 10.00/10**; prism-core: non-zero (pre-existing, needs separate change)
- [x] 8.3 Run `bandit -r` on both packages — **no HIGH/MEDIUM issues** (only pre-existing LOW)
- [x] 8.4 Run `pip-audit` on requirements files — **passes** (no known vulnerabilities found)
- [x] 8.5 Run existing pytest tests — **no regressions** (pre-existing failures unchanged: 1 core, 13 CLI)
- [x] 8.6 Run `pyright` on both packages — **prism-core: 0 errors**; prism-cli: import resolution errors fixed via root `pyrightconfig.json` (14 pre-existing type errors remain, out of scope)
