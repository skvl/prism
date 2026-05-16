## 1. Data Model

- [x] 1.1 Add `desc_mtime`, `desc_size`, `desc_sha256` fields to `NodeMetadata` dataclass in `prism/node/metadata.py`
- [x] 1.2 Update `NodeMetadata.to_toml()` to include description fields when present (omitted if empty, same pattern as blob fields)
- [x] 1.3 Update `NodeMetadata.from_toml()` to load description fields

## 2. Storage Layer

- [x] 2.1 Add `description_path()` helper to `NodeMetadata` or `storage.py` (returns `storage_dir / "description.md"`)
- [x] 2.2 Add description read/write/delete functions in `storage.py` (or extend `StorageEngine`)
- [x] 2.3 Implement description SHA-256 hashing and metadata field computation (size, mtime, sha256)
- [x] 2.4 Update `StorageEngine.delete_blob()` (or node deletion logic) to remove `description.md` along with the node directory

## 3. Node Manager

- [x] 3.1 Add `description` parameter to `NodeManager.create_node()` — writes `description.md` and sets tracking fields
- [x] 3.2 Add `set_description()` method to `NodeManager` — create, update, or delete `description.md` based on `--desc` value; update tracking fields and re-extract links
- [x] 3.3 Add description display to `NodeManager.show_node()` — loads and displays description text
- [x] 3.4 Add `get_description()` helper to `NodeManager` — enables description preview in listing output

## 4. CLI

- [x] 4.1 Add `--desc` option to `prism new` command in `prism-cli/prism_cli/main.py`
- [x] 4.2 Add `--desc` option to `prism edit` command in `prism-cli/prism_cli/main.py`
- [x] 4.3 Add `--desc`/`--description` flag to `prism show` command — displays description section
- [x] 4.4 Add `--desc`/`--description` flag to `prism list` command — adds description preview column
- [x] 4.5 Wire description through `commands.create_node()` and `commands.edit_node()` in `prism-cli/prism_cli/commands.py`

## 5. Change Tracking

- [x] 5.1 Add description mtime comparison to `prism status` logic in `prism/tracking.py` — detect when `description.md` mtime differs from stored `desc_mtime`
- [x] 5.2 Add description link re-extraction — when description changes, re-scan for `[[uuid]]` links and update links array
- [x] 5.3 Update `prism status` output to indicate description changes (different label or annotation vs. body changes)

## 6. Search

- [x] 6.1 Include `description.md` in full-text grep search alongside `data.md` in `prism/query/engine.py`

## 7. Verification

- [x] 7.1 Add description SHA-256 verification to `prism verify` — compare `desc_sha256` against recomputed hash of `description.md`

## 8. REPL

- [x] 8.1 Add `--desc` parsing to `Repl._cmd_new()` — pass description to `commands.create_node()`
- [x] 8.2 Add `--desc` parsing to `Repl._cmd_edit()` — pass description to `commands.edit_node()`
- [x] 8.3 Add `--desc` parsing to `Repl._cmd_show()` — display description section in output
- [x] 8.4 Update tab completion in `completions.py` to suggest `--desc` for `new` and `edit` commands

## 9. Tutor

- [x] 9.1 Add a step to Lesson 2 (Your first note) teaching `--desc` — create a note with description, then show it
- [x] 9.2 Add a verification helper for description presence/content in `Tutor._verify_*` methods

## 10. README

- [x] 10.1 Add `prism new note "Title" --desc "Summary"` example to Quick Start section
- [x] 10.2 Add `--desc` flag to relevant entries in the Commands table (`prism new`, `prism edit`, `prism show`)
- [x] 10.3 Add `--desc` to the REPL commands table (`new`, `edit`, `show`)
- [x] 10.4 Add `prism list-nodes --desc` to the Commands table

## 11. Tests

- [x] 11.1 Test: create node with `--desc` — verify `description.md` exists, tracking fields in metadata
- [x] 11.2 Test: edit node to set description on node without one
- [x] 11.3 Test: edit node to update existing description — verify tracking fields updated
- [x] 11.4 Test: edit node to clear description (`--desc ""`) — verify file deleted, fields removed
- [x] 11.5 Test: show node with `--desc` — verify description displayed
- [x] 11.6 Test: list with `--desc` — verify description preview column
- [x] 11.7 Test: delete node with description — verify `description.md` removed
- [x] 11.8 Test: full-text search matches description text
- [x] 11.9 Test: `prism status` detects description changes (mtime mismatch)
- [x] 11.10 Test: `prism verify` checks description SHA-256
- [x] 11.11 Test: description-only edit with `[[uuid]]` links triggers link extraction — verify links appear in metadata
- [x] 11.12 Test: description without `[[uuid]]` links does not add extraneous link entries
- [x] 11.13 Test: REPL `new --desc` creates node with description
- [x] 11.14 Test: REPL `edit --desc` updates description
- [x] 11.15 Test: REPL `show --desc` displays description
- [x] 11.16 Test: tutor step for descriptions passes verification

## 12. Spec Updates (permanent)

- [x] 12.1 Update `openspec/specs/node-management/spec.md` with new/modified requirements
- [x] 12.2 Update `openspec/specs/change-tracking/spec.md` with new/modified requirements
- [x] 12.3 Update `openspec/specs/query-search/spec.md` with new/modified requirements
- [x] 12.4 Update `openspec/specs/blob-storage/spec.md` with new/modified requirements
- [x] 12.5 Update `openspec/specs/repl-interface/spec.md` with new/modified requirements
