## Context

Current test coverage for prism-cli is 35% overall (1144 of 1748 statements missed):

| Module    | Coverage | Lines Missed |
|-----------|----------|--------------|
| main.py   | 72%      | 186          |
| repl.py   | 8%       | 657          |
| tutor.py  | 19%      | 301          |

Additionally, 12 tests in `test_main.py` are failing because `detect_vault()` behavior changed — tests expect "No vault found" but CWD now resolves to a vault.

The three source modules serve distinct user-facing roles and need different testing approaches.

## Goals / Non-Goals

**Goals:**
- Fix all 12 failing "no vault" tests in `test_main.py`
- Raise `main.py` coverage from 72% to 85%+ by adding tests for untested commands (path subcommands, tag subcommands, edge cases)
- Refactor `Repl` to accept configurable input/output streams for testability
- Write parity tests matching the existing `main.py` test pattern for all REPL commands
- Test `Tutor` verification helpers (`_verify_*`, `_capture_uuid`, `_resolve_uuid`, `_sha256`) as isolated unit tests

**Non-Goals:**
- No Tutor integration tests (interactive flow with subprocess + user prompts)
- No tab completion tests (heavily tied to readline)
- No performance or stress tests
- No changes to Tutor's `_run_step` or `run` methods

## Decisions

### 1. REPL stream injection via constructor params

**Decision**: Add `input_stream` and `output_stream` parameters to `Repl.__init__` defaulting to `sys.stdin` and `sys.stdout`. Replace all `print()` and `input()` calls in `Repl` methods with `self._output.write()` / `self._output.flush()` and `self._input.readline()`.

**Rationale**:
- Fully backwards compatible — default values match current behavior
- Test can inject `io.StringIO` objects to capture output and simulate input
- Minimal change surface (find/replace pattern across ~30 print/input calls)
- Avoids mocking the `builtins` module which is fragile

**Alternatives considered**:
- *Mock `builtins.print`/`builtins.input`*: Works but is fragile, doesn't compose well, and doesn't test the actual I/O path
- *Click's CliRunner for REPL*: The REPL doesn't use Click, so this isn't applicable

### 2. REPL test structure mirrors main.py

**Decision**: Place REPL tests in `tests/test_repl.py` using the same temp vault/vault_dir fixture pattern from `test_main.py`. Each command gets its own test class (`TestReplNewCommand`, `TestReplShowCommand`, etc.) with identical scenarios to the CLI tests but injecting StringIO streams.

**Rationale**: Consistency. Developers familiar with one test file will immediately understand the other. The scenarios are the same — only the invocation mechanism differs.

### 3. Tutor test scope: verification helpers only

**Decision**: Test only the `Tutor._verify_*` methods (15 methods), `_capture_uuid`, `_resolve_uuid`, and `_sha256` as isolated unit tests. These are pure logic methods that take a `Vault` or strings and return `bool`/`str`.

**Rationale**:
- These methods contain the actual correctness logic for the tutorial
- They are testable without interactive scaffolding
- The `_run_step` and `run` methods involve subprocess, input prompts, and retry loops — testing them would require significant restructuring for little gain

### 4. Fixing "no vault" tests

**Decision**: The 12 failing tests pass when run from outside a vault directory. The fix: wrap each "no vault" test body in `monkeypatch.chdir(tempfile.mkdtemp())` so the CWD is guaranteed to not be inside a vault. This is more robust than mocking `detect_vault`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| REPL uses `readline` for completion — `input_stream` won't trigger readline features | Tab completion tests are excluded from scope. Standard command dispatch is still testable via StringIO. |
| REPL `_run_step` recursion could hang if a step keeps failing | Not testing `_run_step` directly — only the verification helpers. |
| Some `_verify_*` methods call `resolve_uuid` which walks the filesystem | Temp vault fixtures (same pattern as `test_main.py`) provide a controlled environment. |
| Stream swap in REPL misses a `print()` call | Systematic grep for all `print(` and `input(` calls. Each match becomes a tracked line. |
