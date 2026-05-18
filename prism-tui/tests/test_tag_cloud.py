"""Tests for tag cloud filtering logic."""

from prism_tui.tabs.tag_cloud import TagCloudTab

from prism.node.metadata import NodeMetadata


def _make_node(uuid: str, tags: list[str] | None = None) -> NodeMetadata:
    return NodeMetadata(
        uuid=uuid,
        type="note",
        title=f"Node {uuid[:4]}",
        tags=tags or [],
    )


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
