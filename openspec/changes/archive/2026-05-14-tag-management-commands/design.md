## Context

Tags currently live as a `list[str]` on `NodeMetadata` and are serialized to `metadata.toml`. They can be set at creation via `prism new --tag` but never modified afterward. There is no aggregation command to see all tags in a vault. The `edit` command supports `--add-path`/`--remove-path` for paths but has no tag equivalents.

The existing `prism path` command group (create/rm/tree) provides the structural template for a `prism tag` group.

## Goals / Non-Goals

**Goals:**
- Add, remove, list (with count), and rename tags via CLI and REPL
- Tags as universal metadata — no schema validation, any node can carry any tag
- Idempotent add and remove (no errors for already-present or absent tags)
- Tab completion in REPL for tag names and UUIDs in tag subcommands
- Tutor lesson covering tag management workflows
- README docs for all new commands

**Non-Goals:**
- Tag hierarchy / taxonomy (parent-child tag relationships)
- Tag colors, icons, or display metadata
- Tag-based access control
- Bulk tag operations beyond rename (e.g., merge, split)
- Changing the existing `prism new --tag` behavior
- `prism tag show` (redundant — `prism show` already shows per-node tags)

## Decisions

**1. New `prism tag` command group over extending `prism edit`**
- Precedent: `prism path` uses the same pattern
- More discoverable (`prism tag --help` lists all tag ops)
- `rename` doesn't fit naturally into `edit` semantics (it's a cross-node operation)
- `list` is a pure aggregation command with no target node

**2. Idempotent add/remove semantics**
- `tag add` on a tag that already exists: no-op (silent skip)
- `tag rm` on a tag that doesn't exist: no-op (silent skip)
- Keeps commands safe for scripting. `rename_tag` will error if `new` is invalid per `TAG_PATTERN`, but will be cross-node idempotent (if `old` doesn't exist on a particular node, skip it)

**3. Tags as universal metadata, not schema-constrained**
- The type system marks `tags` as an optional array field on note, bookmark, file types, but `NodeMetadata` stores tags unconditionally. Adding a tag to a contact node works at the data layer already. We make this official — any node can hold tags regardless of type schema.

**4. `list` output format**
- Without `--count`: one tag name per line (sorted)
- With `--count`: `tag_name (N)` — number of nodes that have this tag
- This is simple, greppable, and consistent with Unix conventions

**5. REPL commands mirror CLI**
- `tag add`, `tag rm`, `tag list`, `tag rename` all work in REPL
- Tab completion for UUIDs on `tag add` / `tag rm`
- Tab completion for existing tag names on `tag rm` / `tag rename`
- No alias needed for the `tag` command itself (short enough)

## Risks / Trade-offs

- **Rename is O(n)** — iterates all nodes to find and replace a tag. On vaults with thousands of nodes this could be slow, but the current design has no tag index (tags aren't first-class entities). Acceptable for a single-user local tool.
- **No transaction safety** — if rename fails partway through (e.g., disk full), some nodes will have the new tag and some won't. Mitigation: validate the new tag before starting the loop, and process nodes sequentially so partial updates are recoverable.
- **`tag rm` vs `prism edit --remove-path` asymmetry** — paths use `edit` for per-node ops and `path rm` for structural deletion. Tags use the group for everything. This is intentional: tags don't have independent existence like path nodes do, so the group is the right home for all tag operations.
