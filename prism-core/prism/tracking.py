"""Change detection and tracking.

Detects modified nodes, new files, orphaned nodes,
and coordinates re-extraction of links and blob metadata.
"""

import os
from datetime import datetime, timezone
from typing import Optional

from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path, sha256_file
from prism.graph.links import LinkExtractor


class ChangeTracker:
    """Tracks changes to vault nodes: modified bodies, new files, orphaned nodes."""
    def __init__(self, vault_path: str) -> None:
        """Initialize the change tracker.

        Args:
            vault_path: Root path of the vault.
        """
        self.vault_path = vault_path
        self.manager = NodeManager(vault_path)

    def status(self) -> dict[str, list[dict[str, str]]]:
        """Get the current vault status report.

        Returns:
            Dict with changed, new_files, and orphaned lists.
        """
        changed_nodes: list[dict[str, str]] = []
        new_files: list[dict[str, str]] = []
        orphaned_nodes: list[dict[str, str]] = []

        storage_dir = os.path.join(self.vault_path, ".storage")
        index_path = os.path.join(self.vault_path, ".metadata", "index.txt")

        tracked_uids: set[str] = set()
        if os.path.exists(index_path):
            with open(index_path) as f:
                tracked_uids = {line.strip() for line in f if line.strip()}

        fs_uids: set[str] = set()

        if os.path.exists(storage_dir):
            for root, _dirs, files in os.walk(storage_dir):
                for fname in files:
                    if fname == "metadata.toml":
                        try:
                            meta = NodeMetadata.from_toml(os.path.join(root, fname))
                            fs_uids.add(meta.uuid)

                            if meta.blob_mtime:
                                body_path = os.path.join(root, f"data.{meta.blob_extension}") if meta.blob_extension else None
                                if body_path and os.path.exists(body_path):
                                    current_mtime = str(os.stat(body_path).st_mtime)
                                    if current_mtime != meta.blob_mtime:
                                        changed_nodes.append({
                                            "uuid": meta.uuid,
                                            "title": meta.title,
                                            "type": meta.type,
                                        })
                        except Exception:
                            continue

        orphaned_uids = tracked_uids - fs_uids
        for uid in sorted(orphaned_uids):
            orphaned_nodes.append({"uuid": uid})

        vault_path_obj = os.path.abspath(self.vault_path)
        if os.path.exists(vault_path_obj):
            for entry in os.listdir(vault_path_obj):
                full_path = os.path.join(vault_path_obj, entry)
                if entry.startswith(".") or os.path.isdir(full_path) or entry == "index.txt":
                    continue
                if entry not in tracked_uids:
                    new_files.append({"path": entry})

        return {
            "changed": changed_nodes,
            "new_files": new_files,
            "orphaned": orphaned_nodes,
        }

    def mark_dirty(self, uid: str) -> None:
        """Mark a node as dirty in its metadata.

        Args:
            uid: UUID of the node.
        """
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return
        meta = NodeMetadata.from_toml(meta_path)
        meta.sync_dirty = True
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.save(meta_path)

    def re_extract_links(self, uid: str) -> bool:
        """Re-extract [[uuid]] links from a node's body.

        Args:
            uid: UUID of the node.

        Returns:
            True if links were re-extracted, False if no body exists.
        """
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return False

        meta = NodeMetadata.from_toml(meta_path)
        if not meta.blob_extension:
            return False

        body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
        if not os.path.exists(body_path):
            return False

        new_links = LinkExtractor.extract_from_file(body_path)
        meta.links = new_links
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        meta.save(meta_path)
        return True

    def update_blob_info(self, uid: str) -> None:
        """Update a node's blob metadata (mtime, size, sha256) from disk.

        Args:
            uid: UUID of the node.
        """
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return

        meta = NodeMetadata.from_toml(meta_path)
        if not meta.blob_extension:
            return

        body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
        if not os.path.exists(body_path):
            return

        stat_info = os.stat(body_path)
        meta.blob_mtime = str(stat_info.st_mtime)
        meta.blob_size = stat_info.st_size
        meta.blob_sha256 = sha256_file(body_path)
        meta.sync_dirty = True
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.save(meta_path)
