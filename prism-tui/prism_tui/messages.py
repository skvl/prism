from __future__ import annotations

from textual.message import Message

from prism.node.metadata import NodeMetadata


class SelectNode(Message):
    def __init__(self, node: NodeMetadata) -> None:
        super().__init__()
        self.node = node
