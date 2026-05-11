# Prism

A local-first, single-user PKM (Personal Knowledge Manager) built on a content-addressed blob store with a typed node graph.

## Installation

```bash
pip install prism-cli
```

Or with pipx:

```bash
pipx install prism-cli
```

## Quick Start

```bash
# Initialize a vault
prism init ~/my-vault

# Create a note
prism new note "Meeting Notes" --tag work

# Import a file
prism add ~/Documents/report.pdf

# Create a contact
prism new contact --name "Alice" --email alice@example.com

# Query nodes
prism query "tag:work"
prism query "type:note AND tag:meeting"
prism query "budget" --format json

# Show node details
prism show <uuid>

# Link nodes
prism link <source-uuid> <target-uuid>

# Show backlinks
prism backlinks <uuid>

# Export graph
prism graph --format dot
prism graph --format json

# Check vault status
prism status

# Verify blob integrity
prism verify <uuid>
```

## Commands

| Command | Description |
|---------|-------------|
| `prism init` | Initialize a new vault |
| `prism vault add` | Register an existing vault |
| `prism vault list` | List registered vaults |
| `prism new <type>` | Create a new typed node |
| `prism add <path>` | Import a file |
| `prism edit <uuid>` | Edit a node |
| `prism rm <uuid>` | Delete a node |
| `prism show <uuid>` | Display node details |
| `prism link <src> <tgt>` | Create a link |
| `prism backlinks <uuid>` | Show backlinks |
| `prism graph` | Export the node graph |
| `prism query <query>` | Search nodes |
| `prism status` | Show vault status |
| `prism verify <uuid>` | Verify blob integrity |

## Architecture

Prism organizes content into **vaults** — self-contained directories with:

- `.storage/` — Content-addressed blob store (UUID-partitioned)
- `.metadata/` — Node metadata, type schemas, and index
- `.metadata/types/` — TOML-based type definitions
- `.metadata/vault.toml` — Vault identity and configuration

Nodes are typed objects (notes, contacts, bookmarks, files) stored as UUID-partitioned directories containing `metadata.toml` and optionally `data.*` for blob content.

### Built-in Types

- **Note** — Markdown body with `[[uuid]]` link support
- **Contact** — Structured fields (name, email, phone, org)
- **Bookmark** — URL with title and tags
- **File** — Binary blob with SHA-256 integrity

## Type System

Extend Prism by adding `.toml` files to `.metadata/types/`:

```toml
name = "movie"
icon = "🎬"
body_model = "null"

[[fields]]
name = "title"
type = "string"
required = true

[[fields]]
name = "year"
type = "number"
required = false
```
