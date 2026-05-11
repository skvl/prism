## Why

Existing PKM tools (Obsidian, etc.) are note-centric — they treat markdown as the primary citizen and other file types as second-class attachments. There is no graph-based personal knowledge manager that treats all content (notes, contacts, bookmarks, articles, arbitrary files) as equal nodes in a unified metadata graph, with content-addressed blob storage and type schemas defined as plain YAML files.

Prism fills this gap: a local-first, single-user PKM built on a content-addressed blob store with a typed node graph, designed from day one for P2P sync and encrypted backup.

## What Changes

- **Monorepo initialization** — multi-project workspace with `prism-core` (Python library), `prism-cli` (CLI tool), and future interface projects (TUI, GUI, WebUI)
- **Vault system** — initialize and manage vaults with `.metadata/` and `.storage/` structure
- **Blob storage** — content-addressed import of any file type into `.storage/<uuid-partitioned>/data.*`
- **Metadata engine** — per-node YAML metadata files with type, tags, links, fields, and change tracking
- **Type system** — user-extensible type schemas in `.metadata/types/*.yaml` (note, contact, bookmark, file as built-ins)
- **Node graph** — `[[uuid]]` links with backlinks, cross-vault `[[vault-uuid::target-uuid]]` links (lazy resolution)
- **Change tracking** — mtime-based detection of blob edits, SHA-256 content hashing for sync readiness
- **CLI** — full command set: `init`, `add`, `new`, `edit`, `link`, `tag`, `show`, `graph`, `query`, `status`
- **Sync/Backup** — explicitly excluded from MVP, designed for later addition via separate Rust daemon

## Capabilities

### New Capabilities

- `vault-lifecycle`: Initialize, open, validate, and repair vaults. Vault-level identity (UUID, keypair placeholder for future sync). Registration of multiple vaults for unified graph view.
- `node-management`: CRUD for typed nodes. Create notes, contacts, bookmarks, and file references. Edit body content and structured fields. Delete with orphan detection.
- `blob-storage`: Content-addressed import of arbitrary files into partitioned `.storage/` tree. Original extension preserved. SHA-256 hashing for integrity and future sync.
- `type-system`: Schema definitions in `.metadata/types/*.yaml`. Built-in types (note, contact, bookmark, file). Field validation, required fields, type-specific display.
- `metadata-graph`: `[[uuid]]` link parsing in note bodies. Explicit link creation between any node types. Backlink auto-tracking. Graph export (DOT/JSON). Cross-vault lazy link resolution.
- `query-search`: Tag-based filtering (`tag:work AND type:note`). Full-text search over note bodies. Type-filtered queries. Combined tag + type + text queries.
- `change-tracking`: Per-node mtime comparison for blob change detection. SHA-256 content hash stored in metadata.yaml. Dirty flagging for future sync. `status` command showing changed/new/orphaned nodes.

### Modified Capabilities

None — this is a greenfield project.

## Impact

- **Repository**: New monorepo at `file_manager/` with Python core + CLI
- **Language**: Python 3.12+ with type hints
- **Dependencies**: `tomlkit` for metadata read/write, `tomllib` (stdlib ≥3.11) for read-only, `click` for CLI
- **Future**: Sync daemon in Rust using `p2panda` — communicates via filesystem (dirty flags in metadata.yaml)
- **Distribution**: `pip install prism-cli` or standalone via `pipx`
