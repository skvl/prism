## Why

The current Prism interfaces (CLI and REPL) are text-in/text-out — no persistent layout, no column browsing, no graph visualization, no structured query builder. Adding a TUI (Textual-based) application provides a rich, persistent, keyboard-driven interface that matches how people naturally explore and manage a PKM: browsing paths, scanning nodes, previewing content, and visually navigating the graph.

## What Changes

- **New `prism-tui` package** with Textual-based TUI application
- **Bridge command** `prism tui` in prism-cli that launches the TUI
- **4-tab interface**: Column Browser, Graph View, Tag Cloud, Query Builder
- **Modal navigation** (ranger-style) with `j/k/h/l`, `gg`/`G`, `t`/`T` filters in browser
- **Command bar** (MC-style) with `F1`–`F8` action buttons
- **Command mode** (`:`) with inline fast-path and wizard dialogs
- **Cross-tab navigation**: Query Builder, Tag Cloud, Graph switch to Browser and select node
- **Vault connection**: `--vault` argument or init/open screen on startup
- **TUI calls prism-core directly** (not through prism-cli's commands.py)

## Capabilities

### New Capabilities
- `tui-shell`: App lifecycle, tab management, command bar, command mode, vault connection, cross-tab navigation
- `tui-column-browser`: Three-column browser (paths, nodes, preview) with modal navigation and filtering
- `tui-graph-view`: Force-directed graph visualization on Textual Canvas, with list fallback for dense graphs
- `tui-tag-cloud`: Tag cloud tab with frequency-weighted display and filter interaction
- `tui-query-builder`: Structured query builder with type picker, tag select, text input, AND/OR/NOT toggles, results list

### Modified Capabilities

- `command-core`: Add bridge entry `prism tui` that shells out to prism-tui (the TUI itself calls prism-core directly)

## Impact

- **New package**: `prism-tui/` at project root with `pyproject.toml`, tests, and AGENTS.md
- **New dependency**: `textual>=1.0` (added to prism-tui's optional deps, not prism-core)
- **Modified package**: `prism-cli` gets one new command (`tui`) that is a thin bridge
- **prism-core**: No changes — the TUI uses existing APIs directly
- **On-disk**: No changes to vault format, storage layout, or metadata
