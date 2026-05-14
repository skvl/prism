## Why

Prism's CLI test coverage is at 35% overall. `main.py` has 72% coverage with 12 failing tests, `repl.py` is at 8% (effectively untested), and `tutor.py` is at 19%. This makes refactoring risky and leaves the user-facing surface area of the tool unverified.

## What Changes

- Fix 12 failing "no vault" tests in `test_main.py` where `detect_vault()` behavior changed
- Add missing tests for `main.py` path subcommands (create, rm, tree) and tag subcommands to reach 85%+ coverage
- Refactor `Repl` class to accept `input_file`/`output_file` streams for testability
- Write parity tests for all REPL commands matching the existing `main.py` test patterns
- Test `Tutor` verification helpers (`_verify_*` methods, `_capture_uuid`, `_resolve_uuid`) as isolated unit tests — no interactive flow testing

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `testing`: Add requirements for CLI command coverage thresholds, REPL input/output stream testability, and Tutor verification helper testing
- `repl-interface`: Update I/O requirement — the Repl SHALL accept configurable input/output streams for testability

## Impact

- `prism-cli/tests/test_main.py` — fix 12 tests, add ~20-30 new tests
- `prism-cli/prism_cli/repl.py` — add `input_stream`/`output_stream` constructor params (backwards compatible)
- `prism-cli/tests/test_repl.py` — new file with ~30-40 tests
- `prism-cli/tests/test_tutor.py` — new file with ~15-20 tests
- `openspec/specs/testing/spec.md` — new requirements for CLI/REPL/Tutor testing
- `openspec/specs/repl-interface/spec.md` — updated I/O stream requirement
