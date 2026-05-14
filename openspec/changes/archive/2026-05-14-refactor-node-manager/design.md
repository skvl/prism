## Context

`NodeManager` in `prism-core/prism/node/manager.py` has 3 methods that mix I/O with data logic:

- `edit_node_body(uid)` — calls `subprocess.call([editor, path])` and reads file stats
- `edit_node_fields(uid)` — calls `input()` in a loop to prompt user for each field
- `delete_node(uid)` — calls `input()` for backlink confirmation when `force=False`

These are the only untestable methods in an otherwise well-tested class (80% coverage vs the rest at 95-100%). Additionally, `_would_create_cycle()` is dead code. Meanwhile, link re-extraction after body edits is done manually by the CLI caller (`main.py:552-560`) — it's possible to forget.

The CLI `edit` command also duplicates storage traversal logic (`main.py:497-510` walks the entire `.storage` directory to find a metadata file, even though `NodeManager._resolve_uuid` does the same job with O(1) index lookup).

## Goals / Non-Goals

**Goals:**
- Make all `NodeManager` methods testable without mocking stdin/subprocess
- Move `[[uuid]]` link re-extraction into `commit_body_edit` so it's atomic with body edits
- Remove dead code (`_would_create_cycle`)
- Eliminate O(n) storage walks from CLI `edit` command
- Keep all CLI commands behavior-identical from the user's perspective

**Non-Goals:**
- Not changing how the `$EDITOR` subprocess works (still spawned by CLI)
- Not changing the `delete_node` backlink-warning behavior (just moves the prompt to CLI)
- Not refactoring `QueryEngine` or `PathResolver` (separate concern)
- Not adding new user-facing features

## Decisions

### Decision 1: Split `edit_node_body` into query + commit phases

**Why**: The current method does two things: (1) informs the caller where the body file is and what its current mtime is, and (2) updates metadata after editing. These are separate concerns — the CLI needs the path to spawn the editor, and the library should own the metadata update (including link extraction).

**New methods:**

```python
def get_body_info(self, uid: str) -> tuple[str, float] | None:
    """Returns (body_path, current_mtime) or None if no body."""
    uid = self._resolve_uuid(uid)
    storage_dir = compute_storage_path(self.vault_path, uid)
    meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
    if not meta.blob_extension:
        return None
    body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
    if not os.path.exists(body_path):
        return None
    return (body_path, os.stat(body_path).st_mtime)

def commit_body_edit(self, uid: str, mtime: float, size: int, sha256: str) -> None:
    """Finalize a body edit: update blob metadata AND re-extract links."""
    uid = self._resolve_uuid(uid)
    storage_dir = compute_storage_path(self.vault_path, uid)
    meta_path = NodeMetadata.metadata_path(storage_dir)
    meta = NodeMetadata.from_toml(meta_path)
    meta.blob_mtime = str(mtime)
    meta.blob_size = size
    meta.blob_sha256 = sha256
    meta.updated_at = datetime.now(timezone.utc).isoformat()
    meta.sync_dirty = True
    if meta.blob_extension == "md":
        body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
        if os.path.exists(body_path):
            meta.links = LinkExtractor.extract_from_file(body_path)
    meta.save(meta_path)
```

Alternatives considered:
- Keep a single method with an `editor_callback` parameter — over-engineered, still has I/O in the library
- Return the body path and let the CLI handle everything including metadata updates — duplicates metadata-saving logic across layers

### Decision 2: Split `edit_node_fields` into query + commit phases

**Why**: `input()` inside the library is the worst pattern — it blocks tests and assumes stdin. The CLI should own the prompt loop.

**New methods:**

```python
def get_field_info(self, uid: str) -> tuple[TypeSchema, dict[str, Any]]:
    """Returns (schema, current_field_values) for a node."""
    uid = self._resolve_uuid(uid)
    storage_dir = compute_storage_path(self.vault_path, uid)
    meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
    schema = self.type_loader.load(meta.type)
    if schema is None:
        raise ValueError(f"Unknown type: {meta.type}")
    return (schema, dict(meta.fields))

def update_node_fields(self, uid: str, changes: dict[str, Any]) -> bool:
    """Apply field changes. Returns True if anything changed."""
    if not changes:
        return False
    uid = self._resolve_uuid(uid)
    storage_dir = compute_storage_path(self.vault_path, uid)
    meta_path = NodeMetadata.metadata_path(storage_dir)
    meta = NodeMetadata.from_toml(meta_path)
    for k, v in changes.items():
        meta.fields[k] = v
    meta.updated_at = datetime.now(timezone.utc).isoformat()
    meta.sync_dirty = True
    meta.save(meta_path)
    return True
```

