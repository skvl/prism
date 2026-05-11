## Why

Prism's CLI requires typing `prism <command> [args]` for every operation, which becomes tedious during extended use. Users who create multiple nodes, run several queries, or browse their vault in a session constantly repeat the tool prefix, retype UUIDs, and lose context between commands. A REPL mode eliminates these friction points by providing a persistent, stateful session with shorter aliases, tab completion, and command history.

## What Changes

- **New `prism repl` command** — launches an interactive REPL session connected to a vault
- **Aliases** for all common commands (`n` for `new`, `s` for `show`, `q` for `query`, etc.)
- **Tab completion** for commands, aliases, UUIDs, type names, and tags
- **Session state** — REPL remembers the last created/modified UUID as `_`
- **Persistent command history** across sessions (readline history file)
- **Degraded mode** — REPL started outside a vault only allows `init`, `open`, and `help`
- **Scrollback** by not clearing screen between commands
- Updates to README and added tests for the REPL mode

## Capabilities

### New Capabilities
- `repl-interface`: Interactive REPL mode for the CLI with aliases, tab completion, session state, and persistent history

### Modified Capabilities
None — this is an addition, not a change to existing behavior.

## Impact

- **New dependency**: Python stdlib `readline` (GPL on Linux, already pre-installed)
- **Affected package**: `prism-cli` — new command added to `main.py`, new module for the REPL
- **No changes** to `prism-core` or any existing command behavior
- **Tests**: New test file for REPL functionality in `prism-core/tests/`
- **Docs**: README updated with REPL usage examples
