# Graph Tab: Full Node Titles with Pan/Zoom

## Problem

The Graph tab's ASCII force-directed visualization truncates node titles based on the node's x-position on the 80-wide canvas. A node at x=70 gets only ~9 characters; a node at x=76 gets the minimum of 4 characters. This makes titles unreadable for nodes positioned near the right edge of the canvas.

The `_pan_x`, `_pan_y`, and `_zoom` fields exist in `GraphTab` but are dead code — never wired into the rendering pipeline.

## Design

### 1. No title truncation

Remove the `[:avail]` slicing in `ForceDirectedLayout.render_ascii()`. Render each node's full title at its (ix, iy) position, extending rightward at full length. No character limit regardless of the node's position.

### 2. Dynamic canvas sizing

After the force-directed layout settles, compute the logical canvas dimensions from content:

- `canvas_width = max(ix + len(title_marker) + 2)` over all nodes
- `canvas_height = max(iy + 2)` over all nodes

If computed dimensions are smaller than the viewport, pad to viewport size. The viewport is queried from the Textual widget's actual dimensions.

### 3. Functional pan/zoom

Wire the existing `_pan_x`, `_pan_y`, `_zoom` fields into the rendering pipeline:

- **Arrow keys** (left/right/up/down): adjust `_pan_x`/`_pan_y` by ±5px per press
- **`+`/`=`** and **`-`** keys: adjust `_zoom` in the range [0.5, 3.0] at 0.2 increments
- **Clamping**: pan stops at canvas edges (cannot scroll past content boundary)
- **Inert when content fits**: if the logical canvas fits entirely within the viewport, pan controls are a no-op

Zoom scales the mapping between logical canvas cells and display characters:
- 1.0x: 1:1 mapping
- 0.5x: 2 logical cells → 1 display char (shrink)
- 2.0x: 1 logical cell → 2 display chars (expand)

### 4. Edge cases

- **Empty graph / all nodes filtered out**: Show "No graph data" (existing behavior, unchanged)
- **Canvas smaller than viewport**: Center content, pan is inert
- **List view fallback**: Unchanged — >50 visible nodes still falls back to list with full titles
- **Single node**: Rendered with full title, no special handling needed

### 5. Files changed

- `prism-tui/prism_tui/tabs/graph.py` — `ForceDirectedLayout.render_ascii()` and `GraphTab` pan/zoom wiring
- `prism-tui/tests/test_layout.py` — Update tests to reflect no-truncation behavior

### 6. Out of scope

- Click/hover interaction with ASCII nodes (would require a different rendering approach)
- The existing spec's "Tooltip on hover" requirement (not feasible with ASCII rendering)
- Force-directed layout algorithm changes
- Type filter changes