### Decision 3: Remove `input()` from `delete_node`

**Why**: `delete_node` is the only destructive method that prompts the user. The CLI already has `--yes`/`-y` for force mode. The non-force path should either raise or indicate backlinks exist, letting the CLI decide.

```python
def delete_node(self, uid: str, force: bool = False) -> bool:
    uid = self._resolve_uuid(uid)
    storage_dir = compute_storage_path(self.vault_path, uid)
    if not os.path.exists(storage_dir):
        return False
    if not force:
        backlinks = self._find_backlinks(uid)
        if backlinks:
            raise ValueError(
                f"{len(backlinks)} node(s) link to this node. "
                "Use --yes to force deletion."
            )
    shutil.rmtree(storage_dir)
    self._index_remove(uid)
    return True
```

**Alternatives considered:**
- Returning a `(bool, list[backlinks])` tuple — awkward API, breaks existing callers
- Silent deletion — dangerous, users might accidentally lose links

### Decision 4: Move link re-extraction into `commit_body_edit`

**Why**: After editing a node's body, the `[[uuid]]` links in it may have changed. If link extraction happens outside the library (as it does now in `main.py`), it's possible for a caller to forget, leaving stale links in metadata. Making it part of `commit_body_edit` makes it atomic — you can't update blob metadata without also re-extracting links.

**Import**: `prism/node/manager.py` needs to import `LinkExtractor` from `prism/graph/links.py`. This creates a `node/manager.py → graph/links.py` dependency edge, but no cycle exists:

```
links.py  →  node/metadata.py, node/storage.py, vault/registry.py
manager.py → node/metadata.py, node/storage.py, path/resolver.py, types/*, vault/vault.py, graph/links.py ← NEW
```

No cycle, no circular import risk.

### Decision 5: Extract `add_path_to_node` and `remove_path_from_node`

**Why**: The CLI `edit` command (`main.py:520-550`) handles `--add-path`/`--remove-path` by inline metadata traversal. Moving to `NodeManager` eliminates the CLI's O(n) storage walk and keeps path manipulation consistent.

```python
def add_path_to_node(self, uid: str, path_str: str) -> bool:
    """Associate a node with a path. Returns True if added."""
    uid = self._resolve_uuid(uid)
    resolver = PathResolver(self.vault_path)
    path_uuid = resolver.resolve(path_str)
    storage_dir = compute_storage_path(self.vault_path, uid)
    meta_path = NodeMetadata.metadata_path(storage_dir)
    meta = NodeMetadata.from_toml(meta_path)
    if path_uuid in meta.paths:
        return False
    meta.paths.append(path_uuid)
    meta.updated_at = datetime.now(timezone.utc).isoformat()
    meta.sync_dirty = True
    meta.save(meta_path)
    return True

def remove_path_from_node(self, uid: str, path_str: str) -> bool:
    """Remove a path association. Returns True if removed."""
    uid = self._resolve_uuid(uid)
    resolver = PathResolver(self.vault_path)
    path_uuid = resolver.resolve(path_str)
    storage_dir = compute_storage_path(self.vault_path, uid)
    meta_path = NodeMetadata.metadata_path(storage_dir)
    meta = NodeMetadata.from_toml(meta_path)
    if path_uuid not in meta.paths:
        return False
    meta.paths = [p for p in meta.paths if p != path_uuid]
    meta.updated_at = datetime.now(timezone.utc).isoformat()
    meta.sync_dirty = True
    meta.save(meta_path)
    return True
```

### Decision 6: Remove `_would_create_cycle` (dead code)

**Why**: The method exists but is never called anywhere in the codebase. No tests cover it. If a `path mv`/`path rename` command is ever implemented, this method (or a better version of it) should be reintroduced with tests.

## Risks / Trade-offs

- **Risk: Existing code (e.g., REPL, tutor) calls the old methods** → Audit all callers. `edit_node_body` and `edit_node_fields` are called from `main.py:553-568` only. `_would_create_cycle` is called nowhere.
- **Risk: Tests need updating** → Old method tests removed, new method tests added. The existing fixture patterns (`vault_dir`, `tempfile.mkdtemp()`) work for all new methods.
- **Trade-off: `commit_body_edit` always re-extracts links** → If the body hasn't changed (CLI checks mtime before calling), this is irrelevant. If the body has changed, re-extraction is the correct behavior.
- **Trade-off: `delete_node` now raises instead of prompting** → The CLI `prism rm` command already supports `--yes`. Existing callers that pass `force=False` and encounter backlinks will get a `ValueError` instead of a prompt — but the only caller is `main.py:583`.
