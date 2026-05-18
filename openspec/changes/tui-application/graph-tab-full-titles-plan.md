# Graph Tab Full Titles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the Graph tab's ASCII force-directed view to show full node titles (no truncation) with working pan controls.

**Architecture:** `ForceDirectedLayout.render_ascii()` computes a logical canvas sized to fit all full-length labels, then slices a viewport based on pan/zoom state passed from `GraphTab`. The dead `_pan_x`/`_pan_y`/`_zoom` fields in `GraphTab` are wired into the rendering pipeline.

**Tech Stack:** Python 3.11+, Textual, prism-core

---

### Task 1: Remove title truncation and add viewport support in ForceDirectedLayout

**Files:**
- Modify: `prism-tui/prism_tui/tabs/graph.py` (ForceDirectedLayout class)

- [ ] **Step 1.1: Write the failing test for full title rendering**

Add to `prism-tui/tests/test_layout.py`:

```python
def test_render_ascii_shows_full_title() -> None:
    title = "Complete Node Title That Should Not Be Truncated"
    nodes = [_make_node("abc-123", title)]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    output = layout.render_ascii(view_width=80, view_height=40)
    assert title in output
```

- [ ] **Step 1.2: Run test to verify it fails**

Run:
```bash
.venv/bin/python -m pytest prism-tui/tests/test_layout.py::test_render_ascii_shows_full_title -v
```

Expected: FAIL — `title` not in output because current code truncates.

- [ ] **Step 1.3: Modify `render_ascii()` to support viewport and no truncation**

Replace the existing `render_ascii` method with:

```python
def render_ascii(
    self,
    selected: str | None = None,
    view_width: int | None = None,
    view_height: int | None = None,
    pan_x: int = 0,
    pan_y: int = 0,
) -> str:
    max_x = 0
    max_y = 0
    for node in self.node_list:
        uid = node.uuid
        if uid not in self.positions:
            continue
        ix = int(self.positions[uid][0])
        iy = int(self.positions[uid][1])
        label_len = len(node.title or uid) + 1
        if uid == selected:
            label_len += 1
        max_x = max(max_x, ix + label_len)
        max_y = max(max_y, iy + 1)

    logical_w = max(max_x, view_width or max_x)
    logical_h = max(max_y, view_height or max_y)

    canvas: list[list[str]] = [
        [" " for _ in range(logical_w)] for _ in range(logical_h)
    ]

    for link in self.links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        if src in self.positions and tgt in self.positions:
            sx, sy = self.positions[src]
            tx, ty = self.positions[tgt]
            self._draw_line(canvas, int(sx), int(sy), int(tx), int(ty), logical_w, logical_h)

    for node in self.node_list:
        uid = node.uuid
        if uid not in self.positions:
            continue
        ix, iy = int(self.positions[uid][0]), int(self.positions[uid][1])
        label = node.title or uid
        selected_marker = "*" if uid == selected else " "
        for ci, ch in enumerate(f"{selected_marker}{label}"):
            col = ix + ci
            if 0 <= col < logical_w and 0 <= iy < logical_h:
                canvas[iy][col] = ch

    if view_width is not None and view_height is not None:
        pan_x = max(0, min(pan_x, logical_w - view_width))
        pan_y = max(0, min(pan_y, logical_h - view_height))
        lines = []
        for y in range(pan_y, pan_y + view_height):
            if y < logical_h:
                row = "".join(canvas[y][pan_x:pan_x + view_width])
                if len(row) < view_width:
                    row += " " * (view_width - len(row))
                lines.append(row)
            else:
                lines.append(" " * view_width)
        return "\n".join(lines)

    return "\n".join("".join(row) for row in canvas)
```

Also update `_draw_line` to accept logical width/height instead of using `self.width`/`self.height`:

```python
def _draw_line(
    self, canvas: list[list[str]], x0: int, y0: int, x1: int, y1: int,
    logical_w: int, logical_h: int,
) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < logical_w and 0 <= y0 < logical_h:
            if canvas[y0][x0] == " ":
                canvas[y0][x0] = "."
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
```

