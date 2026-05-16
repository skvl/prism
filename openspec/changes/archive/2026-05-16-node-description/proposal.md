## Why

Nodes currently lack a free-form summary field. Users must encode descriptions in titles (too short), tags (wrong abstraction), or body content (blurs summary vs. full content). A dedicated description field — stored as a separate Markdown file to avoid TOML escaping issues — gives every node an optional, editable summary that's searchable and displayable independently of the body.

## What Changes

- Add optional `description.md` file alongside `metadata.toml` and `data.*` in each node's storage directory
- Track description file metadata (sha256, mtime, size) in `metadata.toml` for change detection
- Add `--desc` flag to `prism new` and `prism edit` commands for setting/updating description
- Add `--desc` / `--description` flag to `prism show` and `prism list` to display descriptions in output
- Description content is scanned for `[[uuid]]` links (same as body text), and those links populate the node's `links` array
- Include description content in full-text search results
- Track `description.md` changes in `prism status` and dirty-flag machinery
- Deleting a node removes `description.md` along with the rest of the node directory
- REPL `new`, `edit`, and `show` commands support `--desc` flag
- Tutor adds a step teaching node descriptions in an existing lesson
- README updated with description examples

## Capabilities

### New Capabilities

- `node-management`: extend node CRUD to include descriptions — create with `--desc`, edit with `--desc`, show and list with `--show-desc`, delete removes `description.md`

### Modified Capabilities

- `change-tracking`: add `description.md` to per-node mtime tracking, status change detection, and re-indexing
- `query-search`: include description text in full-text search (alongside body text)
- `blob-storage`: description.md follows the same SHA-256 integrity verification pattern as blobs
- `repl-interface`: REPL `new`, `edit`, and `show` commands accept `--desc` flag

## Impact

- `prism-core/prism/node/metadata.py` — `NodeMetadata` gains `desc_sha256`, `desc_mtime`, `desc_size` fields
- `prism-core/prism/node/manager.py` — `create_node()` and `edit_node()` handle `description` parameter; read/write `description.md`
- `prism-core/prism/node/storage.py` — optional `DescriptionEngine` or extended `StorageEngine` for description file ops
- `prism-core/prism/tracking.py` — add description change detection alongside blob change detection
- `prism-core/prism/query/engine.py` — full-text search reads `description.md` in addition to `data.md`
- `prism-cli/prism_cli/main.py` — `--desc` flag on `new` and `edit` commands
- `prism-cli/prism_cli/commands.py` — wire description through to node manager
- `prism-cli/prism_cli/repl.py` — `_cmd_new`, `_cmd_edit`, `_cmd_show` handle `--desc`
- `prism-cli/prism_cli/completions.py` — `--desc` flag completion for relevant commands
- `prism-cli/prism_cli/tutor.py` — new step/lesson covering descriptions
- `README.md` — add description examples to Quick Start, Commands table, and REPL section
- Test files: `test_metadata.py`, `test_manager.py`, `test_storage.py`, `test_query.py`, `test_repl.py`, `test_tutor.py` — new test cases for description workflows
