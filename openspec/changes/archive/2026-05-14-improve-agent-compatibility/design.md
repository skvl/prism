## Context

The project currently has a single `AGENTS.md` at root that combines overview, conventions, module map, and scanning rules. There are no per-package agent guides, no docstrings in library code, no navigable index, and no architecture document. Agents must discover the codebase structure from scratch each session.

The existing `AGENTS.md` is well-written — this change preserves its content and layers additional structure around it rather than replacing it.

## Goals / Non-Goals

**Goals:**
- Layer project documentation so agents can find the right level of detail based on what file they're working with
- Add docstrings to every module, class, and function in both packages
- Create a navigable project index (`INDEX.md`)
- Create a system architecture document (`ARCHITECTURE.md`)
- Document the temp-directory constraint (`.tmp/`)
- All changes are documentation-only — zero runtime behavior impact

**Non-Goals:**
- No changes to any `.py` file logic, signatures, or behavior
- No new dependencies
- No automation or CI for docstring validation
- No docstring enforcement tooling (linting, coverage)

## Decisions

### 1. Docstring style: Google

Google-style is chosen over NumPy or Sphinx because:
- More compact (less vertical space in editor)
- Widely recognized by AI training data
- Types are already explicit in signatures (mypy strict) — docstrings focus on semantics
- Consistent with Python community trend

```python
def resolve_uuid(vault_path: str, partial: str) -> str:
    """Resolve a partial UUID to a full UUID.

    Searches all metadata.toml files in .storage for a node whose
    UUID starts with the given prefix. Raises on zero or multiple matches.

    Args:
        vault_path: Root path of the vault.
        partial: Full or partial UUID string.

    Returns:
        The full 36-character UUID string.

    Raises:
        ValueError: Zero or multiple matches found.
    """
```

**Alternative considered:** NumPy-style (too verbose for this codebase). No docstrings at all (rejected — defeats the purpose).

### 2. AGENTS.md layering: Hub-and-spoke

Root `AGENTS.md` becomes the entry point containing:
- One-paragraph project overview
- Setup instructions
- Three agent constraints (stay in project dir, use `.tmp/`, scan exclusions)
- Links to `prism-core/AGENTS.md` and `prism-cli/AGENTS.md`

`prism-core/AGENTS.md` contains:
- Module map (moved from root, expanded with file-level details)
- Type system overview
- Convention specifics (module naming, import patterns)
- Link to architecture doc

`prism-cli/AGENTS.md` contains:
- Command table (moved from root)
- Click wiring patterns
- REPL architecture notes
- Tutor system notes

**Alternative considered:** Single monolithic file (current approach — doesn't scale as project grows).

### 3. INDEX.md as navigable index

Sits at root. One-line-per-entry format with emoji prefixes:
- Each subdirectory gets a section
- Each module file gets a line with a brief description
- Links to architecture doc and agent guides

**Alternative considered:** `MODULES.md` only (would duplicate index concerns).

### 4. ARCHITECTURE.md as system design doc

Contains:
- ASCII architecture diagram
- Data flow: file import → storage → metadata → graph
- Key design decisions (content addressing, TOML metadata, UUID partitioning)
- Module interaction patterns
- Concurrency model (none — single-user, single-threaded)

### 5. Docstring scope

Every public module, class, and function gets a docstring. Private helpers (`_leading_underscore`) get them where the logic is non-trivial. Module-level docstrings describe the file's purpose and exported symbols.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Docstrings drift from code over time | Acceptable — no enforcement. Static types catch signature drift; docstrings are semantic guidance |
| AGENTS.md links break when files are moved | Links are relative paths; code review catches drift |
| Too much docstring noise in small files | Use short 1-line docstrings for trivial functions |
| Root directory gets cluttered with new files | Only 3 new root files (INDEX.md, ARCHITECTURE.md, plus per-package AGENTS.md files in their own dirs) |
