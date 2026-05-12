import os
import shutil
import tempfile

import pytest

from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.tracking import ChangeTracker
from prism.types.builtins import NOTE_TOML
from prism.vault.vault import Vault


class TestChangeTracker:
    @pytest.fixture
    def vault_dir(self):
        d = tempfile.mkdtemp()
        Vault.init(d)
        types_dir = os.path.join(d, ".metadata", "types")
        with open(os.path.join(types_dir, "note.toml"), "w") as f:
            f.write(NOTE_TOML)
        manager = NodeManager(d)
        manager.create_node(type_name="note", title="Tracked Node", tags=["test"])
        yield d
        shutil.rmtree(d)

    def test_status(self, vault_dir):
        tracker = ChangeTracker(vault_dir)
        status = tracker.status()
        assert "changed" in status
        assert "new_files" in status
        assert "orphaned" in status

    def test_status_with_modified_blob(self, vault_dir):
        manager = NodeManager(vault_dir)
        nodes = [n for n in manager.list_nodes() if n.type != "path"]
        assert len(nodes) > 0
        node = nodes[0]
        storage_dir = compute_storage_path(vault_dir, node.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        meta.blob_mtime = "0"
        meta.save(meta_path)
        body_path = os.path.join(storage_dir, "data.md")
        with open(body_path, "a") as f:
            f.write("\nmodified content")
        tracker = ChangeTracker(vault_dir)
        status = tracker.status()
        assert len(status["changed"]) > 0

    def _first_user_node(self, vault_dir):
        manager = NodeManager(vault_dir)
        nodes = [n for n in manager.list_nodes() if n.type != "path"]
        return nodes[0] if nodes else None

    def test_mark_dirty(self, vault_dir):
        node = self._first_user_node(vault_dir)
        assert node is not None
        tracker = ChangeTracker(vault_dir)
        tracker.mark_dirty(node.uuid)
        meta = NodeMetadata.from_toml(
            NodeMetadata.metadata_path(compute_storage_path(vault_dir, node.uuid))
        )
        assert meta.sync_dirty is True

    def test_mark_dirty_nonexistent(self, vault_dir):
        tracker = ChangeTracker(vault_dir)
        tracker.mark_dirty("00000000-0000-0000-0000-000000000000")

    def test_update_blob_info(self, vault_dir):
        node = self._first_user_node(vault_dir)
        assert node is not None
        tracker = ChangeTracker(vault_dir)
        tracker.update_blob_info(node.uuid)

    def test_update_blob_info_nonexistent(self, vault_dir):
        tracker = ChangeTracker(vault_dir)
        tracker.update_blob_info("00000000-0000-0000-0000-000000000000")

    def test_re_extract_links(self, vault_dir):
        node = self._first_user_node(vault_dir)
        assert node is not None
        tracker = ChangeTracker(vault_dir)
        result = tracker.re_extract_links(node.uuid)
        assert result is True

    def test_re_extract_links_nonexistent(self, vault_dir):
        tracker = ChangeTracker(vault_dir)
        result = tracker.re_extract_links("00000000-0000-0000-0000-000000000000")
        assert result is False

    def test_re_extract_links_no_blob(self, vault_dir):
        from prism.types.builtins import CONTACT_TOML
        types_dir = os.path.join(vault_dir, ".metadata", "types")
        with open(os.path.join(types_dir, "contact.toml"), "w") as f:
            f.write(CONTACT_TOML)
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="contact", fields={"name": "No Blob"})
        tracker = ChangeTracker(vault_dir)
        result = tracker.re_extract_links(meta.uuid)
        assert result is False

    def test_re_extract_links_missing_body(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Missing Body")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        os.unlink(os.path.join(storage_dir, "data.md"))
        tracker = ChangeTracker(vault_dir)
        result = tracker.re_extract_links(meta.uuid)
        assert result is False

    def test_update_blob_info_no_blob(self, vault_dir):
        manager = NodeManager(vault_dir)
        from prism.types.builtins import CONTACT_TOML
        types_dir = os.path.join(vault_dir, ".metadata", "types")
        with open(os.path.join(types_dir, "contact.toml"), "w") as f:
            f.write(CONTACT_TOML)
        meta = manager.create_node(type_name="contact", fields={"name": "No Blob Info"})
        tracker = ChangeTracker(vault_dir)
        tracker.update_blob_info(meta.uuid)

    def test_update_blob_info_missing_body(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Missing Body Info")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        os.unlink(os.path.join(storage_dir, "data.md"))
        tracker = ChangeTracker(vault_dir)
        tracker.update_blob_info(meta.uuid)

    def test_status_with_corrupt_metadata(self, vault_dir):
        import uuid
        bad_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, bad_uid)
        os.makedirs(storage_dir, exist_ok=True)
        with open(NodeMetadata.metadata_path(storage_dir), "w") as f:
            f.write("not [[valid toml\n")
        tracker = ChangeTracker(vault_dir)
        status = tracker.status()
        assert "changed" in status

    def test_status_with_orphaned_node(self, vault_dir):
        with open(os.path.join(vault_dir, ".metadata", "index.txt"), "a") as f:
            f.write("orphaned-uuid-000000000000000\n")
        tracker = ChangeTracker(vault_dir)
        status = tracker.status()
        assert len(status["orphaned"]) > 0

    def test_status_with_new_file(self, vault_dir):
        with open(os.path.join(vault_dir, "new_file.txt"), "w") as f:
            f.write("new file")
        tracker = ChangeTracker(vault_dir)
        status = tracker.status()
        assert len(status["new_files"]) > 0
