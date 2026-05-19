## Context

Overall test coverage is 76%. Target is 90%+ for each package. Current state:

| Package | Coverage | Statements | Missed |
|---------|----------|-----------|--------|
| prism-core | 96% | 1,344 | 54 |
| prism-cli | 81% | 1,620 | 383 |
| prism-tui | 58% | 1,684 | 713 |
| **Overall** | **76%** | **4,746** | **1,150** |

prism-core already exceeds 90%. Main effort is prism-tui and prism-cli `tutor.py`.

## Design

### Strategy
- Work order: core → cli → tui (easy to hard)
- Within each package, drill from lowest-coverage module to highest
- Core/CLI tests use real temp vaults (existing pattern). TUI tests use `MagicMock`.
- Keep fixtures inline per existing pattern — no conftest.py additions
- Add `[tool.coverage.run]` to each `pyproject.toml` for convenient `--cov` targeting

### prism-core (96% → 90%+)

Already at target. Add ~6-8 tests for remaining uncovered edge cases:
- `storage.py` (84%): hash collision, missing blob, delete non-existent
- `path/resolver.py` (93%): circular paths, path not found edge cases
- `query/engine.py` (87%): empty result, NOT query edge cases
- `query/parser.py` (96%): malformed query strings
- Misc single-line gaps in `manager.py`, `metadata.py`, `tracking.py`, `links.py`

### prism-cli (81% → 90%+)

Target: at most ~162 missed statements (down from 383).

**tutor.py (46%, 196 missed)** — biggest gap. The `tutor` module has ~23 verify functions (`verify_vault_init`, `verify_node_count`, etc.) plus lesson plan builder and execute helpers. Each verify function follows a simple pattern: accept vault state + args, run assertion. Write ~20 unit tests covering all verify functions, the lesson plan builder, and the execute-command wrapper.

**completions.py (70%, 34 missed)** — test remaining completion edge cases (flag completions, type names, degraded mode paths).

**repl.py (80%, 108 missed)** — test error paths, edge cases in each REPL command (empty input, invalid UUID, missing args).

**main.py (82%, 107 missed)** — test remaining CLI command paths (error handling, edge case argument combinations, TUI bridge).

**commands.py (91%, 37 missed)** — minor gap-filling.

### prism-tui (58% → 90%+)

Target: at most ~168 missed statements (down from 713). This is the largest effort.

Use `MagicMock` to simulate Textual app state, widgets, and messages — no real vaults. Each module gets a dedicated test file following existing TUI test conventions:

**command_mode.py (30%, 186 missed)** — test command parsing, dispatch routing, mode transitions (`enter_command_mode`, `exit_command_mode`, `on_input_submitted`), error handling for unknown commands, and tab completion integration.

**browser.py (41%, 133 missed)** — test path tree population, node list filtering, preview rendering, modal navigation (j/k/h/l/gg/G), tag/type filter overlay, external editor launch, cross-tab navigation.

**tag_cloud.py (42%, 78 missed)** — test tag-to-widget mapping, single and multi-tag selection, co-occurrence highlighting, result list population, clear selection.

**query_builder.py (55%, 56 missed)** — test form-to-AST conversion, type picker, tag selector, text search, AND/OR/NOT toggle, auto-search, result display, history.

**app.py (60%, 54 missed)** — test app lifecycle, vault connection flow, key bindings, tab switching, wizard mounting, notifications.

**command_bar.py (55%, 25 missed)** — test action label updates, F-key/number-key dispatch, context-sensitive labels.

**graph.py (69%, 77 missed)** — test layout algorithm (pure function, no mocking needed), node/edge rendering, pan/zoom, dense graph fallback, type filter, cross-tab navigation.

## Approach

Approach 1: Zone defense — triage by package. Work through packages in order (core, cli, tui), tackling lowest-coverage module first within each. Pure unit tests with mocking for TUI, real temp vaults for core/cli. No infrastructure changes.

## Success criteria

- All three packages report 90%+ line coverage
- CI runs `pytest --cov` across all packages
- No regression in existing tests
- Existing test patterns/styles preserved within each package
