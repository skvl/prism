## 1. REPL Module

- [x] 1.1 Create `prism_cli/repl.py` with `Repl` class and main loop
- [x] 1.2 Implement command dispatch with alias resolution
- [x] 1.3 Implement session state (`last_uuid`, vault tracking)
- [x] 1.4 Implement degraded mode (restricted commands outside vault)
- [x] 1.5 Implement `help` command (list commands/aliases)
- [x] 1.6 Implement `init`/`open` from inside REPL to transition to full mode
- [x] 1.7 Implement `_` → last_uuid substitution in arguments

## 2. Tab Completion

- [x] 2.1 Configure readline with custom completer function
- [x] 2.2 Implement command/alias completion at position 0
- [x] 2.3 Implement UUID completion from `list_nodes()`
- [x] 2.4 Implement type name completion from `TypeLoader`
- [x] 2.5 Implement tag completion from node metadata

## 3. History

- [x] 3.1 Configure readline history file path (`~/.prism_repl_history`)
- [x] 3.2 Implement save on exit via `readline.write_history_file()`
- [x] 3.3 Implement restore on start via `readline.read_history_file()`
- [x] 3.4 Implement `history` command with numbered listing

## 4. CLI Integration

- [x] 4.1 Add `repl` command to `main.py` with `--vault` option
- [x] 4.2 Wire vault context detection for REPL launch
- [x] 4.3 Handle unsupported commands (e.g., `tutor`) with warning

## 5. Tests

- [x] 5.1 Write test: REPL launches in degraded mode outside vault
- [x] 5.2 Write test: REPL connects to vault when inside vault directory
- [x] 5.3 Write test: aliases dispatch to correct commands
- [x] 5.4 Write test: `_` resolves to last UUID
- [x] 5.5 Write test: `init` from inside REPL transitions to full mode
- [x] 5.6 Write test: unsupported command shows warning
- [x] 5.7 Write test: `exit`/`quit`/Ctrl+D exit the REPL
- [x] 5.8 Write test: tab completion returns valid completions

## 6. Documentation

- [x] 6.1 Update README with REPL usage section
