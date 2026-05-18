"""Tests for force-directed layout as a pure function."""

import math

from prism_tui.tabs.graph import ForceDirectedLayout

from prism.node.metadata import NodeMetadata


def _make_node(uuid: str, title: str = "") -> NodeMetadata:
    return NodeMetadata(
        uuid=uuid,
        type="note",
        title=title or uuid[:8],
    )


def test_layout_returns_positions_for_all_nodes() -> None:
    nodes = [_make_node("a"), _make_node("b"), _make_node("c")]
    links = [{"source": "a", "target": "b"}]
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    assert len(layout.positions) == 3
    for uid in ("a", "b", "c"):
        assert uid in layout.positions
        x, y = layout.positions[uid]
        assert isinstance(x, float)
        assert isinstance(y, float)


def test_layout_separates_overlapping_nodes() -> None:
    nodes = [_make_node("a"), _make_node("b")]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    original_positions = dict(layout.positions)
    layout.tick(100)
    assert layout.positions["a"] != layout.positions["b"]


def test_linked_nodes_attract() -> None:
    nodes = [_make_node("a"), _make_node("b")]
    links = [{"source": "a", "target": "b"}]
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(100)
    ax, ay = layout.positions["a"]
    bx, by = layout.positions["b"]
    dist = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2)
    assert dist < 50


def test_render_ascii_contains_node_labels() -> None:
    nodes = [_make_node("abc-123", "TestNode")]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    output = layout.render_ascii()
    assert "TestNode" in output or "Test" in output


def test_render_ascii_marks_selected_node() -> None:
    nodes = [_make_node("sel-uuid")]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    output_selected = layout.render_ascii(selected="sel-uuid")
    output_unselected = layout.render_ascii(selected=None)
    assert output_selected != output_unselected


def test_render_ascii_long_title_shows_more_than_8_chars() -> None:
    nodes = [_make_node("abc-123", "This is a very long node title that should show")]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    output = layout.render_ascii()
    # The dynamic truncation should show at least 4 chars of the title
    # (floor of avail calculation). The old [:8] hard cap would show at most 8 chars.
    # We verify that the title text actually appears in the output.
    assert "This is a " in output


def test_render_ascii_shows_full_title() -> None:
    title = "Complete Node Title That Should Not Be Truncated"
    nodes = [_make_node("abc-123", title)]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    output = layout.render_ascii()
    assert title in output


def test_render_ascii_pan_offsets_content() -> None:
    nodes = [_make_node("abc-123", "HelloWorld")]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    full = layout.render_ascii()
    panned = layout.render_ascii(view_width=80, view_height=40, pan_x=20, pan_y=0)
    assert full != panned


def test_render_ascii_zoom_changes_output() -> None:
    nodes = [_make_node("abc-123", "Test")]
    links: list[dict[str, str]] = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    normal = layout.render_ascii(view_width=80, view_height=40)
    zoomed = layout.render_ascii(view_width=80, view_height=40, zoom=2.0)
    assert normal != zoomed
