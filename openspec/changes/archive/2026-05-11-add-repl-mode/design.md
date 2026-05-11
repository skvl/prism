## Context

Prism's CLI currently follows a pure command-per-invocation model: each `prism <command>` call is a fresh process. There's no way to maintain state across commands, no tab completion, and every command requires the `prism` prefix. The `tutor` command already demonstrates an interactive pattern but is a guided walkthrough, not a general-purpose REPL.

The REPL will live entirely in `prism-cli` — no changes to `prism-core`. It wraps existing library calls with session management, tab completion, and history.

## Goals / Non-Goals

**Goals:**
- Persistent REPL session with command history across sessions
- Tab completion for commands, aliases, UUIDs, type names, and tags
- Aliases for all commands to reduce typing (`n` → `new`, `s` → `show`, etc.)
- Session state remembering the last created/modified UUID as `_`
- Degraded mode: REPL outside a vault allows only `init`, `open`, `help`, `exit`
- `init` and `open` available from inside the REPL to bind/resolve a vault
- History persistence via readline history file

**Non-Goals:**
- Custom syntax or query language for the REPL (uses same CLI argument format)
- Syntax highlighting or multi-line editing
- Graphical/TUI mode (this is a line-based REPL)
- Replacing existing CLI commands or changing their behavior

## Decisions

### REPL loop: manual `while True` over `cmd.Cmd`

`cmd.Cmd` is Python's stdlib REPL framework. It's tempting but awkward here because:
- Tab completion in `cmd.Cmd` is per-command (`complete_<name>` methods), but we want completion context-aware (commands at position 0, UUIDs/types/tags at other positions)
- Aliases are cumbersome — each alias needs its own `do_<alias>` or routing logic
- A manual loop with readline gives full control over prompt, dispatch, and error handling

**Chosen**: `while True` with `input()` + `readline` configuration.

### Alias strategy: dict-based dispatch

```
ALIASES = {
    "n": "new", "s": "show", "q": "query", "l": "link",
    "bl": "backlinks", "g": "graph", "st": "status",
    "e": "edit", "af": "add-file", "v": "verify",
}
```

The first word of each input line is resolved through the alias map before dispatch. Full command names also work directly.

### Session state: simple dict on the REPL object

```
class ReplSession:
    vault: Optional[Vault]
    last_uuid: Optional[str]      # `_` in commands
    history_file: str             # ~/.prism_repl_history
```

When a command that creates or modifies a node succeeds, its UUID is captured as `last_uuid`. Users reference it with `_` in subsequent commands (e.g., `show _`, `link _ <other>`).

### Tab completion: single readline completer

A single `complete(text, state)` function registered with `readline.set_completer()`. It attempts completion in order:
1. Commands and aliases (if at position 0)
2. UUIDs from `list_nodes()` (if not at position 0)
3. Type names from `TypeLoader`
4. Tags from scanning node metadata

Using `readline.parse_and_bind("tab: complete")` for Tab key binding.

### History: readline history file

- File location: `~/.prism_repl_history`
- Saved on session exit via `readline.write_history_file()`
- Restored on session start via `readline.read_history_file()`
- Default max history length: 1000 entries
- `history` command lists past commands with line numbers

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **readline is GPL on Linux** | The project must be GPL-compatible. Readline is pre-installed on virtually every Linux system, so no distribution issue. The `cmd` module also uses readline internally. |
| **Readline on Windows** | Python's readline may use `pyreadline` or not be available. REPL degrades to no completion on Windows. |
| **History file stores vault paths/UUIDs** | Stored in user home dir with 600 permissions. No sensitive data (no passwords, no content). |
| **Tab completion performance on large vaults** | UUID/tag scans iterate `list_nodes()`. For vaults with thousands of nodes, this could lag. Mitigation: cache with `lru_cache` or refresh threshold. |
| **REPL vs existing `input()` calls** | The existing `input()` calls in `add_file` and `status` work inside a CLI process. Inside the REPL, these commands run within the same process, so `input()` still works but needs care to avoid interfering with the REPL loop. |
