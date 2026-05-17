## Context

Prism currently has two interfaces: a Click-based CLI (`prism <command>`) and a readline-based REPL (`prism repl`). Both are stateless, single-shot interactions — no persistent layout, no graphical rendering, no multi-panel browsing. The prism-core library exposes all PKM operations (node CRUD, query, graph, tags, paths) via direct Python API calls.

The TUI adds a third interface: a persistent Textual-based application that provides rich, keyboard-driven interaction. It calls prism-core directly, bypassing prism-cli's `commands.py` (which wraps core calls in `CmdResult` for Click compatibility). The existing CLI and REPL remain unchanged.

## Goals / Non-Goals

**Goals:**
- Provide a Textual-based TUI application with 4 tabs: Column Browser, Graph View, Tag Cloud, Query Builder
- Modal navigation (ranger-style `j/k/h/l`) in the browser tab with MC-style command bar (`F1`–`F8`)
- Command mode (`:`) with both inline fast-path and wizard dialogs
- Cross-tab navigation: non-browser tabs can select a node and switch to browser tab
- Vault connection via `--vault` argument or init/open screen on startup
- Thin bridge command `prism tui` in prism-cli that launches prism-tui
- TUI calls prism-core directly, no dependency on prism-cli

**Non-Goals:**
- Replacing the CLI or REPL — all three interfaces coexist
- In-app editing of node bodies (launches $EDITOR externally)
- Real-time collaboration or multi-user features
- Mobile or web interface
- Persisting TUI state between sessions (no session save/restore)
- Custom themes beyond Textual's built-in theming

## Decisions

### D1: Textual as TUI framework

Textual provides widget composition, CSS styling, async event loop, built-in Canvas widget, and active maintenance — all from the same team as Rich (already in the dependency tree). Alternatives considered: prompt_toolkit (better for REPLs than full TUIs), Urwid (mature but no CSS, smaller ecosystem), raw curses (too much work).

### D2: Column browser as composite VerticalScroll layout

Three `VerticalScroll` containers inside a `Horizontal` — no custom rendering needed. Textual's `Tree` widget handles the path hierarchy, `ListView` handles the node list, `Markdown` handles preview. Cross-column coordination via Textual's message/event system.

### D3: Graph view uses Textual Canvas with basic force-directed layout

Force-directed layout implemented as a ~100-line pure-Python physics simulation (spring force + repulsion) rather than depending on networkx. The Canvas widget draws edges with lines and nodes with Unicode half-block characters. For graphs exceeding a density threshold (> N nodes on screen), fall back to a flat list view. Pan via arrow keys, zoom via +/-.

### D4: Modal navigation implemented via key method overrides on the browser composite

Each column subclass overrides `key_j`, `key_k`, `key_h`, `key_l` etc. The browser container manages which column is active and routes keys accordingly. This avoids a global mode flag and keeps key handling colocated with widget logic. Command mode (`:`) is a separate `Input` widget at the bottom that takes focus when `:` is pressed.

### D5: Wizards as ModalScreen with form widgets

Textual's `ModalScreen` provides a built-in modal overlay pattern. Each wizard (New Node, Link Nodes, etc.) is a separate Screen subclass with `Input`, `Select`, `Button`, and custom widgets. Inline fast-path (`:new note "Title" --tag work`) bypasses the wizard and creates directly.

### D6: Cross-tab navigation via message passing

When a non-browser tab discovers a node (e.g., user clicks a tag in the cloud, or a result in query builder), it posts a custom `SelectNode` message to the app. The app switches to the browser tab and loads that node. This keeps tabs decoupled — they only know about their own state + the message protocol.

### D7: `prism tui` bridge uses `sys.executable` to launch prism-tui

The bridge in prism-cli's `main.py` runs `subprocess.run([sys.executable, "-m", "prism_tui", ...])` with the vault path forwarded. This keeps prism-cli's dependency footprint unchanged (no textual needed in prism-cli) and allows prism-tui to be installed independently. The TUI process inherits the parent's terminal.

### D8: TUI calls prism-core directly

The TUI imports `prism.vault.vault.Vault`, `prism.node.manager.NodeManager`, etc. directly. This avoids the `CmdResult` serialization layer and gives the TUI direct access to core types and methods. Any exception from prism-core propagates to the TUI's error handler, which displays it in a notification widget.

## Risks / Trade-offs

- [Complexity] Column browser with modal navigation + command bar + wizards creates a non-trivial state machine → Mitigation: encapsulate state per-widget, avoid global mode flags
- [Performance] Force-directed layout on graphs with 100+ nodes may lag at startup → Mitigation: cap initial render, allow progressive layout via animation frames; fallback to list view
- [Dependency] Textual is a heavy dependency (~8MB installed) → Acceptable: it's optional (only prism-tui needs it), and it provides substantial value
- [Cross-tab] Decoupled message passing can make data flow hard to trace → Mitigation: define a small set of message types in a single module, document the message flow
- [Testing] Textual's testing framework (via `pilot`) requires async pytest and has quirks with modal screens → Acceptable: it's functional and well-documented; complex interactions can be extracted as pure functions
- [Terminal compatibility] Textual requires a modern terminal emulator (xterm-256color, kitty, alacritty, iTerm2, Windows Terminal) → Acceptable: this is increasingly standard; we document the requirement

## Open Questions

- OQ1: Should the graph view support interactive node repositioning (drag with mouse)?
  - Answer: no
- OQ2: Should the tag cloud show co-occurrence (two tags used together)?
  - Answer: yes
- OQ3: Should the query builder remember recent queries across sessions?
  - Answer: no
- OQ4: Should the command bar labels change based on which column has focus (context-sensitive)?
  - Answer: yes
