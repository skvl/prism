## Context

Two bugs remain in the prism-tui after rounds 1 and 2 of fixes (from `TODO.md`):

1. **F4: Graph tab truncates long node titles** — `ForceDirectedLayout.render_ascii()` hard-caps all labels to 8 characters via `node.title[:8]`, even though the ASCII canvas is 80 chars wide and per-character bounds checking already prevents overflow.

2. **F5: Tags tab DuplicateIds error** — Tag buttons use `id=f"tag-{tag}"` derived from the tag name. When the Tags tab is re-entered (e.g., clicking a node navigates away and back), `_render_cloud()` removes children and re-mounts buttons, but Textual's DOM teardown can interleave, causing `DuplicateIds: Tried to insert a widget with ID 'tag-ai'`.

## Design

### F4: Dynamic title truncation in graph tab

**File:** `prism-tui/prism_tui/tabs/graph.py`

**Change in `render_ascii()` (line ~110):**

Replace the static `[:8]` truncation with a per-node available-width calculation:

```python
avail = max(4, self.width - int(x) - 1)  # -1 for the selected marker '*'
label = (node.title or uid)[:avail]
```

The existing bounds check in the character rendering loop already guards against writing past `self.width`, so this is safe — we just let each node use as much of its row as its x-position allows, with a floor of 4 characters.

### F5: Eliminate duplicate IDs in tag cloud

**File:** `prism-tui/prism_tui/tabs/tag_cloud.py`

Three methods need changes:

**1. `_render_cloud()`** — Remove `id=` from Button creation, store tag name as a widget attribute instead:

```python
btn = Button(f"{tag} ({count})", classes=f"tag-button {style_class}")
btn._tag_name = tag
area.mount(btn)
```

**2. `on_button_pressed()`** — Read tag from attribute instead of parsing ID:

```python
# Before:
tag = event.button.id.split("-", 1)[1]

# After:
tag = event.button._tag_name
```

**3. `_highlight_co_occurring(tag_name)`** — Query by CSS class, filter by attribute:

```python
# Before:
for other_tag in co_tags:
    btn = self.query_one(f"#tag-{other_tag}", Button)
    btn.classes = f"tag-button {style_class}"

# After:
for other in self.query(".tag-button"):
    if hasattr(other, "_tag_name") and other._tag_name != tag_name and ...:
        other.classes = f"tag-button co-occurring"
```

### Files changed

| File | Changes |
|------|---------|
| `prism-tui/prism_tui/tabs/graph.py` | Dynamic title truncation |
| `prism-tui/prism_tui/tabs/tag_cloud.py` | Remove tag-button IDs, use CSS class + widget attribute |

### No spec changes needed

The existing `tui-graph-view/spec.md` already states "first 12 characters" — the dynamic approach subsumes this without contradiction. The `tui-tag-cloud/spec.md` does not specify widget ID behavior.
