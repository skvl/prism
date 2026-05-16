## Context

Nodes store data in UUID-partitioned directories under `.storage/`. Each directory contains `metadata.toml` (structured fields) and optionally `data.<ext>` (body blob for types with body storage). There is currently no mechanism for attaching brief free-form summaries to nodes — users resort to cramming descriptions into titles, tags, or the body itself.

This design adds an optional `description.md` file per node — a Markdown file alongside `metadata.toml` — providing a universal annotation layer across all node types. The description is supplemental text, independent of the body, and stored as a standalone file to avoid TOML escaping issues with multi-line Markdown content.

## Goals / Non-Goals

**Goals:**
- Every node can optionally have a Markdown description stored as `description.md`
- Description file metadata (sha256, mtime, size) is tracked in `metadata.toml` for change detection
- `prism new --desc` and `prism edit --desc` set/update/clear descriptions
- `prism show --desc` and `prism list --desc` display descriptions
- Description text is included in full-text search
- `prism status` detects description changes
- Deleting a node removes its `description.md` along with the rest of the node directory

**Non-Goals:**
- No rich-text or WYSIWYG editing — plain Markdown
- No rich-text or WYSIWYG editing — plain Markdown
- No description template or auto-generation
- No type-specific description schemas — description is universal
- No dedicated `prism describe` subcommand — handled via `--desc` flags

## Decisions

### 1. Separate Markdown file vs. TOML-inline string

**Decision**: `description.md` as a standalone file.

| Criterion | Separate file | TOML field |
|---|---|---|
| No escaping issues | ✓ | Multi-line Markdown needs careful quoting |
| Edit with any Markdown editor | ✓ | Must edit inside TOML context |
| Clean diffs | ✓ | Diffs show Markdown content directly |
| Atomicity | Extra file to manage | Single file |

The current architecture already uses `data.md` for body content. `description.md` follows the same convention and pattern.

### 2. Track description in metadata

**Decision**: Add `desc_sha256`, `desc_mtime`, `desc_size` to `NodeMetadata`.

This mirrors the existing blob tracking pattern (`blob_sha256`, `blob_mtime`, `blob_size`). Enables:
- `prism status` to detect description changes without statting every node
- `prism verify` to check description integrity
- Future sync to know which descriptions changed

These fields are only written to `metadata.toml` when a description exists (same as blob fields are omitted when there's no blob).

### 3. File existence as the signal

**Decision**: No `has_description` boolean field. If `description.md` exists, there's a description. If not, there isn't.

When `--desc ""` is passed (empty string), the file is deleted and metadata fields are cleared. This keeps the data model simple and avoids synchronization bugs between a boolean field and actual file state.

### 4. CLI surface — `--desc` flag, not a separate command

**Decision**: `--desc` option on `prism new`, `prism edit`, `prism show`, and `prism list`.

- `prism new note "Title" --desc "A brief summary"` — creates with description
- `prism edit <uuid> --desc "Updated summary"` — creates or updates description
- `prism edit <uuid> --desc ""` — removes description (deletes file)
- `prism show <uuid> --desc` — includes description in output
- `prism list --desc` — adds a description preview column

A separate `prism describe` command would be redundant — the description is a node attribute, not a separate entity.

### 5. `[[uuid]]` links in descriptions

**Decision**: Description content IS scanned for `[[uuid]]` links, and those links are added to the node's `links` array (same as body text).

Descriptions are Markdown text and users will naturally want to reference other nodes (`see [[abc-123]] for details`). Links extracted from descriptions are stored alongside body links in the shared `links` array — no distinction is needed. Description-only edits trigger link re-extraction, same as body-only edits.

### 6. Search: include descriptions in full-text grep search

**Decision**: Full-text search (`prism query "terms"`) greps both `data.md` and `description.md`.

This is a minimal change — the existing grep-based search already walks node directories. Adding `description.md` to the grep targets is straightforward and consistent with user expectation.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Old vaults have no `description.md` files | Description is fully optional. No migration needed. |
| User manually creates `description.md` outside Prism | `prism status` detects new description.md via mtime mismatch, same as blob detection. |
| Large descriptions bloat the node directory | Self-limiting — descriptions are summaries, not documents. No size limit enforced. |
| `--desc` on `prism new` adds complexity to an already multi-option command | Description is a simple string argument. No additional complexity in validation or parsing. |
| Search performance: grepping another file per node | Description files are small. The grep cost is negligible compared to existing body search. |
| Description changes trigger link re-extraction, increasing status time | Links can be extracted incrementally — only changed descriptions need re-scanning. |
| REPL doesn't support `--desc` natively | REPL commands (`new`, `edit`, `show`) will parse `--desc` from the command line string and pass it through to the business logic — same pattern as other flags. |
| Tutor lessons need updating | Adding a description step to Lesson 2 (first note) naturally introduces the concept early without restructuring the lesson plan. |
