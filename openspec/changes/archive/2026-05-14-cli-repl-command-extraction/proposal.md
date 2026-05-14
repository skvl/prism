## Why

The CLI (`main.py`) and REPL (`repl.py`) contain ~1,600 lines of duplicated command logic — the same business logic written twice with different I/O mechanisms (Click's `click.echo`/`sys.exit` vs the REPL's `self._p`/`return`). The REPL's tab completion system (200+ lines) has zero test coverage and is coupled to `readline`, making it untestable without mocking. This duplication means bugs fixed in one place may not be fixed in the other, and adding new commands requires writing everything twice.

This change eliminates duplication by extracting shared command logic into a single `commands.py` module, extracts completion into pure testable functions in `completions.py`, and adds comprehensive unit tests for both.

## What Changes

- Extract all 16 shared command implementations from `main.py` and `repl.py` into a new `commands.py` module with a uniform `CmdResult` return protocol
- Extract all tab completion logic from `repl.py` into a new `completions.py` module as pure functions with no `readline` dependency
- Rewrite `repl.py` command handlers as thin wrappers that call `commands.*` and render via `self._p`
- Rewrite `main.py` CLI commands as thin wrappers that call `commands.*` and render via `click.echo`
- Move `_write_builtin_types` and `_find_by_hash` (currently duplicated/misplaced) into `commands.py`
- Add `test_commands.py` with unit tests for every `CmdResult` path of every command function
- Add `test_completions.py` with unit tests for every branching combination in completion resolution
- Existing CLI and REPL integration tests remain and continue to pass

## Capabilities

### New Capabilities

- `command-core`: Shared command execution functions used by both CLI and REPL, with a structured result protocol

### Modified Capabilities

- `testing`: New requirements for unit-testing command logic and completion logic directly via pure functions
- `repl-interface`: Completion requirements clarified to reference the pure-function extraction (no behavioral change, but internal contract specified)

## Impact

- `prism-cli/prism_cli/commands.py` — new module (~550 stmts)
- `prism-cli/prism_cli/completions.py` — new module (~200 stmts)
- `prism-cli/prism_cli/main.py` — reduced from ~665 to ~300 stmts
- `prism-cli/prism_cli/repl.py` — reduced from ~731 to ~350 stmts
- `prism-cli/tests/test_commands.py` — new test file
- `prism-cli/tests/test_completions.py` — new test file
- No dependencies added (uses existing `prism-core` APIs)
- No behavioral changes — CLI and REPL output remains identical
