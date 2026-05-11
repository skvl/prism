## 1. Project Setup

- [x] 1.1 Initialize Python monorepo structure: `prism-core/` library package and `prism-cli/` CLI package
- [x] 1.2 Configure `pyproject.toml` with dependencies (`tomlkit`, `click`, `click-default-group`)
- [x] 1.3 Set up `pytest`, `ruff` linter, `mypy` type checking
- [x] 1.4 Create `prism-core/prism/__init__.py` with version constant
- [x] 1.5 Create `prism-core/prism/vault/`, `prism-core/prism/node/`, `prism-core/prism/types/`, `prism-core/prism/graph/`, `prism-core/prism/query/` module directories

## 2. Vault Lifecycle

- [x] 2.1 Implement UUID generation (UUIDv7) and UUID partitioning utility (`uuid_to_path(uuid) -> str`)
- [x] 2.2 Implement `Vault` class with `init(path)`, `open(path)`, `validate()` methods
- [x] 2.3 Implement vault directory creation: `.storage/`, `.metadata/`, `.metadata/types/`, `.metadata/index.txt`, `.metadata/vault.toml`
- [x] 2.4 Implement `vault.toml` format: vault UUID, schema version, creation timestamp
- [x] 2.5 Implement vault registry at `~/.config/prism/vaults.toml`: add, list, remove vaults
- [x] 2.6 Implement vault context detection: auto-detect current vault from CWD or `--vault` flag

## 3. Type System

- [x] 3.1 Implement `TypeSchema` dataclass: name, icon, fields (name, type, required flag, default)
- [x] 3.2 Implement `TypeLoader`: scan `.metadata/types/*.toml`, parse and validate schemas
- [x] 3.3 Create built-in type TOML files: `note.toml`, `contact.toml`, `bookmark.toml`, `file.toml`
- [x] 3.4 Implement `FieldValidator`: validate field values against schema (required check, type check)
- [x] 3.5 Support `body_model` in schema: `file(markdown)`, `file(binary)`, `null`

## 4. Blob Storage

- [x] 4.1 Implement `StorageEngine` class: manage `.storage/` directory tree
- [x] 4.2 Implement UUID-partitioned path computation (strip dashes, 4-char directory levels)
- [x] 4.3 Implement `import_blob(source_path, vault) -> Node`: copy file, compute SHA-256, return node UUID
- [x] 4.4 Implement `delete_blob(uuid, vault)`: remove `.storage/<partition>/` directory tree
- [x] 4.5 Implement `read_blob(uuid, vault) -> bytes`: retrieve blob content by UUID
- [x] 4.6 Implement SHA-256 hashing utility with chunked reading for large files

- [x] 5.1 Implement `NodeMetadata` dataclass: uuid, type, title, tags, fields dict, links list, timestamps, blob info
- [x] 5.2 Implement `metadata.toml` read/write with `tomlkit` (preserving comments on future updates)
- [x] 5.3 Implement `create_node(vault, type_name, fields, blob_path?) -> Node`: create metadata.yaml + optional data.*
- [x] 5.4 Implement `edit_node_body(uuid, vault)`: open `data.*` in `$EDITOR`, detect changes via mtime, re-extract links
- [x] 5.5 Implement `edit_node_fields(uuid, vault)`: interactive dialog for structured field editing
- [x] 5.6 Implement `delete_node(uuid, vault)`: remove storage directory, remove from index, handle backlinks warning
- [x] 5.7 Implement `show_node(uuid, vault)`: format and display node details (type-specific display)
- [x] 5.8 Implement `index.txt` management: append on create, remove on delete, rebuild on demand

## 6. Metadata Graph

- [x] 6.1 Implement `[[uuid]]` regex extraction from markdown body text
- [x] 6.2 Implement `[[vault-uuid::target-uuid]]` cross-vault link regex extraction
- [x] 6.3 Implement `links` array management in metadata.yaml: add, remove, update cached title/type
- [x] 6.4 Implement backlinks index: scan all nodes' links arrays per vault, build reverse mapping
- [x] 6.5 Implement `prism backlinks <uuid>`: display all source nodes linking to target
- [x] 6.6 Implement graph export: DOT format (for Graphviz) and JSON format
- [x] 6.7 Implement cross-vault link resolution: check registered vaults for target UUID

- [x] 7.1 Implement query parser: tokenize `tag:`, `type:`, free-text, `AND`/`OR`/`NOT` operators
- [x] 7.2 Implement tag filter: match nodes whose tags array contains the queried tag
- [x] 7.3 Implement type filter: match nodes of the queried type
- [x] 7.4 Implement basic full-text search: grep-based search over `data.*` bodies for note nodes
- [x] 7.5 Implement combined queries: `type:note AND tag:meeting AND budget`
- [x] 7.6 Implement output formatting: table (default), JSON (`--format json`)

- [x] 8.1 Store `blob_mtime`, `blob_size`, `blob_sha256` in metadata.yaml on create and edit
- [x] 8.2 Implement `prism status` command: walk `.storage/`, stat per node, compare mtime/size
- [x] 8.3 Implement new file detection: compare filesystem tree against `.metadata/index.txt`
- [x] 8.4 Implement orphan detection: find index entries with missing `.storage/<uuid>/` directories
- [x] 8.5 Implement link re-extraction prompt on detected changes
- [x] 8.6 Implement `sync_dirty` flag: set `true` on any change, store `updated_at` timestamp

## 9. CLI Integration

- [x] 9.1 Create Click CLI entry point: `prism` with all subcommands
- [x] 9.2 Implement global options: `--vault PATH`, `--verbose`, `--format` (table/json)
- [x] 9.3 Wire `prism init`, `prism vault add/list` to vault lifecycle module
- [x] 9.4 Wire `prism add` to blob storage module
- [x] 9.5 Wire `prism new <type>` to node management module (with type validation)
- [x] 9.6 Wire `prism edit`, `prism rm`, `prism show` to node management module
- [x] 9.7 Wire `prism link`, `prism backlinks`, `prism graph` to metadata graph module
- [x] 9.8 Wire `prism query` to query module
- [x] 9.9 Wire `prism status` to change tracking module
- [x] 9.10 Wire `prism verify` to blob storage module (integrity check)

## 10. Documentation and Packaging

- [x] 10.1 Write README.md with installation, quick start, and command reference
- [x] 10.2 Add type annotations across all modules (mypy strict mode)
- [x] 10.3 Write `pytest` tests for core modules: vault lifecycle, blob storage, type validation, graph, query parser
- [x] 10.4 Configure `pip`/`pipx` installable package
- [x] 10.5 Verify end-to-end workflow: init → add blob → link → query → status → verify
