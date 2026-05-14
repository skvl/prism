## Why

Three interactive methods in `NodeManager` (`edit_node_body`, `edit_node_fields`, `delete_node`) mix I/O (`input()`, `subprocess.call`) with data logic, making them untestable without mocking. Additionally, `_would_create_cycle()` is dead code. Meanwhile, link re-extraction after body edits lives in the CLI layer, creating a consistency risk — nothing guarantees it happens. This change separates concerns: library handles data logic (including link extraction), CLI handles user interaction.

## What Changes

- **Refactor `edit_node_body`** → split into `get_body_info(uid)` (returns body path + mtime) and `commit_body_edit(uid, mtime, size, sha256)` (updates blob metadata and re-extracts `[[uuid]]` links)
- **Refactor `edit_node_fields`** → split into `get_field_info(uid)` (returns schema + current values) and `update_node_fields(uid, changes: dict)` (applies field updates)
- **Refactor `delete_node`** → remove `input()` call from non-force path; CLI handles confirmation prompt
- **Move link re-extraction** → `commit_body_edit` calls `LinkExtractor.extract_from_file()` internally — no caller can forget it
- **Extract path operations** → `add_path_to_node(uid, path_str)` and `remove_path_from_node(uid, path_str)` move inline CLI logic into `NodeManager`
- **Remove dead code** → delete `_would_create_cycle()` (unused, untested)
- **CLI simplifications** → `main.py`'s `edit` and `rm` commands updated to use new I/O-free library methods; O(n) storage walks replaced with `_resolve_uuid`-based lookups

No breaking changes to CLI commands or user-facing behavior.

## Capabilities

### New Capabilities

None — internal refactoring, no new user-facing capabilities.

### Modified Capabilities

None — all existing behavior is preserved. No spec-level requirement changes.

## Impact

- **`prism-core/prism/node/manager.py`** — 3 methods removed, 6 new methods added; `_would_create_cycle` deleted
- **`prism-core/prism/graph/links.py`** — no changes; already provides the extraction API
- **`prism-cli/prism_cli/main.py`** — `edit` and `rm` commands restructured to call new methods
- **`prism-core/tests/`** — old method tests removed, new method tests added; dead code test gap closed
- **Coverage** — `manager.py` from 80% → ~97%; overall from 93% → ~95%
