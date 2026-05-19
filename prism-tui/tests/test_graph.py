from unittest.mock import MagicMock, patch

import json

from prism_tui.tabs.graph import ForceDirectedLayout, GraphTab

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


class TestGraphTab:
    def test_init_defaults(self):
        tab = GraphTab()
        assert tab._vault is None
        assert tab._manager is None
        assert tab._layout is None
        assert tab._selected_uuid is None
        assert tab._type_filter is None

    def test_set_vault_no_vault(self):
        tab = GraphTab()
        tab._load_graph = MagicMock()
        tab.set_vault(MagicMock())
        assert tab._load_graph.called

    def test_load_graph_no_vault(self):
        tab = GraphTab()
        tab._vault = None
        tab._load_graph()

    def test_load_graph_with_vault(self):
        tab = GraphTab()
        tab._vault = MagicMock()
        tab._vault.path = "/tmp/test"
        tab._manager = MagicMock()
        tab._manager.list_nodes.return_value = []
        static = MagicMock()
        static.content_region.width = 80
        static.content_region.height = 24
        tab.query_one = MagicMock(return_value=static)
        with patch("prism_tui.tabs.graph.GraphExporter") as MockExporter:
            instance = MagicMock()
            instance.export_json.return_value = json.dumps({"edges": []})
            MockExporter.return_value = instance
            tab._load_graph()

    def test_filtered_nodes_no_filter(self):
        tab = GraphTab()
        tab._all_nodes = [_make_node("a")]
        result = tab._filtered_nodes()
        assert len(result) == 1

    def test_filtered_nodes_with_filter(self):
        tab = GraphTab()
        tab._type_filter = "note"
        n1 = _make_node("a")
        n2 = _make_node("b")
        n2.type = "contact"
        tab._all_nodes = [n1, n2]
        result = tab._filtered_nodes()
        assert len(result) == 1
        assert result[0].type == "note"

    def test_render_canvas_no_layout(self):
        tab = GraphTab()
        static = MagicMock()
        tab.query_one = MagicMock(return_value=static)
        tab._layout = None
        tab._render_canvas()
        static.update.assert_called_with("No graph data")

    def test_render_canvas_with_layout(self):
        tab = GraphTab()
        static = MagicMock()
        static.content_region.width = 80
        static.content_region.height = 24
        tab.query_one = MagicMock(return_value=static)
        tab._layout = MagicMock()
        tab._layout.render_ascii.return_value = "graph\nart"
        tab._selected_uuid = None
        tab._pan_x = 0
        tab._pan_y = 0
        tab._zoom = 1.0
        tab._render_canvas()
        assert tab._layout.render_ascii.called

    def test_on_mount_with_vault(self):
        tab = GraphTab()
        tab._vault = MagicMock()
        tab._load_graph = MagicMock()
        list_view = MagicMock()
        tab.query_one = MagicMock(return_value=list_view)
        tab.on_mount()
        assert tab._load_graph.called
        assert list_view.display is False

    def test_on_key_t_prompts_filter(self):
        tab = GraphTab()
        tab.notify = MagicMock()
        event = MagicMock()
        event.key = "t"
        tab.on_key(event)
        assert tab.notify.called

    def test_on_key_enter_navigates_browser(self):
        tab = GraphTab()
        tab._selected_uuid = "test-uuid"
        tab.post_message = MagicMock()
        tab._all_nodes = [_make_node("test-uuid", "Test")]
        event = MagicMock()
        event.key = "Enter"
        tab.on_key(event)
        assert tab.post_message.called

    def test_on_key_left_pan(self):
        tab = GraphTab()
        tab._layout = MagicMock()
        tab._render_canvas = MagicMock()
        event = MagicMock()
        event.key = "left"
        tab.on_key(event)
        tab._render_canvas.assert_called()

    def test_on_key_right_pan(self):
        tab = GraphTab()
        tab._layout = MagicMock()
        tab._render_canvas = MagicMock()
        event = MagicMock()
        event.key = "right"
        tab.on_key(event)
        assert tab._pan_x == 5

    def test_on_key_up_pan(self):
        tab = GraphTab()
        tab._layout = MagicMock()
        tab._render_canvas = MagicMock()
        event = MagicMock()
        event.key = "up"
        tab.on_key(event)
        assert tab._pan_y == 0  # pan_y = max(0, 0-2) = 0

    def test_on_key_down_pan(self):
        tab = GraphTab()
        tab._layout = MagicMock()
        tab._render_canvas = MagicMock()
        event = MagicMock()
        event.key = "down"
        tab.on_key(event)
        assert tab._pan_y == 2

    def test_on_key_zoom_in(self):
        tab = GraphTab()
        tab._zoom = 1.0
        event = MagicMock()
        event.key = "plus"
        tab.on_key(event)
        assert tab._zoom == 1.2

    def test_on_key_zoom_out(self):
        tab = GraphTab()
        tab._zoom = 1.0
        event = MagicMock()
        event.key = "minus"
        tab.on_key(event)
        assert tab._zoom == 0.8

    def test_on_key_zoom_minimum(self):
        tab = GraphTab()
        tab._zoom = 0.5
        event = MagicMock()
        event.key = "minus"
        tab.on_key(event)
        assert tab._zoom == 0.5

    def test_on_key_zoom_maximum(self):
        tab = GraphTab()
        tab._zoom = 3.0
        event = MagicMock()
        event.key = "plus"
        tab.on_key(event)
        assert tab._zoom == 3.0

    def test_handle_pan_no_layout(self):
        tab = GraphTab()
        tab._layout = None
        tab._handle_pan("left")

    def test_navigate_to_browser_no_selection(self):
        tab = GraphTab()
        tab._selected_uuid = None
        tab.post_message = MagicMock()
        tab._navigate_to_browser()
        assert not tab.post_message.called

    def test_prompt_type_filter(self):
        tab = GraphTab()
        tab.notify = MagicMock()
        tab._prompt_type_filter()
        assert tab.notify.called

    def test_show_list_view(self):
        tab = GraphTab()
        static = MagicMock()
        list_view = MagicMock()
        tab.query_one = MagicMock(side_effect=[static, list_view])
        tab._all_links = [{"source": "a", "target": "b"}]
        tab._show_list_view([
            _make_node("a", "Node A"),
            _make_node("b", "Node B"),
        ])
        assert static.display is False
        assert list_view.display is True
        assert list_view.clear.called


class TestForceDirectedLayoutEdgeCases:
    def test_render_ascii_no_view_dimensions(self):
        nodes = [_make_node("a")]
        layout = ForceDirectedLayout(nodes, [])
        layout.tick(10)
        result = layout.render_ascii(None, None, None, 0, 0, 1.0)
        assert result is not None

    def test_render_ascii_view_overflow(self):
        nodes = [_make_node("a")]
        layout = ForceDirectedLayout(nodes, [])
        layout.tick(10)
        result = layout.render_ascii(None, 80, 100, 0, 0, 1.0)
        assert result is not None

    def test_draw_line_short(self):
        nodes = [_make_node("a")]
        layout = ForceDirectedLayout(nodes, [])
        canvas = [[" " for _ in range(5)] for _ in range(5)]
        layout._draw_line(canvas, 0, 0, 1, 1, 5, 5)
        assert canvas[0][0] == "." or canvas[1][1] == "."
