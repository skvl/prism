## Context

The current tag system is flat — tags are stored as `list[str]` on `NodeMetadata` and support only exact-match querying. There is no hierarchy, no browsing, and no index. Path-like tags introduce a virtual filesystem built on top of the existing graph and node storage infrastructure.

Path segments are stored as regular nodes (type = `path`) with parent-child edges in `[[uuid]]` links. This reuses all existing infrastructure — storage engine, metadata serialization, link extraction — without new storage mechanisms.

## Goals / Non-Goals

**Goals:**
- Define the `path` node type and its TOML schema
- Add `paths` as a first-class field on `NodeMetadata`
- Implement `mkdir -p` path creation with auto-generated parent segments
- Implement cascade deletion of path subtrees
- Implement `path:` query prefix with exact-match semantics (resolves path → UUID → match)
- Implement per-segment TAB completion in the REPL
- Inline validation of tag and segment character rules via `NodeMetadata.__post_init__`
- Root `/` node auto-created on vault init
- Path nodes excluded from graph export by default (opt-in flag)

**Non-Goals:**
- Persistent path-to-UUID index (noted as future optimization)
- Subtree/prefix matching in queries (exact match only)
- Renaming path segments (create new path, delete old, re-tag)
- Cross-vault path resolution

## Data Model

### Path Node (metadata.toml)

```toml
type = "path"
title = "2026"

[fields]
name = "2026"

[[links]]
target = "<parent-segment-uuid>"
type = "path-parent"
title = ".."
```

The root `/` node has no parent link. Its UUID is deterministic (derived from a known string, or stored in `.metadata/config.toml`).

### NodeMetadata Changes

```python
@dataclass
class NodeMetadata:
    uuid: str
    type: str
    title: str = ""
    tags: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)  # NEW: list of path segment UUIDs
    links: list[dict[str, str]] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)
    updated_at: str = ""
    created_at: str = ""

    def __post_init__(self):
        for tag in self.tags:
            if not TAG_PATTERN.match(tag):
                raise ValueError(f"Invalid tag: {tag!r}")
        for seg in self._all_path_segments():  # segments extracted from paths if stored inline
            if not SEGMENT_PATTERN.match(seg):
                raise ValueError(f"Invalid path segment: {seg!r}")
```

### Validation Rules

```python
# Simple tag: no space, no /, UTF-8 letters/digits/_/-
TAG_PATTERN = re.compile(r'\A[\w\-]+\Z')
# With re.UNICODE, \w matches Unicode letters/digits + underscore

# Path segment: no / or control chars, UTF-8 including spaces
SEGMENT_PATTERN = re.compile(r'\A[^\x00-\x1f\x7f/]+\Z')
```

## Path Creation Flow

```
prism path create /photos/2026/02/vacations

1. Normalize: strip leading /, split on / → ["photos", "2026", "02", "vacations"]
2. Walk segments from root, resolving each name:
   - Look up root node UUID (from vault config)
   - For "photos": find child of root with fields.name == "photos"
     - Found? → continue
     - Not found? → create new path node, link to root as path-parent
   - Repeat for "2026", "02", "vacations"
3. Return leaf node UUID
```

Resolution walks the graph — from root, scan children's `links`, fetch their metadata, check `fields.name`. For deep paths, this is O(d × f) where d is depth and f is average fan-out.

## Path Deletion Flow

```
prism path rm /photos/2026/02

1. Resolve path to leaf node UUID
2. BFS/DFS to collect all descendant UUIDs
3. For each descendant (including leaf):
   a. Remove its UUID from all nodes' `paths` lists (scan all metadata)
   b. Delete node's storage directory
4. Remove segment from parent's links
```

Cascade deletion is the most expensive operation — step 3a requires scanning every node's metadata. This is acceptable for a single-user local tool where deletions are rare.

## Query Resolution

```
query: path:/photos/2026/02/vacations

1. Resolve path to leaf UUID (same resolution as creation)
2. Scan all nodes, filter those with <leaf-uuid> in node.paths
3. Apply remaining query filters (AND/OR/NOT with tags etc.)
```

The query engine needs a new filter type `"path"` alongside existing `"tag"` and `"type"`. The parser recognizes `path:<value>` as a token.

No persistent index — resolution walks the graph, then scans all nodes. A future optimization would cache the `path-string → uuid` mapping.

## Graph Integration

- Parent-child edges stored as `[[uuid]]` links with `type = "path-parent"` in the link dict
- Path nodes are regular nodes — they can have tags, appear in `tag:` queries etc.
- `GraphExporter` has a new `--include-paths` flag (default false). When false, skips `type = "path"` nodes.
- `BacklinkIndex` includes path nodes (a path segment shows backlinks of nodes filed under it)

## TAB Completion (REPL)

```
1. User types "path:/pho" and presses TAB
2. REPL extracts the current segment being typed (segments after last /)
3. Walks the path graph from root, following segments before cursor
4. At the target parent node, scans children for matching prefix
5. Returns completions: "/photos", "/phone"
```

Implementation sketch:
- `PathResolver.complete(prefix_path: str) → list[str]` 
- Takes partial path, returns matching segment names
- Walk existing nodes (graph resolution or flat scan)

## CLI Surface

```
prism path
├── create <path>       — create path segment hierarchy (mkdir -p)
├── rm <path>           — remove path segment (cascade delete)
└── tree [<path>]       — browse virtual filesystem hierarchy

prism edit <uuid>
    --add-path <path>   — file node under a path
    --remove-path <path> — un-file node from a path
```

## Vault Init

On `prism init`, after creating the storage directory structure, a root path node is created:

```toml
# .storage/<root-uuid>/metadata.toml
type = "path"
title = "/"

[fields]
name = "/"
```

The root UUID is stored in `.metadata/config.toml` as `path_root_uuid`.

## Decisions

| Decision | Choice | Alternatives Considered |
|----------|--------|------------------------|
| Path storage | Regular graph nodes with type=path | Separate index file, dedicated storage |
| Parent edges | [[uuid]] links with path-parent type | SQLite, custom index |
| Paths on NodeMetadata | list[str] of UUIDs | list[str] of path strings |
| Validation | __post_init__ on NodeMetadata | CLI-level, schema-level, validator module |
| Graph export | Exclude paths by default | Include by default, separate export |
| Query matching | Exact match only | Subtree/prefix matching |
| Root node | Created on vault init | Implicit root, created on first path create |
| Delete semantics | Cascade delete children, clean up node refs | Refuse deletion if children exist |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Path resolution walks graph O(d × f) — slow for deep paths with wide fan-out | Acceptable for single-user local tool; persistent index noted as future optimization |
| Cascade delete scans all nodes — expensive for large vaults | Deletions are rare; acceptable trade-off |
| No path validation at edit time (user provides path string, not UUID) | Resolve path to UUID at edit time, fail early if not found |
| Circular path links (accidental) | Validate new links don't create cycles during create |
| Node with `paths` referencing deleted segment UUID | Cleaned up during cascade delete; stale references possible only if storage corrupted |

## Open Questions

- Path completion walks the graph — for popular parents with many children, this could be slow. Acceptable at REPL speeds?
  - Answer: yes it is acceptable in MVP.
- Should `prism show` display resolved path strings (e.g., `/photos/2026/02/vacations`) or raw UUIDs?
  - Answer: resolved paths.
- Where is the root UUID stored? Options: `.metadata/config.toml` or deterministic derivation from a namespace UUID + string "/".
  - Answer: config
