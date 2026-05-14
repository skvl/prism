## Context

The CLI (`main.py`) and REPL (`repl.py`) each implement the same 16 command handlers independently, sharing ~550 lines of duplicated business logic. The REPL's tab completion system is 200+ lines of branching logic coupled to `readline` with zero test coverage. Adding a new CLI command currently requires writing it twice.

## Goals / Non-Goals

**Goals:**
- Extract all shared command logic into `commands.py` with a uniform `CmdResult` return protocol
- Extract completion logic into `completions.py` as pure functions (no `readline` dependency)
- Rewrite `main.py` and `repl.py` as thin I/O wrappers around `commands.*`
- Achieve 100% coverage of completion logic and ~95%+ coverage of command logic
- All existing 216 tests continue to pass unchanged

**Non-Goals:**
- No behavioral changes to CLI or REPL output
- No changes to `prism-core` library
- No new REPL features or UX changes
- No changes to `tutor.py` (separate concern)

## Decisions

### 1. CmdResult protocol over exceptions

Command functions return `CmdResult(ok, error, code, data)` instead of raising exceptions. This gives callers a uniform protocol for success/failure, avoids the CLI's `sys.exit` vs REPL's `return` divergence, and makes testing straightforward (assert on `result.ok`/`result.error`).

Alternatives considered:
- **Raise exceptions**: Cleaner internally but forces both callers to handle the same exception types differently (CLI exits, REPL returns)
- **Return raw values + raise on error**: Inconsistent protocol, harder to test

### 2. Pure function extraction for completions

`resolve_completions(parts, text, vault, aliases)` is a pure function with no I/O. Callers supply the already-split line buffer. The sub-helpers (`complete_uuid`, `complete_tag`, etc.) are also pure functions taking `(vault, text)`. The REPL's `_get_completions` becomes a one-liner that reads the buffer and delegates.

This eliminates `readline` dependency from testable code. The 200+ line completion system becomes fully testable via simple function calls with no mocking.

### 3. All-at-once extraction

All 16 command handlers are extracted in a single change rather than incrementally. Rationale:
- Avoids a long tail of partial extraction PRs
- Eliminates ambiguity about which handlers are "done" vs "still duplicated"
- The extraction pattern is mechanical and repetitive — batch extraction is efficient
- All tests pass at each step (the wrappers call through to the same logic)

### 4. Separate `completions.py` module

Completion functions live in their own module rather than as module-level functions in `repl.py`. This gives clean import boundaries — `test_completions.py` imports only what it needs without pulling in the `Repl` class or `readline`.

### 5. `_write_builtin_types` and `_find_by_hash` migrate to `commands.py`

`_write_builtin_types` is copy-pasted identically in both `main.py` and `repl.py`. `_find_by_hash` lives in `main.py` but the REPL has inline equivalent logic. Both move to `commands.py` as shared helpers.

## Risks / Trade-offs

- **[Risk] Large single change** — ~1,600 lines moved across 4 files. Code review will be dense.
  **Mitigation**: The extraction is mechanical (copy → wrap → delete). Pattern is uniform across all commands.
- **[Risk] Behavioral drift** — Subtle differences between CLI and REPL implementations could be accidentally unified where they should differ.
  **Mitigation**: Compare outputs of both wrappers against same `CmdResult`. Existing integration tests catch differences.
- **[Trade-off] More files** — 2 new source files + 2 new test files. Slightly more project surface area.
  **Value**: Each file is smaller, more focused, and individually testable.
- **[Risk] Completion extraction misses edge cases** — `_get_completions` has complex branching that may have untested edge states.
  **Mitigation**: The pure function extraction makes every branch testable. The test file enumerates all branching combinations.
