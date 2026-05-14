## 1. Root AGENTS.md restructure

- [x] 1.1 Rewrite root `AGENTS.md` as hub: keep overview, setup, and conventions; add agent constraints (`.tmp/` only, no files outside project); add links to per-package guides; move module map and command table to sub-package guides
- [x] 1.2 Remove module map and command table sections from root `AGENTS.md` (they move to per-package guides)

## 2. Per-package agent guides

- [x] 2.1 Create `prism-core/AGENTS.md` with expanded module map (file-level descriptions), type system overview, import conventions, and link to ARCHITECTURE.md
- [x] 2.2 Create `prism-cli/AGENTS.md` with command reference table, Click wiring patterns, REPL architecture notes, and tutor system notes

## 3. INDEX.md navigation index

- [x] 3.1 Create `INDEX.md` at project root with one-line-per-entry listing of every subdirectory and file, grouped by area, with emoji prefixes and brief descriptions

## 4. ARCHITECTURE.md system design

- [x] 4.1 Create `ARCHITECTURE.md` at project root with ASCII architecture diagram, data flow (import → storage → metadata → graph), key design decisions (content addressing, TOML metadata, UUID partitioning), and module interaction patterns

## 5. Docstrings — prism-core (library)

- [x] 5.1 Add module-level docstrings to all files in `prism-core/prism/` (vault/, types/, node/, graph/, query/, tracking.py)
- [x] 5.2 Add class docstrings to: `Vault`, `FieldDef`, `TypeSchema`, `TypeLoader`, `FieldValidator`, `NodeMetadata`, `StorageEngine`, `NodeManager`, `LinkExtractor`, `BacklinkIndex`, `GraphExporter`, `QueryParser`, `QueryEngine`, `ChangeTracker`
- [x] 5.3 Add function docstrings to all public functions in `prism-core/prism/` — including top-level helpers (`generate_uuid`, `uuid_to_path`, `resolve_uuid`, `compute_storage_path`, `sha256_file`, etc.)
- [x] 5.4 Add Google-style Args/Returns/Raises sections to non-trivial docstrings across all core files

## 6. Docstrings — prism-cli (CLI)

- [x] 6.1 Add module-level docstrings to all files in `prism-cli/prism_cli/` (main.py, commands.py, repl.py, tutor.py, completions.py)
- [x] 6.2 Add class docstrings to: `REPLContext`, `ReplMode`, `PrismTutor`, `CompletionProvider` (and any other classes)
- [x] 6.3 Add function docstrings to all public functions in `prism-cli/prism_cli/`
- [x] 6.4 Add Google-style Args/Returns sections to non-trivial docstrings

## 7. Final verification

- [x] 7.1 Run `ruff check prism/` from `prism-core/` — no new lint errors from docstring additions
- [x] 7.2 Run `mypy prism/` from `prism-core/` — no new type errors
- [x] 7.3 Run `pytest` from `prism-core/` — all tests pass
- [x] 7.4 Run `pytest` from `prism-cli/` — all tests pass
