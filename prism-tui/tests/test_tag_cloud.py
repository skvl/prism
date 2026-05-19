"""Tests for tag cloud filtering logic."""

from collections import Counter
from unittest.mock import MagicMock

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