- [ ] **Step 1.4: Remove unused `color` variable**

Delete line: `color = TYPE_COLORS.get(node.type, "white")` from the render loop (it's assigned but never read).

- [ ] **Step 1.5: Run tests to verify they pass**

Run:
```bash
.venv/bin/python -m pytest prism-tui/tests/test_layout.py -v
```

Expected: all 7 tests PASS (6 existing + 1 new).

- [ ] **Step 1.6: Commit**

```bash
git add prism-tui/prism_tui/tabs/graph.py prism-tui/tests/test_layout.py
git commit -m "fix(tui): render full node titles in graph with viewport support"
```

---

### Task 2: Wire pan/zoom in GraphTab

**Files:**
- Modify: `prism-tui/prism_tui/tabs/graph.py` (GraphTab class)

- [ ] **Step 2.1: Write a test for pan behavior**

Add to `prism-tui/tests/test_layout.py`:

```python
def test_render_ascii_pan_offsets_content() -> None:
    nodes = [_make_node("abc-123", "HelloWorld")]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    full = layout.render_ascii()
    panned = layout.render_ascii(view_width=80, view_height=40, pan_x=20, pan_y=0)
    assert full != panned
```

- [ ] **Step 2.2: Run test to verify it fails**

Run:
```bash
.venv/bin/python -m pytest prism-tui/tests/test_layout.py::test_render_ascii_pan_offsets_content -v
```

Expected: PASS (the viewport support was added in Task 1, so this should already work — confirms the API is correct).

- [ ] **Step 2.3: Modify `_render_canvas()` to pass viewport and pan/zoom**

Replace the existing `_render_canvas` method:

```python
def _render_canvas(self) -> None:
    canvas_widget = self.query_one("#graph-canvas", Static)
    if self._layout is None:
        canvas_widget.update("No graph data")
        return
    view_width = canvas_widget.content_region.width
    view_height = canvas_widget.content_region.height
    ascii_art = self._layout.render_ascii(
        selected=self._selected_uuid,
        view_width=view_width,
        view_height=view_height,
        pan_x=self._pan_x,
        pan_y=self._pan_y,
    )
    canvas_widget.update(ascii_art)
```

- [ ] **Step 2.4: Wire zoom in `render_ascii()`**

The current `render_ascii` already scales the viewport. Add zoom by scaling positions and label lengths before rendering the logical canvas:

```python
def render_ascii(
    self,
    selected: str | None = None,
    view_width: int | None = None,
    view_height: int | None = None,
    pan_x: int = 0,
    pan_y: int = 0,
    zoom: float = 1.0,
) -> str:
    scale = zoom
    max_x = 0
    max_y = 0
    scaled_positions: dict[str, tuple[float, float]] = {}
    for node in self.node_list:
        uid = node.uuid
        if uid not in self.positions:
            continue
        px, py = self.positions[uid]
        sx, sy = px * scale, py * scale
        scaled_positions[uid] = (sx, sy)
        ix, iy = int(sx), int(sy)
        label_len = int(len(node.title or uid) * scale) + 1
        if uid == selected:
            label_len += 1
        max_x = max(max_x, ix + label_len)
        max_y = max(max_y, iy + 1)

    logical_w = max(max_x, view_width or max_x)
    logical_h = max(max_y, view_height or max_y)

    canvas: list[list[str]] = [
        [" " for _ in range(logical_w)] for _ in range(logical_h)
    ]

    for link in self.links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        if src in scaled_positions and tgt in scaled_positions:
            sx, sy = scaled_positions[src]
            tx, ty = scaled_positions[tgt]
            self._draw_line(canvas, int(sx), int(sy), int(tx), int(ty), logical_w, logical_h)

    for node in self.node_list:
        uid = node.uuid
        if uid not in scaled_positions:
            continue
        ix, iy = int(scaled_positions[uid][0]), int(scaled_positions[uid][1])
        label = node.title or uid
        selected_marker = "*" if uid == selected else " "
        for ci, ch in enumerate(f"{selected_marker}{label}"):
            col = ix + ci
            if 0 <= col < logical_w and 0 <= iy < logical_h:
                canvas[iy][col] = ch

    if view_width is not None and view_height is not None:
        pan_x = max(0, min(pan_x, logical_w - view_width))
        pan_y = max(0, min(pan_y, logical_h - view_height))
        lines = []
        for y in range(pan_y, pan_y + view_height):
            if y < logical_h:
                row = "".join(canvas[y][pan_x:pan_x + view_width])
                if len(row) < view_width:
                    row += " " * (view_width - len(row))
                lines.append(row)
            else:
                lines.append(" " * view_width)
        return "\n".join(lines)

    return "\n".join("".join(row) for row in canvas)
```

- [ ] **Step 2.5: Fix keyboard pan handlers to clamp pan bounds**

Update `_handle_pan`:

```python
def _handle_pan(self, direction: str) -> None:
    if self._layout is None:
        return
    canvas_widget = self.query_one("#graph-canvas", Static)
    view_w = canvas_widget.content_region.width
    view_h = canvas_widget.content_region.height
    if direction == "left":
        self._pan_x = max(0, self._pan_x - 5)
    elif direction == "right":
        self._pan_x += 5
    elif direction == "up":
        self._pan_y = max(0, self._pan_y - 2)
    elif direction == "down":
        self._pan_y += 2
    self._render_canvas()
```

- [ ] **Step 2.6: Wire zoom into `_render_canvas()` and keyboard handling**

Update `_render_canvas()` to pass zoom:

```python
def _render_canvas(self) -> None:
    canvas_widget = self.query_one("#graph-canvas", Static)
    if self._layout is None:
        canvas_widget.update("No graph data")
        return
    view_width = canvas_widget.content_region.width
    view_height = canvas_widget.content_region.height
    ascii_art = self._layout.render_ascii(
        selected=self._selected_uuid,
        view_width=view_width,
        view_height=view_height,
        pan_x=self._pan_x,
        pan_y=self._pan_y,
        zoom=self._zoom,
    )
    canvas_widget.update(ascii_art)
```

The existing `on_key` handlers for `plus`/`equal`/`minus` already adjust `self._zoom` and call `_render_canvas()` — no changes needed there (lines 246-250 already work).

- [ ] **Step 2.7: Add zoom test**

Add to `prism-tui/tests/test_layout.py`:

```python
def test_render_ascii_zoom_changes_output() -> None:
    nodes = [_make_node("abc-123", "Test")]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    normal = layout.render_ascii(view_width=80, view_height=40)
    zoomed = layout.render_ascii(view_width=80, view_height=40, zoom=2.0)
    assert normal != zoomed
```

- [ ] **Step 2.8: Run layout tests to confirm nothing broke**

Run:
```bash
.venv/bin/python -m pytest prism-tui/tests/test_layout.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 2.9: Commit**

```bash
git add prism-tui/prism_tui/tabs/graph.py prism-tui/tests/test_layout.py
git commit -m "fix(tui): wire pan/zoom controls in graph tab rendering"
```

---

### Task 3: Update existing spec and verify

**Files:**
- Modify: `openspec/changes/tui-application/specs/tui-graph-view/spec.md`

- [ ] **Step 3.1: Update the spec to reflect no-truncation behavior**

Change line 15 from:
```
- **THEN** the node box SHALL display the first 12 characters of the node's title
```
to:
```
- **THEN** the node label SHALL display the full node title without truncation
- **THEN** the user SHALL pan the view with arrow keys to see labels beyond the viewport
```

- [ ] **Step 3.2: Run full test suite**

Run:
```bash
.venv/bin/python -m pytest prism-tui/tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3.3: Commit**

```bash
git add openspec/changes/tui-application/specs/tui-graph-view/spec.md
git commit -m "docs: update graph spec for full titles and pan"
```
