# Prism — Architecture

## ASCII Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI (prism-cli)                      │
│  ┌──────────┬────────────┬─────────┬──────────┬──────────┐  │
│  │  main.py │ commands.py │ repl.py │ tutor.py │completions│  │
│  └────┬─────┴─────┬──────┴────┬────┴────┬─────┴─────┬────┘  │
│       │           │           │         │           │        │
└───────┼───────────┼───────────┼─────────┼───────────┼────────┘
        │           │           │         │           │
        ▼           ▼           ▼         ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Library (prism-core)                     │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │  Vault   │───▶│  Types   │───▶│  Node    │               │
│  │ (vault/) │    │ (types/) │    │ (node/)  │               │
│  └──────────┘    └──────────┘    └────┬─────┘               │
│                                       │                      │
│         ┌─────────────────────────────┼──────────────┐       │
│         │                             │              │       │
│         ▼                             ▼              ▼       │
│  ┌──────────┐                 ┌──────────┐   ┌──────────┐    │
│  │  Graph   │                 │  Query   │   │  Path    │    │
│  │ (graph/) │                 │ (query/) │   │ (path/)  │    │
│  └──────────┘                 └──────────┘   └──────────┘    │
│                                                              │
│  ┌────────────┐                                              │
│  │  Tracking  │ (tracking.py)                                │
│  └────────────┘                                              │
└─────────────────────────────────────────────────────────────┘
        │           │           │
        ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer (on-disk)                   │
│                                                              │
│  ~/my-vault/                                                 │
│  ├── .metadata/          # Vault config, type defs, index    │
│  │   ├── vault.toml      # Vault UUID, schema version        │
│  │   ├── types/          # .toml type definition files       │
│  │   └── index.txt       # UUID index for fast listing       │
│  ├── .storage/           # Content-addressed blob store      │
│  │   └── ab/cd/ef/...   # UUID-partitioned directories      │
│  │       ├── data.md     # Blob body (markdown/binary)       │
│  │       └── metadata.toml # Node type, tags, links, fields  │
│  └── ...                  # User files (imported or external) │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### File Import

```
source file ──▶ sha256_file() ──▶ compute_storage_path(uuid)
                                      │
                                      ▼
                              .storage/ab/cd/ef/ghij/  dir created
                                      │
                                      ▼
                              data.ext  (blob copied in)
                                      │
                                      ▼
                              metadata.toml  (written)
```

### Node Creation

```
prism new note "title" ──▶ NodeManager.create_node()
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              TypeLoader   FieldValidator  generate_uuid()
              loads schema  validates      creates UUID
                    │       fields              │
                    └───────────┬───────────────┘
                                ▼
                        NodeMetadata created
                        StorageEngine stores
                        Index updated
```

### Graph & Links

```
Note body with [[uuid]] links
        │
        ▼
LinkExtractor.extract_links()
        │
        ▼
Links stored in metadata.toml
        │
        ▼
BacklinkIndex.build()  ◀── scans all metadata
        │
        ▼
GraphExporter.export_dot/json()
```

### Query Execution

```
query string "tag:ideas AND type:note"
        │
        ▼
QueryParser.parse() ──▶ QueryAST
        │
        ▼
QueryEngine.execute(ast)
        │
        ▼
Load all nodes ──▶ Filter by tags
               ──▶ Filter by type
               ──▶ Filter by text match
               ──▶ Combine with AND/OR/NOT
```

## Key Design Decisions

### 1. Content Addressing

Blobs are stored by SHA-256 hash, not by original filename. This provides:
- **Deduplication**: same file content = one blob, multiple references
- **Integrity verification**: `prism verify` recomputes hash and compares
- **Immutable storage**: blob content never changes (edits create new entries)

The `StorageEngine` handles blob lifecycle: `import_blob()`, `delete_blob()`, `read_blob()`, `verify_integrity()`.

### 2. TOML Metadata

All metadata is stored as TOML files via `tomlkit`:
- `vault.toml` — vault identity (UUID, schema version, creation date)
- `type/*.toml` — type definitions (fields, body model, icon)
- `.storage/*/metadata.toml` — per-node metadata (type, tags, links, paths)

TOML was chosen over YAML/JSON for:
- **Human readability**: comments, clean formatting
- **Git-friendly**: diffs cleanly
- **Strong typing**: `tomlkit` preserves types and formatting

### 3. UUID Partitioning

Storage paths use the UUID hex digest split into directory levels:

```
UUID: 550e8400-e29b-41d4-a716-446655440000
Path: .storage/550e/8400/e29b/41d4-a716-446655440000/
```

This prevents any single directory from holding too many entries — critical for filesystem performance at scale. The top-level dirs act as a natural hash bucket.

### 4. Single-User, Single-Threaded

The project assumes a single concurrent user:
- No file locks, no mutexes, no transaction log
- No server process, no database daemon
- No sync, no conflict resolution
- Simplicity and reliability over concurrency

### 5. Local-First

Everything lives on the local filesystem:
- No cloud dependency, no API keys, no network required
- Vault is a plain directory — backup with `rsync`, `tar`, Dropbox
- No vendor lock-in — data is just files

## Module Interaction Patterns

### Vault → Types → Node

The most common interaction chain:
1. `Vault` provides the vault path and metadata
2. `TypeLoader` loads the node's type schema from `.metadata/types/`
3. `NodeManager` orchestrates node creation: validates fields via `FieldValidator`, stores blob via `StorageEngine`, saves metadata via `NodeMetadata`

### Node → Graph

After nodes exist:
1. `LinkExtractor` parses note bodies for `[[uuid]]` references
2. `BacklinkIndex` scans all metadata to build reverse-link map
3. `GraphExporter` renders the full graph in DOT or JSON format

### Query Engine

The query layer is independent of the storage layer:
1. `QueryParser` tokenizes query strings into an AST (no I/O)
2. `QueryEngine` loads all node metadata, then performs in-memory filtering against the AST
3. Results are returned as `NodeMetadata` lists for display or export

### Change Tracking

`ChangeTracker` sits outside the normal CRUD path:
- `status()` compares stored mtime against filesystem mtime for each node
- `mark_dirty()` forces re-extraction of links on the next status call
- `re_extract_links()` re-runs `LinkExtractor` on a specific node
