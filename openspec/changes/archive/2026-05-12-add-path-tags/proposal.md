## Why

The current tag system is flat — tags are simple strings with no hierarchy, no browsing, and no structure. As the vault grows, this makes organization harder. Path-like tags add a browsable virtual filesystem to the tag system, letting users organize nodes hierarchically (e.g., `/photos/2026/02/vacations`) while keeping flat tags for ad-hoc classification. This is a natural extension of the PKM concept: nodes benefit from both flat tagging and hierarchical categorization.

## What Changes

- **New `path` type** — a node type representing a path segment in the virtual filesystem
- **New `paths` field on `NodeMetadata`** — a `list[str]` of path segment UUIDs, first-class alongside `tags`
- **Root `/` path node** — auto-created on `prism init`
- **`mkdir -p` semantics** — creating `/a/b/c` auto-creates parent segments `/a` and `/a/b`
- **`prism path` subcommand group** — `prism path create`, `prism path rm`, `prism path tree`
- **`prism edit --add-path / --remove-path /`** — add/remove path associations on existing nodes
- **Per-segment TAB completion** in REPL for path-like tags
- **`path:` query prefix** — `path:/photos/2026/02/vacations` matches nodes filed under exact path
- **`path: + tag: AND/OR/NOT` combinable** — e.g., `path:/photos AND tag:vacation`
- **Path hierarchy stored as graph links** — parent-child edges use `[[uuid]]` with tag `path-parent`
- **Cascade delete** — removing a path node removes it from all nodes' `paths` lists and deletes children
- **Multiple paths per node** — a node can be filed under several paths
- **Inline validation** — `NodeMetadata.__post_init__` validates tag and path segment character rules
- **Tag character rules** — simple tags: UTF-8 letters, digits, `_`, `-` (no spaces, no `/`)
- **Path segment character rules** — UTF-8 letters, digits, spaces, `_`, `-` (no `/`, no control chars)
- **Graph export excludes path nodes by default**

## Capabilities

### New Capabilities
- `path-tags`: Hierarchical path-based tagging with virtual filesystem semantics — path nodes as graph objects, `mkdir -p` creation, `tree` browsing, `prism path` subcommand group

### Modified Capabilities
- `type-system`: Add the `path` type definition
- `metadata-graph`: Path hierarchy stored as `path-parent` links in the graph; graph export excludes path nodes by default
- `query-search`: Add `path:` query prefix with exact-match semantics, combinable with `tag:` and other filters via AND/OR/NOT
- `node-management`: `paths` field on NodeMetadata, `prism edit --add-path/--remove-path`
- `repl-interface`: Per-segment TAB completion for path-like tags
- `vault-lifecycle`: Root `/` path node created on vault init

## Impact

- **prism-core**: `prism/node/metadata.py` — add `paths` field, `__post_init__` validation; new `prism/path/` module for path operations; `prism/query/` — add `path:` filter to parser and engine; `prism/graph/` — add path node filtering to export
- **prism-cli**: `prism_cli/main.py` — add `prism path` command group, `--add-path`/`--remove-path` to edit, TAB completion changes
- **Storage**: Path segments stored as regular nodes in `.storage/`; no new storage mechanism needed
- **Index**: No persistent index initially (noted as future optimization)
