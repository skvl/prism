from prism_tui.tabs.graph import ForceDirectedLayout

from prism.node.metadata import NodeMetadata


def _make_node(uuid: str, title: str = "") -> NodeMetadata:
    return NodeMetadata(
        uuid=uuid,
        type="note",
        title=title or uuid[:8],
    )


def test_layout_empty_nodes():
    layout = ForceDirectedLayout([], [])
    result = layout.render_ascii(None, 80, 24, 0, 0, 1.0)
    assert result is not None


def test_layout_tick_converges():
    nodes = [_make_node("a"), _make_node("b"), _make_node("c")]
    links = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(iterations=10)
    for pos in layout.positions.values():
        assert 0 <= pos[0] <= layout.width
        assert 0 <= pos[1] <= layout.height


def test_render_ascii_with_selection():
    nodes = [_make_node("a", "Node A"), _make_node("b", "Node B")]
    links = [{"source": "a", "target": "b"}]
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    result = layout.render_ascii("a", 80, 40, 0, 0, 1.0)
    assert "Node A" in result or "*" in result


def test_render_ascii_pan_and_zoom():
    nodes = [_make_node("a", "Test")]
    links = []
    layout = ForceDirectedLayout(nodes, links)
    layout.tick(10)
    result = layout.render_ascii(None, 80, 24, 10, 10, 2.0)
    assert result is not None


def test_draw_line():
    nodes = [_make_node("a")]
    links = []
    layout = ForceDirectedLayout(nodes, links)
    canvas = [[" " for _ in range(10)] for _ in range(10)]
    layout._draw_line(canvas, 0, 0, 9, 9, 10, 10)
    assert canvas[0][0] == "." or canvas[9][9] == "."
