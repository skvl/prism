from prism_tui.messages import SelectNode
from prism.node.metadata import NodeMetadata


def test_select_node_message():
    node = NodeMetadata(
        uuid="test-uuid",
        type="note",
        title="Test Node",
        tags=["work"],
    )
    msg = SelectNode(node)
    assert msg.node is node
    assert msg.node.uuid == "test-uuid"
    assert msg.node.title == "Test Node"
