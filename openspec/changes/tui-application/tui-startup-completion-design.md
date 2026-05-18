## Context

The TUI startup screen (`StartupScreen` in `prism-tui/prism_tui/startup_screen.py`) has a path input for specifying the vault location and two buttons: "Open Existing Vault" and "Initialize New Vault". Two UX issues exist:

1. **No TAB completion**: Typing `/tm` and pressing TAB does nothing — TAB just cycles focus between widgets. Users want shell-like filesystem path completion.
2. **No ENTER-to-submit**: Pressing ENTER in the path input does nothing. Users must TAB to a button and press ENTER again. ENTER should auto-detect whether to open or init.

## Goals / Non-Goals

**Goals:**
- TAB on path input shows filesystem completion with dropdown popup (like zsh)
- ENTER on path input auto-detects open vs init based on vault existence
- Completion is reusable for other TUI path inputs in the future

**Non-Goals:**
- Vault-path completion (inside prism partitions) — only filesystem paths for now
- Completion for non-path TUI inputs (tags, UUIDs, etc.)
- Replacing Textual's default TAB focus-cycling in other contexts

## Decisions

### D1: Reusable `PathInput` widget

A new `PathInput` widget in `prism-tui/prism_tui/widgets/path_input.py` extends Textual's `Input` with filesystem TAB completion. It uses a pluggable completion strategy interface so vault-path completion can be added later without changing the widget.

### D2: TAB-triggered completion via `on_key` interception

TAB key is intercepted in `PathInput.on_key`. When the input has text and TAB is pressed:
- Parse the current value into directory + prefix
- List directory entries with `os.listdir()`, filter by prefix match
- Single match → complete inline (trailing `/` for directories)
- Multiple matches → show a positioned popup with matches
- Tab / Enter in popup selects highlighted item
- Escape dismisses popup

This avoids breaking Textual's normal TAB focus-cycling when the input is empty.

### D3: Completion popup styled as a `ListView`

The popup is a Textual `ListView` mounted as a child of `PathInput`, positioned below the input. It reuses Textual's built-in widget rendering and key handling. The popup is unmounted when dismissed.

### D4: ENTER auto-detection in `StartupScreen`

`on_input_submitted` handler in `StartupScreen`:
- Empty path → use default: `~/.local/share/prism/vaults/default`
- Path exists and is a prism vault → `Vault.open(path)`
- Path doesn't exist → `Vault.init(path)`
- Path exists but not a vault → notify error

### D5: Completion strategy interface

```python
class PathCompleter(Protocol):
    def complete(self, partial: str) -> list[str]: ...
```

Filesystem completer is the default. Vault-path completer can be added later.

## Risks / Trade-offs

- [OS] `os.listdir()` on permission-denied directories will raise → wrapped in try/except, swallow + empty result
- [Edge case] Paths with spaces or special chars → displayed as-is, input value is the raw path string
- [Performance] Listing directories on network mounts could lag → acceptable for an interactive input; runs synchronously on TAB press
- [Complexity] Popup widget lifecycle (mount/unmount, focus management) → encapsulated in `PathInput`, tested via Textual Pilot

## Open Questions

- OQ1: Should `~` expansion happen on TAB or on submit?
  - Answer: on TAB — `~/doc` should complete to `/home/user/documents/`
- OQ2: Should hidden files (dotfiles) be included in completion?
  - Answer: no — only show hidden entries if the prefix starts with `.`
