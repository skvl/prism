## 1. Data Model & Validation

- [x] 1.1 Add `path.toml` built-in type schema to `prism/types/builtins.py`
- [x] 1.2 Add `paths: list[str]` field to `NodeMetadata` dataclass
- [x] 1.3 Implement `__post_init__` validation for tags (no spaces, no `/`, UTF-8 letters/digits/`_`/`-`)
- [x] 1.4 Implement `__post_init__` validation for path segments (no `/`, no control chars, UTF-8 including spaces)
- [x] 1.5 Register `path` type as non-creatable via `prism new` in `NodeManager`
- [x] 1.6 Update `NodeMetadata.to_toml()` and `from_toml()` to serialize/deserialize `paths`

## 2. Path Resolution Engine

- [x] 2.1 Create `prism/path/resolver.py` module with `PathResolver` class
- [x] 2.2 Implement `resolve(path_string)` — normalize, split, walk path graph from root resolving each segment name to UUID via `fields.name` and `path-parent` links
- [x] 2.3 Implement `resolve_or_create(path_string)` — same as resolve but creates missing segments (mkdir -p)
- [x] 2.4 Implement `collect_descendants(uuid)` — BFS/DFS to gather all child segment UUIDs
- [x] 2.5 Store root path UUID in vault config (`.metadata/vault.toml` key `path_root_uuid`)
- [x] 2.6 Add cycle detection to prevent circular `path-parent` links

## 3. Vault Lifecycle

- [x] 3.1 Create root `/` path node during `Vault.init()` with `type = "path"` and `fields.name = "/"`
- [x] 3.2 Write root UUID to vault config on init
- [x] 3.3 Load root UUID from vault config on vault open

## 4. CLI: Path Subcommands

- [x] 4.1 Add `prism path` command group to CLI with `create`, `rm`, `tree` subcommands
- [x] 4.2 Implement `prism path create <path>` — resolve_or_create, output leaf UUID
- [x] 4.3 Implement `prism path rm <path>` — resolve, collect descendants, remove from all nodes' `paths`, delete nodes, remove parent link
- [x] 4.4 Add confirmation prompt for `prism path rm` when path has children or referenced nodes
- [x] 4.5 Implement `prism path tree [<path>]` — walk hierarchy from root/subpath, display tree with node counts per leaf

## 5. CLI: Edit Integration

- [x] 5.1 Add `--add-path` / `-a` and `--remove-path` / `-r` options to `prism edit`
- [x] 5.2 Implement `--add-path` — resolve path to UUID, append to node's `paths` if not present
- [x] 5.3 Implement `--remove-path` — resolve path to UUID, remove from node's `paths`
- [x] 5.4 Error handling: non-existent path on `--add-path` shows "Path does not exist"
- [x] 5.5 Update `prism show` to resolve and display path strings from UUIDs

## 6. Query System

- [x] 6.1 Add `path:` token recognition to query parser (`prism/query/parser.py`)
- [x] 6.2 Add `"path"` filter type to query engine (`prism/query/engine.py`) — resolve path, filter nodes whose `paths` contain leaf UUID
- [x] 6.3 Support AND/OR/NOT combination of `path:` with `tag:` and `type:` filters
- [x] 6.4 Validate that path values start with `/` in query, warn and fall back to text search if not

## 7. Graph Integration

- [x] 7.1 Add `--include-paths` / `-p` flag to `prism graph` (default false)
- [x] 7.2 In `GraphExporter`, skip nodes with `type = "path"` unless `--include-paths` is set
- [x] 7.3 When `--include-paths` is set, include `path-parent` edges in graph export

## 8. REPL Tab Completion

- [x] 8.1 Implement `PathResolver.complete(prefix_path)` — walk path graph to parent of last segment, return child names matching prefix
- [x] 8.2 Wire path completion into REPL tab-completion handler for `path:` contexts and `--add-path`/`--remove-path` values
- [x] 8.3 Support partial segment completion (e.g., `/pho` → `/photos`)
