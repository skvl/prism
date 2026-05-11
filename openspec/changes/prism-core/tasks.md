## 1. Project Setup

- [ ] 1.1 Initialize Python monorepo structure: `prism-core/` library package and `prism-cli/` CLI package
- [ ] 1.2 Configure `pyproject.toml` with dependencies (`tomlkit`, `click`, `click-default-group`)
- [ ] 1.3 Set up `pytest`, `ruff` linter, `mypy` type checking
- [ ] 1.4 Create `prism-core/prism/__init__.py` with version constant
- [ ] 1.5 Create `prism-core/prism/vault/`, `prism-core/prism/node/`, `prism-core/prism/types/`, `prism-core/prism/graph/`, `prism-core/prism/query/` module directories

## 2. Vault Lifecycle

- [ ] 2.1 Implement UUID generation (UUIDv7) and UUID partitioning utility (`uuid_to_path(uuid) -> str`)
- [ ] 2.2 Implement `Vault` class with `init(path)`, `open(path)`, `validate()` methods
- [ ] 2.3 Implement vault directory creation: `.storage/`, `.metadata/`, `.metadata/types/`, `.metadata/index.txt`, `.metadata/vault.toml`
- [ ] 2.4 Implement `vault.toml` format: vault UUID, schema version, creation timestamp
- [ ] 2.5 Implement vault registry at `~/.config/prism/vaults.toml`: add, list, remove vaults
- [ ] 2.6 Implement vault context detection: auto-detect current vault from CWD or `--vault` flag

## 3. Type System

- [ ] 3.1 Implement `TypeSchema` dataclass: name, icon, fields (name, type, required flag, default)
- [ ] 3.2 Implement `TypeLoader`: scan `.metadata/types/*.toml`, parse and validate schemas
- [ ] 3.3 Create built-in type TOML files: `note.toml`, `contact.toml`, `bookmark.toml`, `file.toml`
- [ ] 3.4 Implement `FieldValidator`: validate field values against schema (required check, type check)
- [ ] 3.5 Support `body_model` in schema: `file(markdown)`, `file(binary)`, `null`

## 4. Blob Storage

- [ ] 4.1 Implement `StorageEngine` class: manage `.storage/` directory tree
- [ ] 4.2 Implement UUID-partitioned path computation (strip dashes, 4-char directory levels)
- [ ] 4.3 Implement `import_blob(source_path, vault) -> Node`: copy file, compute SHA-256, return node UUID
- [ ] 4.4 Implement `delete_blob(uuid, vault)`: remove `.storage/<partition>/` directory tree
- [ ] 4.5 Implement `read_blob(uuid, vault) -> bytes`: retrieve blob content by UUID
- [ ] 4.6 Implement SHA-256 hashing utility with chunked reading for large files

## 5. Node Management

- [ ] 5.1 Implement `NodeMetadata` dataclass: uuid, type, title, tags, fields dict, links list, timestamps, blob info
- [ ] 5.2 Implement `metadata.toml` read/write with `tomlkit` (preserving comments on future updates)
- [ ] 5.3 Implement `create_node(vault, type_name, fields, blob_path?) -> Node`: create metadata.yaml + optional data.*
- [ ] 5.4 Implement `edit_node_body(uuid, vault)`: open `data.*` in `$EDITOR`, detect changes via mtime, re-extract links
- [ ] 5.5 Implement `edit_node_fields(uuid, vault)`: interactive dialog for structured field editing
- [ ] 5.6 Implement `delete_node(uuid, vault)`: remove storage directory, remove from index, handle backlinks warning
- [ ] 5.7 Implement `show_node(uuid, vault)`: format and display node details (type-specific display)
- [ ] 5.8 Implement `index.txt` management: append on create, remove on delete, rebuild on demand

## 6. Metadata Graph

- [ ] 6.1 Implement `[[uuid]]` regex extraction from markdown body text
- [ ] 6.2 Implement `[[vault-uuid::target-uuid]]` cross-vault link regex extraction
- [ ] 6.3 Implement `links` array management in metadata.yaml: add, remove, update cached title/type
- [ ] 6.4 Implement backlinks index: scan all nodes' links arrays per vault, build reverse mapping
- [ ] 6.5 Implement `prism backlinks <uuid>`: display all source nodes linking to target
- [ ] 6.6 Implement graph export: DOT format (for Graphviz) and JSON format
- [ ] 6.7 Implement cross-vault link resolution: check registered vaults for target UUID

## 7. Query and Search

- [ ] 7.1 Implement query parser: tokenize `tag:`, `type:`, free-text, `AND`/`OR`/`NOT` operators
- [ ] 7.2 Implement tag filter: match nodes whose tags array contains the queried tag
- [ ] 7.3 Implement type filter: match nodes of the queried type
- [ ] 7.4 Implement basic full-text search: grep-based search over `data.*` bodies for note nodes
- [ ] 7.5 Implement combined queries: `type:note AND tag:meeting AND budget`
- [ ] 7.6 Implement output formatting: table (default), JSON (`--format json`)

## 8. Change Tracking

- [ ] 8.1 Store `blob_mtime`, `blob_size`, `blob_sha256` in metadata.yaml on create and edit
- [ ] 8.2 Implement `prism status` command: walk `.storage/`, stat per node, compare mtime/size
- [ ] 8.3 Implement new file detection: compare filesystem tree against `.metadata/index.txt`
- [ ] 8.4 Implement orphan detection: find index entries with missing `.storage/<uuid>/` directories
- [ ] 8.5 Implement link re-extraction prompt on detected changes
- [ ] 8.6 Implement `sync_dirty` flag: set `true` on any change, store `updated_at` timestamp

## 9. CLI Integration

- [ ] 9.1 Create Click CLI entry point: `prism` with all subcommands
- [ ] 9.2 Implement global options: `--vault PATH`, `--verbose`, `--format` (table/json)
- [ ] 9.3 Wire `prism init`, `prism vault add/list` to vault lifecycle module
- [ ] 9.4 Wire `prism add` to blob storage module
- [ ] 9.5 Wire `prism new <type>` to node management module (with type validation)
- [ ] 9.6 Wire `prism edit`, `prism rm`, `prism show` to node management module
- [ ] 9.7 Wire `prism link`, `prism backlinks`, `prism graph` to metadata graph module
- [ ] 9.8 Wire `prism query` to query module
- [ ] 9.9 Wire `prism status` to change tracking module
- [ ] 9.10 Wire `prism verify` to blob storage module (integrity check)

## 10. Documentation and Packaging

- [ ] 10.1 Write README.md with installation, quick start, and command reference
- [ ] 10.2 Add type annotations across all modules (mypy strict mode)
- [ ] 10.3 Write `pytest` tests for core modules: vault lifecycle, blob storage, type validation, graph, query parser
- [ ] 10.4 Configure `pip`/`pipx` installable package
- [ ] 10.5 Verify end-to-end workflow: init → add blob → link → query → status → verify
