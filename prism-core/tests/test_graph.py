import pytest

from prism.graph.links import LinkExtractor


class TestLinkExtractor:
    def test_extract_uuid_links(self):
        body = "Hello [[a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d]] world"
        links = LinkExtractor.extract_links(body)
        assert len(links) == 1
        assert links[0]["target"] == "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

    def test_extract_cross_vault_links(self):
        body = "See [[a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d::f1e2d3c4-b5a6-4c7d-8e9f-0a1b2c3d4e5f]]"
        links = LinkExtractor.extract_links(body)
        assert len(links) == 1
        assert links[0].get("vault") == "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

    def test_extract_multiple_links(self):
        body = "[[a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d]] and [[f1e2d3c4-b5a6-4c7d-8e9f-0a1b2c3d4e5f]]"
        links = LinkExtractor.extract_links(body)
        assert len(links) == 2

    def test_no_links(self):
        body = "Hello world without any links"
        links = LinkExtractor.extract_links(body)
        assert len(links) == 0

    def test_duplicate_links_deduped(self):
        body = "[[a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d]] and again [[a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d]]"
        links = LinkExtractor.extract_links(body)
        assert len(links) == 1


class TestGraphExporter:
    def test_dot_export(self):
        from prism.graph.links import GraphExporter
        from prism.node.metadata import NodeMetadata

        nodes = [
            NodeMetadata(uuid="a1b2", type="note", title="Note A"),
            NodeMetadata(uuid="c3d4", type="note", title="Note B", links=[{"target": "a1b2"}]),
        ]
        exporter = GraphExporter("/tmp")
        dot = exporter.export_dot(nodes)
        assert "digraph Prism" in dot
        assert "Note A" in dot
        assert "Note B" in dot

    def test_json_export(self):
        from prism.graph.links import GraphExporter
        from prism.node.metadata import NodeMetadata

        nodes = [
            NodeMetadata(uuid="a1b2", type="note", title="Note A"),
            NodeMetadata(uuid="c3d4", type="note", title="Note B", links=[{"target": "a1b2"}]),
        ]
        exporter = GraphExporter("/tmp")
        js = exporter.export_json(nodes)
        assert '"nodes"' in js
        assert '"edges"' in js
