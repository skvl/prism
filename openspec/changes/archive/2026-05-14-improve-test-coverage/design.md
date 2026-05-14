## Context

The project follows a no-mock testing pattern: each test class creates a real temp vault via `tempfile.mkdtemp()` + `Vault.init()`, exercises the code against real files, and cleans up. All existing tests follow this pattern. The three areas to cover fit naturally into it.

## Goals / Non-Goals

**Goals:**
- Raise overall coverage from 82% to ~90%
- Cover all 7 public `PathResolver` methods
- Cover `delete_node` non-interactive paths, `show_node` with paths
- Cover `NOT` negation and invalid field comparison in query engine

**Non-Goals:**
- No refactoring of existing code for testability
- No mocking or test doubles
- No testing interactive (`input()`/`$EDITOR`) paths
- No changes to source code

## Decisions

| Decision | Rationale |
|----------|-----------|
| New file `test_path_resolver.py` | PathResolver is a self-contained module; follows pattern of other test files |
| No conftest.py fixtures | Consistent with existing pattern — each class defines its own fixtures |
| Temp vault via `Vault.init()` | The path resolver needs a real vault with `.metadata/vault.toml` for `_load_root_uuid()` |
| `path-parent` links for tree structure | The resolver traverses nodes via `path-parent` link type — tests must create this manually |
| Skip interactive `edit_node_body/fields` tests | These require `$EDITOR` subprocess or `input()` — out of scope per agreement |

## Risks / Trade-offs

- [Low] Path resolver tests require creating multi-node tree structures with correct links. If the link format changes, tests break. Mitigation: tests validate behavior, not internal structure.
- [Low] The 90% target is an estimate — actual coverage depends on branch coverage in untested paths.
