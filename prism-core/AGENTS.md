# prism-core — Agent Guide

## Module Map

### `prism/vault/` — Vault lifecycle

| File | Key Exports |
|------|-------------|
| `vault.py` | `Vault` class (`init()`, `open()`, `validate()`), `generate_uuid()`, `uuid_to_path()` |
| `registry.py` | `VaultRegistry` (`add()`, `list()`, `remove()`, `get_by_uuid()`) |
| `context.py` | `detect_vault(cwd, vault_flag)` — walks up from cwd to find vault |

### `prism/types/` — Type system

| File | Key Exports |
|------|-------------|
| `schema.py` | `TypeSchema`, `FieldDef` dataclasses, `VALID_TYPES`, `VALID_BODY_MODELS` |
| `loader.py` | `TypeLoader` (`load_all()`, `load(name)`) |
| `validator.py` | `FieldValidator` (`validate(fields)`) |
| `builtins.py` | `NOTE_TOML`, `CONTACT_TOML`, `BOOKMARK_TOML`, `FILE_TOML`, `PATH_TOML` constants |

### `prism/node/` — Node CRUD and storage

| File | Key Exports |
|------|-------------|
| `manager.py` | `NodeManager` (`create_node`, `edit`, `delete`, `show`, `list`), `resolve_uuid()` |
| `metadata.py` | `NodeMetadata` dataclass (`from_toml()`, `to_toml()`, `save()`, `metadata_path()`) |
| `storage.py` | `StorageEngine` (`import_blob`, `delete`, `read`, `verify`), `sha256_file()`, `compute_storage_path()` |

### `prism/graph/` — Link extraction and graph export

| File | Key Exports |
|------|-------------|
| `links.py` | `LinkExtractor` (`extract_links()`), `BacklinkIndex` (`build()`, `get_backlinks()`), `GraphExporter` (`export_dot()`, `export_json()`) |

### `prism/query/` — Query language

| File | Key Exports |
|------|-------------|
| `parser.py` | `QueryParser` (`parse()`), `QueryAST` dataclass |
| `engine.py` | `QueryEngine` (`execute(ast)`) |

### `prism/path/` — Path hierarchy

| File | Key Exports |
|------|-------------|
| `resolver.py` | `PathResolver` (`resolve()`, `resolve_or_create()`, `collect_descendants()`, `complete()`) |

### Root files

| File | Key Exports |
|------|-------------|
| `tracking.py` | `ChangeTracker` (`status()`, `mark_dirty()`, `re_extract_links()`, `update_blob_info()`) |
| `__init__.py` | `VERSION` constant |

## Type System Overview

Types are defined in TOML files under `.metadata/types/` in a vault. Each type file defines:

- `name` — unique type identifier (e.g. `"note"`, `"contact"`)
- `icon` — emoji icon for display
- `body_model` — `"null"` (no body), `"file(markdown)"` (markdown body), or `"file(binary)"` (binary body)
- `[[fields]]` — array of field definitions, each with `name`, `type` (string/url/datetime/number/array), `required` (bool), `default`

Four built-in types ship with the project: `note` (markdown body + tags), `contact` (structured fields), `bookmark` (url), `file` (binary body).

Validation is handled by `FieldValidator` which checks:
- Required fields are present
- Values match expected types
- No unknown fields are submitted

## Import Conventions

- **stdlib → third-party → local** (grouped by blank lines)
- Within `prism-core`, use absolute imports via the package: `from prism.types.loader import TypeLoader`
- Within submodules, relative imports for intra-package references
- `TYPE_CHECKING` imports are avoided — mypy strict mode catches all type issues statically

## Architecture

See [`ARCHITECTURE.md`](../ARCHITECTURE.md) for the full system design including data flow diagrams and key design decisions.
