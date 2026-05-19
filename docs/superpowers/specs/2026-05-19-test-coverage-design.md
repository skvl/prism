# Test Coverage — Phase 2 Design

## Goal

Bring `prism-cli` and `prism-tui` to ≥95% test coverage. `prism-core` is already at 98% and needs no work. Add CI coverage gates and update AGENTS.md to require ≥95% for all current and future subprojects.

## Current State

| Subproject | Coverage | Status |
|---|---|---|
| prism-core | 98% | ✅ done |
| prism-cli | 90% | ⚠️ tutor.py (52%), repl.py (86%) |
| prism-tui | 82% | ❌ multiple files below 80% |

## Work Order (Phase 1 → Phase 3)

### Phase 1 — Deep gaps (<60%)

1. `prism_tui/tabs/tag_cloud.py` (43%) — 77 uncovered stmts
2. `prism_tui/tabs/browser.py` (51%) — 110 uncovered stmts
3. `prism_cli/tutor.py` (52%) — 173 uncovered stmts

### Phase 2 — Medium gaps (60–80%)

4. `prism_tui/command_bar.py` (65%) — 19 uncovered stmts
5. `prism_tui/app.py` (69%) — 42 uncovered stmts
6. `prism_tui/messages.py` (71%) — 2 uncovered stmts
7. `prism_tui/tabs/query_builder.py` (73%) — 34 uncovered stmts
8. `prism_tui/tabs/graph.py` (78%) — 53 uncovered stmts

### Phase 3 — Home stretch (>80%)

9. `prism_cli/repl.py` (86%) — 80 uncovered stmts
10. `prism_tui/startup_screen.py` (89%) — 7 uncovered stmts
11. `prism_tui/widgets/completions.py` (88%) — 3 uncovered stmts
12. `prism_tui/__main__.py` (0%) — 3 uncovered stmts

## Testing Approach

### TUI files (Textual)

- Use `MagicMock` for `_vault`, `_manager`, `query_one`, `notify` (same pattern as existing test_app.py, test_tag_cloud.py)
- Test logic methods directly without full Textual app lifecycle
- For rendering logic: mock DOM queries with fake widgets
- No pytest-textual dependency needed

### tutor.py

- Real temp vaults via `Vault.init()` as fixture (same pattern as existing test_tutor.py)
- Each `_verify_*` method tested with vault in known state
- Lesson step coverage: set up vault to match step preconditions, verify passes

### repl.py

- Real temp vaults + `StringIO` I/O streams (same pattern as existing test_repl.py)
- Edge cases: degraded mode commands, empty/whitespace input, corrupted vault
- Feed command sequences through `run_repl()` helper

## CI Gates

Add `[tool.coverage.report] fail_under = 95` to each `pyproject.toml`.

The pytest invocation already uses `--cov` — adding `--cov-fail-under=95` on CI will enforce the threshold.

## AGENTS.md Updates

Root `AGENTS.md`: add a "Code Quality" section requiring ≥95% coverage for all subprojects, referencing the coverage config in each pyproject.toml.

Subpackage AGENTS.md: add a one-liner with the coverage target for that package.
