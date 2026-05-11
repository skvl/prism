import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest

from prism.graph.links import BacklinkIndex, GraphExporter, LinkExtractor
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.vault.vault import Vault


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
    def test_extract_from_file(self):
        tmp = tempfile.mkstemp(suffix=".md")[1]
        try:
            with open(tmp, "w") as f:
                f.write("Link to [[a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d]]")
            links = LinkExtractor.extract_from_file(tmp)
            assert len(links) == 1
            assert links[0]["target"] == "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        finally:
            os.unlink(tmp)


class TestGraphExporter:
    def test_dot_export(self):
        nodes = [
            NodeMetadata(uuid="a1b2", type="note", title="Note A"),
            NodeMetadata(uuid="c3d4", type="note", title="Note B", links=[{"target": "a1b2"}]),
        ]
        exporter = GraphExporter("/tmp")
        dot = exporter.export_dot(nodes)
        assert "digraph Prism" in dot
        assert "Note A" in dot
        assert "Note B" in dot

    def test_dot_export_empty_nodes(self):
        exporter = GraphExporter("/tmp")
        dot = exporter.export_dot([])
        assert "digraph Prism" in dot

    def test_dot_export_no_links(self):
        nodes = [NodeMetadata(uuid="a1b2", type="note", title="Note A")]
        exporter = GraphExporter("/tmp")
        dot = exporter.export_dot(nodes)
        assert "Note A" in dot

    def test_json_export(self):
        nodes = [
            NodeMetadata(uuid="a1b2", type="note", title="Note A"),
            NodeMetadata(uuid="c3d4", type="note", title="Note B", links=[{"target": "a1b2"}]),
        ]
        exporter = GraphExporter("/tmp")
        js = exporter.export_json(nodes)
        assert '"nodes"' in js
        assert '"edges"' in js

    def test_json_export_no_links(self):
        nodes = [NodeMetadata(uuid="a1b2", type="note", title="Note A")]
        exporter = GraphExporter("/tmp")
        js = exporter.export_json(nodes)
        assert '"nodes"' in js

    def test_resolve_cross_vault_link_no_vault(self):
        result = GraphExporter.resolve_cross_vault_link("nonexistent-uuid", "target-uuid")
        assert result is None


class TestBacklinkIndex:
    @pytest.fixture
    def vault_dir(self):
        d = tempfile.mkdtemp()
        Vault.init(d)
        uid1 = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        uid2 = "f1e2d3c4-b5a6-4c7d-8e9f-0a1b2c3d4e5f"
        storage_dir1 = compute_storage_path(d, uid1)
        os.makedirs(storage_dir1, exist_ok=True)
        meta1 = NodeMetadata(uuid=uid1, type="note", title="Note A", links=[{"target": uid2}])
        meta1.save(NodeMetadata.metadata_path(storage_dir1))
        storage_dir2 = compute_storage_path(d, uid2)
        os.makedirs(storage_dir2, exist_ok=True)
        meta2 = NodeMetadata(uuid=uid2, type="note", title="Note B")
        meta2.save(NodeMetadata.metadata_path(storage_dir2))
        yield d
        shutil.rmtree(d)

    def test_build(self, vault_dir):
        index = BacklinkIndex(vault_dir)
        result = index.build()
        assert "f1e2d3c4-b5a6-4c7d-8e9f-0a1b2c3d4e5f" in result
        assert len(result["f1e2d3c4-b5a6-4c7d-8e9f-0a1b2c3d4e5f"]) == 1

    def test_get_backlinks(self, vault_dir):
        index = BacklinkIndex(vault_dir)
        result = index.get_backlinks("f1e2d3c4-b5a6-4c7d-8e9f-0a1b2c3d4e5f")
        assert len(result) == 1
        result2 = index.get_backlinks("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
        assert len(result2) == 0

    def test_build_empty_vault(self):
        d = tempfile.mkdtemp()
        try:
            index = BacklinkIndex(d)
            result = index.build()
            assert result == {}
        finally:
            shutil.rmtree(d)

    def test_build_with_corrupt_metadata(self, vault_dir):
        bad_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, bad_uid)
        os.makedirs(storage_dir, exist_ok=True)
        with open(NodeMetadata.metadata_path(storage_dir), "w") as f:
            f.write("not valid toml {{{{\n")
        index = BacklinkIndex(vault_dir)
        result = index.build()
        assert "f1e2d3c4-b5a6-4c7d-8e9f-0a1b2c3d4e5f" in result


class TestResolveCrossVaultLink:
    @pytest.fixture
    def vault_dir(self):
        d = tempfile.mkdtemp()
        Vault.init(d)
        meta = NodeMetadata(uuid=str(uuid.uuid4()), type="note", title="Cross Vault Target")
        storage_dir = compute_storage_path(d, meta.uuid)
        os.makedirs(storage_dir, exist_ok=True)
        meta.save(NodeMetadata.metadata_path(storage_dir))
        yield d, meta
        shutil.rmtree(d)

    def test_resolve_success(self, vault_dir, monkeypatch):
        d, meta = vault_dir
        tmp_reg = Path(tempfile.mkdtemp()) / "vaults.toml"
        monkeypatch.setattr("prism.vault.registry.REGISTRY_PATH", tmp_reg)
        from prism.vault.registry import VaultRegistry
        reg = VaultRegistry()
        vault = Vault.open(d)
        reg.add(vault.vault_uuid, d)
        result = GraphExporter.resolve_cross_vault_link(vault.vault_uuid, meta.uuid)
        assert result is not None
        assert result["uuid"] == meta.uuid
        assert result["title"] == "Cross Vault Target"

    def test_resolve_nonexistent_target(self, vault_dir, monkeypatch):
        d, _meta = vault_dir
        tmp_reg = Path(tempfile.mkdtemp()) / "vaults.toml"
        monkeypatch.setattr("prism.vault.registry.REGISTRY_PATH", tmp_reg)
        from prism.vault.registry import VaultRegistry
        reg = VaultRegistry()
        vault = Vault.open(d)
        reg.add(vault.vault_uuid, d)
        result = GraphExporter.resolve_cross_vault_link(vault.vault_uuid, "00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_resolve_corrupt_target_metadata(self, vault_dir, monkeypatch):
        d, _meta = vault_dir
        tmp_reg = Path(tempfile.mkdtemp()) / "vaults.toml"
        monkeypatch.setattr("prism.vault.registry.REGISTRY_PATH", tmp_reg)
        from prism.vault.registry import VaultRegistry
        reg = VaultRegistry()
        vault = Vault.open(d)
        reg.add(vault.vault_uuid, d)
        target_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(d, target_uid)
        os.makedirs(storage_dir, exist_ok=True)
        with open(NodeMetadata.metadata_path(storage_dir), "w") as f:
            f.write("not [[valid toml\n")
        result = GraphExporter.resolve_cross_vault_link(vault.vault_uuid, target_uid)
        assert result is None
