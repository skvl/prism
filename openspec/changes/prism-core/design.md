## Context

Prism is a local-first, single-user PKM (personal knowledge manager) built on a content-addressed blob store with a typed node graph. The system treats all content — notes, contacts, bookmarks, articles, arbitrary files — as equal nodes in a unified graph, with metadata stored as YAML sidecars and file content stored in a partitioned UUID-based blob store.

This document covers the core library (`prism-core`) and CLI interface (`prism-cli`). Sync and backup are explicitly deferred to a future Rust daemon.

## Goals / Non-Goals

**Goals:**
- Content-addressed blob storage: every file imported into Prism is stored as `data.*` under a UUID-partitioned path in `.storage/`
- Typed node graph: nodes have types defined by YAML schema files, with `[[uuid]]` links forming a directed graph
- Metadata-only nodes: contacts, bookmarks, and structured types live purely as `metadata.yaml` with no companion file
- TOML-first metadata: all node metadata is stored in human-readable, diffable, mergeable TOML files (predictable format for future three-way merge during sync)
- Vault portability: a vault is a directory containing `.storage/` + `.metadata/`, fully self-contained and movable
- Graceful cross-vault linking: `[[vault-uuid::target-uuid]]` resolves lazily, cached in metadata.yaml
- CLI as power tool: full command set with structured output for scripting
- Change tracking via mtime: per-node filesystem mtime compared with stored value in metadata.yaml

**Non-Goals:**
- Multi-user collaboration (single-user only)
- Real-time sync or P2P networking (deferred to post-MVP Rust daemon)
- Encrypted backup to WebDAV or similar (deferred)
- FUSE virtual filesystem (deferred, optional)
- GUI/TUI/WebUI interfaces (separate future projects in monorepo)
- Plugin system or scripting (deferred)
- Full-text search engine integration (basic grep-based search initially)

## Decisions

### Decision: Blob store model (`.storage/<uuid-partitioned>/data.EXT`)

**Chosen** over path-based organization (e.g., `notes/meeting.md`).

- All files are stored by UUID-partitioned path, eliminating filesystem path as identity
- Original extension preserved as `data.EXT` for editor compatibility
- Solves the long filename problem — the user never sees or navigates the blob store directly
- UUID partitioning (`a1b2/c3d4/e5f6/a7b8c9d0e1f2/`) prevents directory bloat
- Trade-off: user cannot browse vault with a regular file manager. Mitigated by CLI/TUI/GUI interfaces as the primary interaction surface.

### Decision: Metadata-only nodes (no human file for contacts, bookmarks, events)

**Chosen** over generating companion `.md` files.

- Contacts, bookmarks, and structured types exist only as `.storage/<uuid>/metadata.yaml`
- The YAML IS the source of truth — no second file to keep in sync
- Reduces filesystem operations (one file per node regardless of type)
- Trade-off: cannot grep for contacts easily. Mitigated by `prism query` and future TUI/GUI.

### Decision: Source of truth is dual (TOML metadata + blob files)

**Chosen** over a central database.

- `.metadata/index.txt` maps paths → UUIDs (for file tracking)
- `.metadata/types/*.toml` define type schemas
- `.storage/<uuid>/metadata.toml` per node (links, tags, fields, timestamps)
- `.storage/<uuid>/data.EXT` per blob node
- TOML chosen over YAML for merge predictability. When the future sync daemon performs three-way merges of metadata files, TOML's strict format eliminates semantic ambiguity that YAML's flexible parsing would introduce.
- Trade-off: TOML's `[[array]]` syntax is more verbose for deeply nested structures than YAML. Acceptable since schemas are written once and rarely modified.

### Decision: `[[uuid]]` links with lazy resolution

**Chosen** over path-based or alias-based linking.

- Canonical form: `[[a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d]]`
- Cross-vault: `[[vault-uuid::target-uuid]]`
- Each metadata.yaml caches `title` and `type` of linked nodes for display without resolution
- Unresolvable links shown as gray/unknown — valid state, not an error
- Trade-off: UUIDs are ugly in raw markup. Mitigated by aliases (`prism alias name uuid`) with pre-processing on write.

### Decision: Change tracking via per-node mtime

**Chosen** over a monolithic watcher state file.

- Each metadata.yaml stores `mtime`, `size`, `sha256` of its associated blob
- `prism status` walks `.storage/`, stats each node directory, compares mtime
- No central watcher/state.yaml — eliminates sync drift and single-file size concerns
- Optional daemon (inotify watch on `.storage/`) for real-time detection
- Trade-off: full scan stats N files. Acceptable for single-user scale (50K files ≈ 25ms).

### Decision: Python 3.12+ for MVP, Rust for future sync daemon

**Chosen** for rapid iteration, strong AI tooling, and the user's desire to deepen Python skills.

- Core library as a Python package (`prism-core`)
- CLI as a Python entry point (`prism-cli`) using Click
- Future sync daemon as a separate Rust binary (`prism-syncd`) using p2panda
- Communication via filesystem protocol: sync daemon reads dirty flags from metadata.yaml

### Decision: Type schemas as directory of TOML files

**Chosen** over a single monolithic types file.

- `.metadata/types/note.toml`, `contact.toml`, `bookmark.toml`, `file.toml`
- Each type file contains field definitions (name, type, required, default)
- Adding a type = dropping a new file. Merging = per-file, no conflicts.
- Schema validation on `prism new` and `prism edit`

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Blob store model requires user to always use Prism for file access | CLI + future TUI/GUI/WebUI provide the interface. Power users can navigate `.storage/` directly if needed. |
| TOML metadata files are slower to query than a DB | `.metadata/index.txt` provides fast UUID lookups. Full scans are acceptable at single-user scale. |
| [[uuid]] links break if user edits metadata.toml behind Prism's back | This is undefined behavior — user agreed not to mutate vault outside Prism. Corruption detection in `prism validate`. |
| Python performance for large vaults | MVP targets single-user scale. If performance becomes an issue, critical paths can be reimplemented in Rust incrementally (the architecture is designed for this). |
| No full-text search engine in MVP | Basic grep-based search is sufficient for MVP. A dedicated engine can be added post-MVP if needed. |
