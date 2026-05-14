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

# Create a path hierarchy
prism path create /projects/meeting-notes

# View path tree
prism path tree

# Create a node at a path
prism new note "Q1 Planning" --add-path /projects/meeting-notes

# Remove a path
prism path rm /projects/meeting-notes
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
| `prism path create <path>` | Create path segments (mkdir -p) |
| `prism path rm <path>` | Remove a path and its subtree |
| `prism path tree [path]` | Display path hierarchy as a tree |
| `prism query <query>` | Search nodes |
| `prism status` | Show vault status |
| `prism verify <uuid>` | Verify blob integrity |
| `prism repl` | Launch an interactive REPL session |

## REPL Mode

Launch an interactive REPL session for a persistent, stateful experience:

```bash
# Inside a vault directory
prism repl

# With an explicit vault path
prism repl --vault ~/my-vault
```

The REPL provides:

- **Aliases** — shorter command names (`n` for `new`, `s` for `show`, `q` for `query`, `l` for `link`, etc.)
- **Tab completion** — complete commands, UUIDs, type names, and tags
- **Session state** — the last created/modified UUID is stored as `_` (e.g., `show _`)
- **Command history** — persistent across sessions (saved to `~/.prism_repl_history`)
- **Degraded mode** — outside a vault, only `init`, `open`, `help`, and `exit` are available

### REPL Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `init` | | Initialize a new vault |
| `open` | | Open an existing vault |
| `new` | `n` | Create a new typed node |
| `show` | `s` | Display node details |
| `edit` | `e` | Edit a node |
| `rm` | | Delete a node |
| `query` | `q` | Search nodes |
| `link` | `l` | Create a directed link |
| `backlinks` | `bl` | Show backlinks |
| `graph` | `g` | Export the node graph |
| `status` | `st` | Show vault status |
| `add-file` | `af` | Import a file |
| `verify` | `v` | Verify blob integrity |
| `history` | | Show command history |
| `help` | | Show help and aliases |
| `exit` / `quit` | | Exit the REPL |

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
- **Path** — Virtual filesystem segment with `path-parent` links

## Path Hierarchy

Prism supports a virtual filesystem hierarchy for organizing nodes. Paths are first-class nodes with CRUD via `prism path` subcommands, supporting tagging, linking, and querying like any other node.

- **Create** — `prism path create /projects/notes` creates segments recursively (mkdir -p semantics)
- **Associate** — `prism new note "Title" --add-path /projects/notes` or `prism edit <uuid> --add-path /projects/notes`
- **Remove association** — `prism edit <uuid> --remove-path /projects/notes` (path node itself is not deleted)
- **Browse** — `prism path tree` shows the full hierarchy; `prism path tree /projects` shows a subtree
- **Delete** — `prism path rm /projects` removes the segment and all descendants, cleaning up node references
- **Multiple paths** — a node can belong to many paths; querying any path returns it

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
