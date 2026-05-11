# Prism — Agent Guide

## Project Overview

Local-first, single-user PKM (Personal Knowledge Manager). Content-addressed blob store with typed node graph, TOML metadata, UUID-partitioned storage, and `[[uuid]]` link system.

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

## Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run tests (from `prism-core/`) |
| `ruff check prism/` | Lint (from `prism-core/`) |
| `mypy prism/` | Type check (from `prism-core/`) |
| `prism --help` | CLI help |

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

## Module Map

| Module | Key Classes/Functions |
|--------|----------------------|
| `vault/vault.py` | `Vault.init()`, `.open()`, `.validate()`, `generate_uuid()`, `uuid_to_path()` |
| `vault/registry.py` | `VaultRegistry.add()`, `.list()`, `.remove()`, `.get_by_uuid()` |
| `vault/context.py` | `detect_vault(cwd, vault_flag)` |
| `types/schema.py` | `TypeSchema`, `FieldDef` dataclasses, `VALID_TYPES`, `VALID_BODY_MODELS` |
| `types/loader.py` | `TypeLoader.load_all()`, `.load(name)` |
| `types/validator.py` | `FieldValidator.validate(fields)` |
| `types/builtins.py` | `NOTE_TOML`, `CONTACT_TOML`, `BOOKMARK_TOML`, `FILE_TOML` constants |
| `node/storage.py` | `StorageEngine.import/delete/read/verify`, `sha256_file()`, `compute_storage_path()` |
| `node/metadata.py` | `NodeMetadata` dataclass, `.from_toml()`, `.to_toml()`, `.save()` |
| `node/manager.py` | `NodeManager.create/edit/delete/show/list`, index management |
| `graph/links.py` | `LinkExtractor.extract_links()`, `BacklinkIndex`, `GraphExporter.export_dot/json()` |
| `query/parser.py` | `QueryParser.parse()`, `QueryAST` |
| `query/engine.py` | `QueryEngine.execute(ast)` |
| `tracking.py` | `ChangeTracker.status()`, `.mark_dirty()`, `.re_extract_links()` |
| CLI `main.py` | `cli` group + 14 commands wired to library |

## OpenSpec

Capability specs live in `openspec/specs/<capability>/spec.md` (7 areas). Archived changes in `openspec/changes/archive/`.

## Agent Scanning Exclusions

The following directories should be excluded from agent scanning:
- `documentation/ai-sessions/` — contains exported AI chat logs, not project code
