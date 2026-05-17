## 1. Package scaffolding and bridge

- [x] 1.1 Create `prism-tui/pyproject.toml` with textual dependency, entry point `prism_tui.__main__`
- [x] 1.2 Create `prism-tui/prism_tui/__init__.py` and `__main__.py` with `python -m prism_tui` entry
- [x] 1.3 Create `prism-tui/prism_tui/app.py` with Textual `App` subclass and tab container
- [x] 1.4 Add `prism tui` bridge command to `prism-cli/prism_cli/main.py` using `subprocess.run`
- [x] 1.5 Install prism-tui in editable mode in the project's virtual environment

## 2. Vault connection and startup screen

- [x] 2.1 Implement vault connection logic: try `--vault` argument, fall back to context detection
- [x] 2.2 Implement startup screen with "Initialize new vault" and "Open existing vault" options
- [x] 2.3 Wire vault init/open actions to prism-core `Vault.init()` / `Vault.open()`
- [x] 2.4 Store vault reference in app-level state for tab access

## 3. Column browser tab

- [x] 3.1 Create `prism-tui/prism_tui/tabs/browser.py` with three-column `Horizontal` layout
- [x] 3.2 Implement Path column using Textual `Tree` widget, populate from vault path hierarchy
- [x] 3.3 Implement Node List column using `ListView`, populate nodes at selected path
- [x] 3.4 Implement Preview column using `Markdown` widget with rendered node body
- [x] 3.5 Wire cross-column coordination: path selection → node list update, node selection → preview update
- [x] 3.6 Implement modal navigation: `j`/`k` per column, `h`/`l` between columns, `gg`/`G`
- [x] 3.7 Implement `t` tag filter overlay and `T` type filter overlay
- [x] 3.8 Implement `e` to launch `$EDITOR` with node body file, detect changes on exit
- [x] 3.9 Display node metadata (type, tags, dates) and backlinks count in preview
- [x] 3.10 Render `[[uuid]]` links in preview as highlighted, clickable references
- [x] 3.11 Implement `r` refresh action to reload vault state

## 4. Command bar

- [x] 4.1 Create fixed bottom bar widget with 8 action buttons labeled `F1`–`F8`
- [x] 4.2 Wire context-sensitive labels: change actions based on active tab and focused column
- [x] 4.3 Handle both F-key and number-key activation of actions
- [x] 4.4 Default actions: Help, New, Edit, Link, Tag, Delete, Refresh, Menu

## 5. Command mode and wizards

- [x] 5.1 Implement `:` key capture to show Input widget with `: ` prefix
- [x] 5.2 Implement command dispatch: parse input, route to handler or open wizard
- [x] 5.3 Implement tab completion for commands, UUIDs, types, tags, paths in command Input
- [x] 5.4 Implement `Esc` to exit command mode without executing
- [x] 5.5 Create `NewNodeWizard` modal with type dropdown, title input, tag selector, path browse
- [x] 5.6 Create `LinkNodesWizard` modal with source/target UUID inputs and validation
- [x] 5.7 Create `TagManageWizard` modal for add/remove/rename operations
- [x] 5.8 Support inline fast-path: `:new note "Title" --tag work` bypasses wizard

## 6. Graph view tab

- [x] 6.1 Create `prism-tui/prism_tui/tabs/graph.py` with Canvas widget
- [x] 6.2 Implement basic force-directed layout algorithm (spring + repulsion)
- [x] 6.3 Render nodes as labeled boxes colored by type on Canvas
- [x] 6.4 Render edges with arrowheads between connected nodes
- [x] 6.5 Implement node selection with emphasis/dim effect
- [x] 6.6 Implement pan (arrow keys) and zoom (+/-)
- [x] 6.7 Implement dense graph fallback: switch to flat list view when >50 nodes
- [x] 6.8 Implement type filter for graph (`t` key)
- [x] 6.9 Implement cross-tab navigation: `Enter` on node → switch to browser tab
- [x] 6.10 Implement hover tooltip with node details

## 7. Tag cloud tab

- [x] 7.1 Create `prism-tui/prism_tui/tabs/tag_cloud.py`
- [x] 7.2 Load all tags with node counts from vault
- [x] 7.3 Display tags sized by frequency using styled Button or Static widgets
- [x] 7.4 Implement single-click selection with node list below cloud
- [x] 7.5 Implement multi-tag AND selection
- [x] 7.6 Implement co-occurrence highlighting for related tags
- [x] 7.7 Implement cross-tab navigation: click node result → switch to browser tab
- [x] 7.8 Implement `Esc` or "Clear" button to reset selection

## 8. Query builder tab

- [x] 8.1 Create `prism-tui/prism_tui/tabs/query_builder.py`
- [x] 8.2 Implement type picker (`Select` dropdown)
- [x] 8.3 Implement multi-select tag selector widget
- [x] 8.4 Implement text search input field
- [x] 8.5 Implement AND/OR/NOT toggle buttons
- [x] 8.6 Wire prism-core query engine: build `QueryAST` from form state, execute
- [x] 8.7 Display results in a table with columns: type, title, tags, updated date
- [x] 8.8 Show result count above results table
- [x] 8.9 Implement auto-search on form change (debounced)
- [x] 8.10 Implement recent query history (in-memory, per session)
- [x] 8.11 Implement cross-tab navigation: select result → switch to browser tab

## 9. Notifications and error handling

- [x] 9.1 Create notification widget (non-blocking, auto-dismiss)
- [x] 9.2 Wire error display from prism-core exceptions
- [x] 9.3 Wire success notifications for create/edit/delete operations
- [x] 9.4 Implement keyboard quit: `q` or `Ctrl+C` exits the TUI

## 10. Testing

- [x] 10.1 Write tests for force-directed layout as pure function
- [x] 10.2 Write tests for command dispatch logic
- [x] 10.3 Write tests for startup screen vault connection flow
- [x] 10.4 Write Textual pilot tests for tab switching and basic column browser interaction
- [x] 10.5 Write tests for query builder form-to-AST conversion
- [x] 10.6 Write tests for tag cloud filtering logic
- [x] 10.7 Write bridge command test in prism-cli tests
