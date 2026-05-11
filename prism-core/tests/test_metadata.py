import os
import tempfile

import tomlkit

from prism.node.metadata import NodeMetadata


class TestNodeMetadata:
    def test_to_toml_with_all_fields(self):
        meta = NodeMetadata(
            uuid="test-uuid-1234",
            type="note",
            title="Test Title",
            tags=["a", "b"],
            fields={"key": "val", "count": 42},
            links=[{"target": "other-uuid", "type": "", "title": ""}],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00",
            blob_extension="md",
            blob_mtime="12345.0",
            blob_size=100,
            blob_sha256="abc123def456",
            sync_dirty=True,
        )
        toml_str = meta.to_toml()
        assert "test-uuid-1234" in toml_str
        assert "sync_dirty" in toml_str
        doc = tomlkit.loads(toml_str)
        assert doc["uuid"] == "test-uuid-1234"
        assert doc["blob_extension"] == "md"
        assert doc["blob_size"] == 100
        assert doc["blob_sha256"] == "abc123def456"
        assert doc["blob_mtime"] == "12345.0"
        assert doc["sync_dirty"] is True
        assert doc["title"] == "Test Title"
        assert doc["type"] == "note"
        assert list(doc["tags"]) == ["a", "b"]
        assert doc["fields"]["key"] == "val"

    def test_to_toml_empty_fields(self):
        meta = NodeMetadata(uuid="u1", type="empty-test")
        toml_str = meta.to_toml()
        doc = tomlkit.loads(toml_str)
        assert doc["uuid"] == "u1"
        assert "tags" not in doc
        assert "fields" not in doc
        assert "links" not in doc
        assert "blob_extension" not in doc
        assert doc["sync_dirty"] is False

    def test_save_and_from_toml_roundtrip(self):
        tmp = tempfile.mkstemp()[1]
        try:
            meta = NodeMetadata(
                uuid="roundtrip-uuid",
                type="note",
                title="Roundtrip Title",
                tags=["tag1"],
                fields={"key": "value"},
            )
            meta.save(tmp)
            loaded = NodeMetadata.from_toml(tmp)
            assert loaded.uuid == "roundtrip-uuid"
            assert loaded.title == "Roundtrip Title"
            assert loaded.type == "note"
            assert loaded.tags == ["tag1"]
            assert loaded.fields == {"key": "value"}
        finally:
            os.unlink(tmp)

    def test_metadata_path(self):
        path = NodeMetadata.metadata_path("/some/dir")
        assert path == "/some/dir/metadata.toml"
