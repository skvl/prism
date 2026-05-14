## Why

Tags in Prism are stored as universal metadata on nodes and are queryable, but there is no way to manage them once a node is created — no add, remove, list, or rename operations exist. Users can only set tags at creation time via `prism new --tag`. This limits tag-based workflows and makes tag maintenance tedious.

## What Changes

- New `prism tag` command group with four subcommands: `add`, `rm`, `list`, `rename`
- Tags become universally manageable post-creation on any node type
- New `NodeManager` methods: `add_tag()`, `remove_tag()`, `list_tags()`, `rename_tag()`
- REPL gains `tag` subcommand with tab completion
- Tutor adds Lesson 7 covering tag management
- README updated with `prism tag` command docs
- No breaking changes — existing `--tag` flag on `prism new` continues working identically

## Capabilities

### New Capabilities

- `tag-management`: CLI and library support for adding, removing, listing, and renaming tags on existing nodes

### Modified Capabilities

<!-- No existing specs are changing; this is an entirely new capability -->

## Impact

- `prism-core/prism/node/manager.py` — 4 new methods
- `prism-cli/prism_cli/main.py` — new `tag` Click command group
- `prism-cli/prism_cli/repl.py` — `_cmd_tag` dispatch, completion, help
- `prism-cli/prism_cli/tutor.py` — new Lesson 7, TOTAL_LESSONS to 8
- `README.md` — new command table entries
