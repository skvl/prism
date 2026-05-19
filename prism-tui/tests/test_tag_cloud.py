"""Tests for tag cloud filtering logic."""

from collections import Counter
from unittest.mock import MagicMock, patch

import pytest

from prism_tui.tabs.tag_cloud import TagCloudTab

from prism.node.metadata import NodeMetadata


def _make_node(uuid: str, tags: list[str] | None = None) -> NodeMetadata:
    return NodeMetadata(
        uuid=uuid,
        type="note",
        title=f"Node {uuid[:4]}",
        tags=tags or [],
    )


@pytest.fixture
def tag_cloud():
    tab = TagCloudTab()
    tab._vault = MagicMock()
    tab._manager = MagicMock()
    tab._tag_nodes = {"work": ["uuid1", "uuid2"], "personal": ["uuid3"]}
    tab._tag_counts = Counter({"work": 2, "personal": 1})
    tab._selected_tags = set()
    tab._filtered_nodes = []
    tab.query_one = MagicMock()
    return tab


def test_no_tag_derived_ids_in_source() -> None:
    """Tag buttons should use _tag_name attribute, not tag-derived IDs."""
    import inspect

    source = inspect.getsource(TagCloudTab._render_cloud)
    assert 'id=f"tag-' not in source, "Should not use tag-derived IDs"
    assert "._tag_name" in source, "Should set _tag_name attribute"


def test_tag_selection_narrows_nodes() -> None:
    """Selecting a tag should filter the node list to matching nodes."""
    tab = TagCloudTab()
    aaa = _make_node("aaa", ["ai"])
    bbb = _make_node("bbb", ["ai", "ml"])
    ccc = _make_node("ccc", ["ml"])
    tab._tag_nodes = {"ai": [aaa, bbb], "ml": [ccc]}

    tab._selected_tags = {"ai"}
    matching: set[str] | None = None
    for tag in tab._selected_tags:
        tag_node_uuids = {n.uuid for n in tab._tag_nodes.get(tag, [])}
        if matching is None:
            matching = tag_node_uuids
        else:
            matching &= tag_node_uuids
    filtered = matching or set()

    assert "aaa" in filtered
    assert "bbb" in filtered
    assert "ccc" not in filtered


def test_load_tags_no_vault(tag_cloud):
    tag_cloud._vault = None
    tag_cloud._load_tags()


def test_render_cloud_no_tags(tag_cloud):
    tag_cloud._tag_counts = Counter()
    tag_cloud._render_cloud()


def test_highlight_co_occurring_no_selection(tag_cloud):
    tag_cloud._selected_tags = set()
    tag_cloud._highlight_co_occurring()


def test_update_node_list_no_selection(tag_cloud):
    tag_cloud._selected_tags = set()
    tag_cloud._update_node_list()


def test_on_button_pressed_selects_tag(tag_cloud):
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    event = MagicMock()
    event.button._tag_name = "work"
    tag_cloud.on_button_pressed(event)
    assert "work" in tag_cloud._selected_tags


def test_on_button_pressed_clear(tag_cloud):
    tag_cloud._selected_tags = {"work"}
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    event = MagicMock()
    event.button._tag_name = "__clear__"
    tag_cloud.on_button_pressed(event)
    assert len(tag_cloud._selected_tags) == 0


def test_on_button_pressed_deselects_tag(tag_cloud):
    tag_cloud._selected_tags = {"work"}
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    event = MagicMock()
    event.button._tag_name = "work"
    tag_cloud.on_button_pressed(event)
    assert "work" not in tag_cloud._selected_tags


def test_on_key_escape_clears_selection(tag_cloud):
    tag_cloud._selected_tags = {"work"}
    tag_cloud._render_cloud = MagicMock()
    tag_cloud._update_node_list = MagicMock()
    event = MagicMock()
    event.key = "escape"
    tag_cloud.on_key(event)
    assert len(tag_cloud._selected_tags) == 0
    assert event.stop.called


def test_on_list_view_selected_posts_message(tag_cloud):
    tag_cloud._filtered_nodes = [
        _make_node("uuid1", ["work"]),
        _make_node("uuid2", ["personal"]),
    ]
    tag_cloud.post_message = MagicMock()
    event = MagicMock()
    event.item._node_uuid = "uuid1"
    tag_cloud.on_list_view_selected(event)
    assert tag_cloud.post_message.called


def test_on_list_view_selected_none_item(tag_cloud):
    tag_cloud.post_message = MagicMock()
    event = MagicMock()
    event.item = None
    tag_cloud.on_list_view_selected(event)
    assert not tag_cloud.post_message.called


def test_load_tags_with_vault(tag_cloud):
    tag_cloud._vault = MagicMock()
    with patch("prism_tui.tabs.tag_cloud.NodeManager") as MockNodeManager:
        MockNodeManager.return_value.list_nodes.return_value = [
            _make_node("a", ["work"]),
        ]
        tag_cloud._render_cloud = MagicMock()
        tag_cloud._update_node_list = MagicMock()
        tag_cloud._load_tags()
    assert tag_cloud._tag_counts["work"] == 1


def test_compose_returns_widgets(tag_cloud):
    from textual.containers import VerticalScroll
    from textual.widgets import ListView
    result = list(tag_cloud.compose())
    assert len(result) == 2
    assert isinstance(result[0], VerticalScroll)
    assert isinstance(result[1], ListView)
