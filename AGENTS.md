# Prism — Agent Guide

## Project Overview

Local-first, single-user PKM (Personal Knowledge Manager). Content-addressed blob store with typed node graph, TOML metadata, UUID-partitioned storage, and `[[uuid]]` link system.

## Agent Constraints

AI agents working in this project MUST follow these rules:

- **No files outside project root**: All created, modified, or temporary files MUST reside within the project directory.
- **Use `.tmp/` for temp files**: Any temporary files, scratch output, or intermediate artifacts MUST be placed in `.tmp/` at the project root.
- **Respect scanning exclusions**: Directories listed in Agent Scanning Exclusions should be skipped during file searches.

## Directory Structure

```
├── prism-core/              # Library package (prism-core)
│   ├── pyproject.toml
│   ├── prism/
│   │   ├── vault/           # Vault lifecycle (init, open, validate, registry, context detection)
│   │   ├── types/           # Type system (schemas, loader, validator, 4 built-in types)
│   │   ├── node/            # Node management (CRUD, metadata, storage engine, SHA-256)
│   │   ├── graph/           # Link extraction, backlinks, graph export (DOT/JSON)
│   │   ├── query/           # Query parser (tag:/type:/AND/OR/NOT), query engine
│   │   └── tracking.py      # Change detection (mtime, dirty flag, re-extract)
│   └── tests/               # pytest test files
├── prism-cli/               # CLI package (prism-cli)
│   ├── pyproject.toml
│   └── prism_cli/
│       └── main.py          # Click entry point (14 commands)
├── openspec/                # Specification system
│   ├── specs/               # Main capability specs (7 areas)
│   └── changes/archive/     # Archived completed changes
├── README.md
└── .gitignore
```

## Setup

Both packages must be installed together in editable mode:

```bash
pip install -e prism-core/ -e prism-cli/
```

## Code Conventions

- **Python 3.11+**, strict mypy (`strict = true`, `disallow_untyped_defs = true`)
- **Imports**: stdlib → third-party → local, grouped by blank lines
- **Naming**: `snake_case` modules/functions, `PascalCase` classes, `UPPER_SNAKE` constants
- **Private**: `_leading_underscore` for methods and helpers
- **Data classes**: `@dataclass` over plain dicts (NodeMetadata, FieldDef, TypeSchema)
- **Serialization**: TOML via `tomlkit` for all metadata
- **CLI**: Click with `@click.group()`, argument/option decorators, `@click.pass_context`
- **Testing**: pytest, class-based groups, tempfile fixtures, no mocking
- **Error handling**: CLI catches exceptions → `click.echo(..., err=True)` + `sys.exit(1)`
- **Dependencies**: `tomlkit`, `click`, `click-default-group`

## Per-Package Guides

Detailed documentation for each sub-package:

- **[`prism-core/AGENTS.md`](prism-core/AGENTS.md)** — Module map (file-level descriptions), type system overview, import conventions, architecture link
- **[`prism-cli/AGENTS.md`](prism-cli/AGENTS.md)** — Command reference table, Click wiring patterns, REPL architecture, tutor system notes

## OpenSpec

Capability specs live in `openspec/specs/<capability>/spec.md` (7 areas). Archived changes in `openspec/changes/archive/`.

## Agent Scanning Exclusions

The following directories should be excluded from agent scanning:
- `documentation/ai-sessions/` — contains exported AI chat logs, not project code
