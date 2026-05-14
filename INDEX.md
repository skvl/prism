# Prism — Project Index

## 📁 Root

| Entry | Description |
|-------|-------------|
| `AGENTS.md` | Agent guide — overview, setup, conventions, constraints, links to per-package guides |
| `README.md` | Project readme |
| `.gitignore` | Git ignore rules |

## 📦 prism-core/ — Library package

| Entry | Description |
|-------|-------------|
| `pyproject.toml` | Package config (editable install) |
| `AGENTS.md` | Package-level agent guide with module map and type system |
| `prism/__init__.py` | Package root, exports `VERSION` |
| `prism/tracking.py` | Change detection (mtime, dirty flag, re-extract) |
| `prism/vault/__init__.py` | Vault subpackage |
| `prism/vault/vault.py` | `Vault` class — init, open, validate, UUID generation |
| `prism/vault/registry.py` | `VaultRegistry` — add, list, remove vaults |
| `prism/vault/context.py` | `detect_vault()` — auto-detect vault from cwd |
| `prism/types/__init__.py` | Types subpackage |
| `prism/types/schema.py` | `TypeSchema`, `FieldDef` dataclasses, valid types/body models |
| `prism/types/loader.py` | `TypeLoader` — load type definitions from TOML files |
| `prism/types/validator.py` | `FieldValidator` — validate fields against schema |
| `prism/types/builtins.py` | Built-in type TOML definitions (note, contact, bookmark, file, path) |
| `prism/node/__init__.py` | Node subpackage |
| `prism/node/manager.py` | `NodeManager` — create, edit, delete, show, list, tag, path operations |
| `prism/node/metadata.py` | `NodeMetadata` dataclass — TOML serialization, tag pattern |
| `prism/node/storage.py` | `StorageEngine` — blob import/delete/read/verify, SHA-256 hashing |
| `prism/graph/__init__.py` | Graph subpackage |
| `prism/graph/links.py` | `LinkExtractor`, `BacklinkIndex`, `GraphExporter` — link extraction and graph export |
| `prism/query/__init__.py` | Query subpackage |
| `prism/query/parser.py` | `QueryParser`, `QueryAST` — parse tag:/type:/AND/OR/NOT queries |
| `prism/query/engine.py` | `QueryEngine` — execute query AST against vault nodes |
| `prism/path/__init__.py` | Path subpackage |
| `prism/path/resolver.py` | `PathResolver` — path hierarchy resolution, creation, completion |
| `tests/__init__.py` | Test package |
| `tests/test_vault.py` | Vault lifecycle tests |
| `tests/test_types.py` | Type system tests |
| `tests/test_loader.py` | Type loader tests |
| `tests/test_manager.py` | Node manager tests |
| `tests/test_metadata.py` | Node metadata tests |
| `tests/test_storage.py` | Storage engine tests |
| `tests/test_graph.py` | Graph/link tests |
| `tests/test_query.py` | Query parser/engine tests |
| `tests/test_path_resolver.py` | Path resolver tests |
| `tests/test_tracking.py` | Change tracking tests |
| `tests/test_repl.py` | REPL integration tests (core side) |
| `tests/test_tutor.py` | Tutor integration tests (core side) |

## 🖥️ prism-cli/ — CLI package

| Entry | Description |
|-------|-------------|
| `pyproject.toml` | Package config (editable install) |
| `AGENTS.md` | Package-level agent guide with command reference and patterns |
| `prism_cli/__init__.py` | CLI package root |
| `prism_cli/main.py` | Click entry point — `cli` group + 14+ commands wired to library |
| `prism_cli/commands.py` | Command implementations, `CmdResult` dataclass |
| `prism_cli/repl.py` | `Repl` class — interactive REPL with aliases, history, completion |
| `prism_cli/tutor.py` | `Tutor` class — 8-lesson interactive tutorial in sandbox vault |
| `prism_cli/completions.py` | Tab-completion for commands, UUIDs, types, tags, paths |
| `tests/__init__.py` | Test package |
| `tests/test_main.py` | CLI main entry point tests |
| `tests/test_commands.py` | Command implementation tests |
| `tests/test_repl.py` | REPL tests |
| `tests/test_tutor.py` | Tutor tests |
| `tests/test_completions.py` | Completion provider tests |

## 📋 openspec/ — Specification system

| Entry | Description |
|-------|-------------|
| `config.yaml` | OpenSpec configuration |
| `specs/blob-storage/spec.md` | Blob storage capability spec |
| `specs/change-tracking/spec.md` | Change tracking capability spec |
| `specs/command-core/spec.md` | Command core capability spec |
| `specs/metadata-graph/spec.md` | Metadata and graph capability spec |
| `specs/node-management/spec.md` | Node management capability spec |
| `specs/onboarding/spec.md` | Onboarding/tutorial capability spec |
| `specs/path-tags/spec.md` | Path and tags capability spec |
| `specs/query-search/spec.md` | Query and search capability spec |
| `specs/repl-interface/spec.md` | REPL interface capability spec |
| `specs/tag-management/spec.md` | Tag management capability spec |
| `specs/testing/spec.md` | Testing capability spec |
| `specs/type-system/spec.md` | Type system capability spec |
| `specs/vault-lifecycle/spec.md` | Vault lifecycle capability spec |

## 🔧 .opencode/ — OpenCode configuration

| Entry | Description |
|-------|-------------|
| `commands/opsx-apply.md` | Apply command docs |
| `commands/opsx-archive.md` | Archive command docs |
| `commands/opsx-explore.md` | Explore mode command docs |
| `commands/opsx-propose.md` | Propose command docs |
| `skills/openspec-apply-change/SKILL.md` | Apply-change skill |
| `skills/openspec-archive-change/SKILL.md` | Archive-change skill |
| `skills/openspec-explore/SKILL.md` | Explore skill |
| `skills/openspec-propose/SKILL.md` | Propose skill |

## 📚 Related Documents

| Document | Description |
|----------|-------------|
| `ARCHITECTURE.md` | System architecture, data flow, design decisions |
| `prism-core/AGENTS.md` | Library package agent guide |
| `prism-cli/AGENTS.md` | CLI package agent guide |
