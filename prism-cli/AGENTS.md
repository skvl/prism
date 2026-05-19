# prism-cli — Agent Guide

## Command Reference

| Command | Description |
|---------|-------------|
| `prism init <path>` | Initialize a new vault |
| `prism add-file <path> [--type]` | Import a file into the vault |
| `prism new <type> [title] [--tag] [--add-path]` | Create a new typed node |
| `prism show <uuid>` | Display node details |
| `prism edit <uuid> [--add-path] [--remove-path]` | Edit node body or fields |
| `prism rm <uuid>` | Delete a node |
| `prism link <source> <target>` | Create a directed link |
| `prism backlinks <uuid>` | Show nodes linking to the given UUID |
| `prism graph [--format dot\|json] [--include-paths]` | Export the node graph |
| `prism query <query>` | Search nodes by tags, type, and text |
| `prism status` | Show vault status (changed/new/orphaned) |
| `prism verify <uuid>` | Verify blob SHA-256 integrity |
| `prism tag add <uuid> <tag> [<tag>...]` | Add tags to a node |
| `prism tag rm <uuid> <tag> [<tag>...]` | Remove tags from a node |
| `prism tag list [--count]` | List all unique tags |
| `prism tag rename <old> <new>` | Rename a tag across all nodes |
| `prism path create <path>` | Create a path segment hierarchy |
| `prism path rm <path>` | Remove a path segment and subtree |
| `prism path tree [<path>]` | Display path hierarchy as a tree |
| `prism vault add <path>` | Register an existing vault |
| `prism vault list` | List registered vaults |
| `prism tutor [--lesson N]` | Launch interactive tutorial |
| `prism repl [--vault <path>]` | Launch interactive REPL |

## Click Wiring Patterns

- A top-level `@click.group()` called `cli` in `main.py` with global `--vault`, `--verbose`, `--format` options
- Commands are functions decorated with `@cli.command()` (flat) or `@cli.group()` + subcommands (nested for `vault`, `tag`, `path`)
- `@click.pass_context` is used on every command/group to access `ctx.obj["vault"]` and `ctx.obj["format"]`
- The `new` command uses `context_settings=dict(ignore_unknown_options=True, allow_extra_args=True)` to forward `--field=value` extras
- Error handling pattern: check vault, call command function, check `result.ok`, echo error + `sys.exit(1)` on failure
- `CmdResult` dataclass (`ok`, `error`, `code`, `data`) is the return type for all command functions in `commands.py`
- Output format follows `--format table|json` option propagated through context

## REPL Architecture

The REPL (`repl.py`) provides an interactive shell wrapping the CLI commands:

- **`Repl` class**: maintains `vault` reference, `last_uuid` for `_` shorthand, custom I/O via `input_stream`/`output_stream` (testable)
- **Degraded mode**: commands `init`, `open`, `help`, `exit`, `quit`, `history` work without a vault — all others print "No vault connected"
- **Aliases**: `n→new`, `s→show`, `q→query`, `l→link`, `bl→backlinks`, `g→graph`, `st→status`, `e→edit`, `af→add-file`, `v→verify`
- **Dispatch table**: maps command names to `_cmd_*` methods on the `Repl` class
- **History**: persisted to `~/.prism_repl_history` (max 1000 entries) via `readline`
- **Completion**: integrates with `completions.py` to provide tab-completion for commands, UUIDs, type names, tags, and paths
- **Underscore shorthand**: `_` in arguments resolves to `last_uuid` (set by `new`, `link`, `edit`, `add-file` commands)

Unsupported in REPL: `tutor` (must run from shell as `prism tutor`).

## Tutor System

The tutor (`tutor.py`) provides a guided interactive tutorial:

- **8 lessons** covering vault init, nodes, types, links, queries, file import, tags, and change tracking
- Each lesson has multiple `Step`s with a concept explanation, command to run, and verification callback
- **`Tutor` class**: creates a temp vault sandbox, walks through lessons, verifies each step, offers retry on failure
- **Verification**: each step has a `Callable[[Vault], bool]` that checks the expected state (node count, tag presence, link existence, etc.)
- **Auto-run**: pressing ENTER at a step prompt automatically runs the correct command
- Lessons can be resumed from any lesson number via `prism tutor --lesson N`
- Uses `subprocess.run` to execute `prism` commands with `sys.executable -m prism_cli.main`
- Temporary vault is cleaned up unless the user opts to keep it

