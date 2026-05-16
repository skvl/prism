"""Node CRUD operations.

Provides NodeManager for creating, editing, deleting, and querying nodes,
plus a resolve_uuid helper for partial UUID matching.
"""

import os
import shutil
from datetime import datetime, timezone
from typing import Any, Optional

from prism.node.metadata import TAG_PATTERN, NodeMetadata
from prism.node.storage import StorageEngine, compute_storage_path, sha256_file
from prism.path.resolver import PathResolver
from prism.types.loader import TypeLoader
from prism.types.schema import TypeSchema
from prism.types.validator import FieldValidator
from prism.vault.vault import generate_uuid


def resolve_uuid(vault_path: str, partial: str) -> str:
    """Resolve a partial UUID to a full 36-character UUID.

    Searches all metadata.toml files in .storage for a node whose
    UUID starts with the given prefix.

    Args:
        vault_path: Root path of the vault.
        partial: Full or partial UUID string.

    Returns:
        The full 36-character UUID string.

    Raises:
        ValueError: Zero or multiple matches found.
    """
    if len(partial) >= 36:
        return partial
    nodes = _list_all_nodes(vault_path)
    matches = [n.uuid for n in nodes if n.uuid.startswith(partial)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        short_matches = [m[:12] for m in matches]
        raise ValueError(f"Multiple nodes match partial UUID '{partial}': {short_matches}")
    raise ValueError(f"No node found matching UUID '{partial}'")


def _list_all_nodes(vault_path: str) -> list[NodeMetadata]:
    nodes: list[NodeMetadata] = []
    storage_dir = os.path.join(vault_path, ".storage")
    if not os.path.exists(storage_dir):
        return nodes
    for root, _dirs, files in os.walk(storage_dir):
        for fname in files:
            if fname == "metadata.toml":
                try:
                    meta = NodeMetadata.from_toml(os.path.join(root, fname))
                    nodes.append(meta)
                except Exception:
                    continue
    return nodes


class NodeManager:
    """Manages node CRUD operations within a vault.

    Handles creating, editing, deleting, and querying nodes,
    including tag management and path associations.
    """

    def __init__(self, vault_path: str) -> None:
        """Initialize the node manager.

        Args:
            vault_path: Root path of the vault.
        """
        self.vault_path = vault_path
        self.storage = StorageEngine(vault_path)
        self.types_dir = os.path.join(vault_path, ".metadata", "types")
        self.type_loader = TypeLoader(self.types_dir)
        self.index_path = os.path.join(vault_path, ".metadata", "index.txt")

    def _resolve_uuid(self, uid: str) -> str:
        return resolve_uuid(self.vault_path, uid)

    def create_node(
        self,
        type_name: str,
        title: str = "",
        fields: Optional[dict[str, Any]] = None,
        blob_path: Optional[str] = None,
        tags: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> NodeMetadata:
        """Create a new node of the given type.

        Args:
            type_name: Type identifier for the node.
            title: Optional title for the node.
            fields: Optional field values.
            blob_path: Optional path to a file to import as blob.
            tags: Optional list of tags.
            description: Optional description text (written to description.md).

        Returns:
            The newly created NodeMetadata.

        Raises:
            ValueError: If type is unknown, validation fails, or type is 'path'.
        """
        if type_name == "path":
            raise ValueError(
                "Path nodes cannot be created via `prism new`. Use `prism path create` instead."
            )

        schema = self.type_loader.load(type_name)
        if schema is None:
            raise ValueError(f"Unknown type: {type_name}")

        field_values: dict[str, Any] = {}
        if fields:
            field_values.update(fields)
        if title:
            field_values.setdefault("title", title)

        validator = FieldValidator(schema)
        errors = validator.validate(field_values)
        field_errors = [e for e in errors if "required" in e]
        if field_errors:
            raise ValueError("\n".join(field_errors))

        uid = str(generate_uuid())
        now = datetime.now(timezone.utc).isoformat()

        meta = NodeMetadata(
            uuid=uid,
            type=type_name,
            title=title,
            tags=tags or [],
            fields={k: v for k, v in field_values.items() if k not in ("title", "tags")},
            created_at=now,
            updated_at=now,
            sync_dirty=True,
        )

        storage_dir = compute_storage_path(self.vault_path, uid)
        os.makedirs(storage_dir, exist_ok=True)

        if blob_path and os.path.isfile(blob_path):
            dest = self.storage.import_blob(blob_path, uid)
            ext = os.path.splitext(blob_path)[1]
            meta.blob_extension = ext.lstrip(".")
            stat_info = os.stat(dest)
            meta.blob_mtime = str(stat_info.st_mtime)
            meta.blob_size = stat_info.st_size
            meta.blob_sha256 = sha256_file(dest)
        elif schema.body_model == "file(markdown)":
            body_path = os.path.join(storage_dir, "data.md")
            with open(body_path, "w") as f:
                f.write(f"# {title}\n\n")
            meta.blob_extension = "md"
            stat_info = os.stat(body_path)
            meta.blob_mtime = str(stat_info.st_mtime)
            meta.blob_size = stat_info.st_size
            meta.blob_sha256 = sha256_file(body_path)

        if description is not None:
            sha256_val, mtime_val, size_val = self.storage.write_description(uid, description)
            meta.desc_sha256 = sha256_val
            meta.desc_mtime = mtime_val
            meta.desc_size = size_val

        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta.save(meta_path)

        self._index_add(uid)

        return meta

    def get_body_info(self, uid: str) -> tuple[str, float] | None:
        """Get the body file path and modification time for a node.

        Args:
            uid: UUID of the node (full or partial).

        Returns:
            Tuple of (body_path, mtime) or None if no body exists.
        """
        uid = self._resolve_uuid(uid)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        if not meta.blob_extension:
            return None
        body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
        if not os.path.exists(body_path):
            return None
        return (body_path, os.stat(body_path).st_mtime)

    def commit_body_edit(self, uid: str, mtime: float, size: int, sha256: str) -> None:
        """Commit an edited body, updating metadata and re-extracting links.

        Args:
            uid: UUID of the node (full or partial).
            mtime: New modification time.
            size: New file size.
            sha256: New SHA-256 hash.
        """
        uid = self._resolve_uuid(uid)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        meta.blob_mtime = str(mtime)
        meta.blob_size = size
        meta.blob_sha256 = sha256
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        if meta.blob_extension == "md":
            from prism.graph.links import LinkExtractor

            body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
            if os.path.exists(body_path):
                meta.links = LinkExtractor.extract_from_file(body_path)
        meta.save(meta_path)

    def set_description(self, uid: str, description: str) -> None:
        """Set, update, or clear a node's description.

        Creates or updates description.md if description is non-empty;
        deletes it and clears tracking fields if description is empty.

        Args:
            uid: UUID of the node (full or partial).
            description: Description text (empty string clears).
        """
        uid = self._resolve_uuid(uid)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)

        sha256_val, mtime_val, size_val = self.storage.write_description(uid, description)

        meta.desc_sha256 = sha256_val
        meta.desc_mtime = mtime_val
        meta.desc_size = size_val
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True

        if description:
            from prism.graph.links import LinkExtractor

            desc_path = NodeMetadata.description_path(storage_dir)
            meta.links = LinkExtractor.extract_from_file(desc_path)

        meta.save(meta_path)

    def get_field_info(self, uid: str) -> tuple[TypeSchema, dict[str, Any]]:
        """Get the type schema and current field values for a node.

        Args:
            uid: UUID of the node (full or partial).

        Returns:
            Tuple of (TypeSchema, field_values dict).

        Raises:
            ValueError: If the node's type is unknown.
        """
        uid = self._resolve_uuid(uid)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        schema = self.type_loader.load(meta.type)
        if schema is None:
            raise ValueError(f"Unknown type: {meta.type}")
        return (schema, dict(meta.fields))

    def update_node_fields(self, uid: str, changes: dict[str, Any]) -> bool:
        """Update field values on a node.

        Args:
            uid: UUID of the node (full or partial).
            changes: Dictionary of field name to new value.

        Returns:
            True if changes were applied, False if no changes provided.
        """
        if not changes:
            return False
        uid = self._resolve_uuid(uid)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        for k, v in changes.items():
            meta.fields[k] = v
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        meta.save(meta_path)
        return True

    def delete_node(self, uid: str, force: bool = False) -> bool:
        """Delete a node and its storage directory.

        Args:
            uid: UUID of the node (full or partial).
            force: If True, skip backlink check.

        Returns:
            True if deleted, False if not found.

        Raises:
            ValueError: If backlinks exist and force is False.
        """
        uid = self._resolve_uuid(uid)
        storage_dir = compute_storage_path(self.vault_path, uid)
        if not os.path.exists(storage_dir):
            return False

        if not force:
            backlinks = self._find_backlinks(uid)
            if backlinks:
                raise ValueError(
                    f"{len(backlinks)} node(s) link to this node. Use --yes to force deletion."
                )

        shutil.rmtree(storage_dir)
        self._index_remove(uid)
        return True

    def show_node(self, uid: str, show_description: bool = False) -> Optional[str]:
        """Get a formatted display string for a node.

        Args:
            uid: UUID of the node (full or partial).
            show_description: Whether to include the description section.

        Returns:
            Formatted string or None if not found.
        """
        uid = self._resolve_uuid(uid)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return None

        meta = NodeMetadata.from_toml(meta_path)

        lines: list[str] = []
        lines.append(f"UUID:   {meta.uuid}")
        lines.append(f"Type:   {meta.type}")
        if meta.title:
            lines.append(f"Title:  {meta.title}")
        if meta.tags:
            lines.append(f"Tags:   {', '.join(meta.tags)}")
        if meta.paths:
            resolver = PathResolver(self.vault_path)
            resolved_paths: list[str] = []
            for puid in meta.paths:
                try:
                    resolved_paths.append(resolver.resolve_uuid_to_path(puid))
                except Exception:
                    resolved_paths.append(puid[:8])
            lines.append(f"Paths:  {', '.join(resolved_paths)}")
        if meta.fields:
            for k, v in meta.fields.items():
                lines.append(f"  {k}: {v}")
        if meta.links:
            lines.append("Links:")
            for link in meta.links:
                lines.append(f"  -> {link.get('target', '?')} ({link.get('title', 'untitled')})")
        lines.append(f"Created: {meta.created_at}")
        lines.append(f"Updated: {meta.updated_at}")

        if show_description and self._has_description(storage_dir):
            desc_path = NodeMetadata.description_path(storage_dir)
            with open(desc_path) as f:
                desc_text = f.read()
            lines.append(f"\nDescription:\n{desc_text}")

        if meta.blob_extension:
            body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
            if os.path.exists(body_path) and meta.blob_extension == "md":
                with open(body_path) as f:
                    body_lines = f.readlines()
                preview = "".join(body_lines[:20])
                lines.append(f"\nBody (first 20 lines):\n{preview}")

        return "\n".join(lines)

    @staticmethod
    def _has_description(storage_dir: str) -> bool:
        desc_path = NodeMetadata.description_path(storage_dir)
        return os.path.exists(desc_path)

    def _index_add(self, uid: str) -> None:
        with open(self.index_path, "a") as f:
            f.write(f"{uid}\n")

    def _index_remove(self, uid: str) -> None:
        if not os.path.exists(self.index_path):
            return
        with open(self.index_path) as f:
            uids = [line.strip() for line in f if line.strip() != uid]
        with open(self.index_path, "w") as f:
            for u in uids:
                f.write(f"{u}\n")

    def rebuild_index(self) -> None:
        """Rebuild the index.txt from all nodes found in .storage.

        Walks the .storage directory tree, collects all node UUIDs,
        sorts them, and writes them to index.txt.
        """
        storage_dir = os.path.join(self.vault_path, ".storage")
        uids: list[str] = []
        if os.path.exists(storage_dir):
            for root, dirs, _files in os.walk(storage_dir):
                for d in dirs:
                    meta_path = os.path.join(root, d, "metadata.toml")
                    if os.path.exists(meta_path):
                        meta = NodeMetadata.from_toml(meta_path)
                        uids.append(meta.uuid)
        uids.sort()
        with open(self.index_path, "w") as f:
            for uid in uids:
                f.write(f"{uid}\n")

    def _find_backlinks(self, uid: str) -> list[dict[str, str]]:
        uid = self._resolve_uuid(uid)
        result: list[dict[str, str]] = []
        storage_dir = os.path.join(self.vault_path, ".storage")
        if not os.path.exists(storage_dir):
            return result

        for root, _dirs, files in os.walk(storage_dir):
            for fname in files:
                if fname == "metadata.toml":
                    try:
                        meta = NodeMetadata.from_toml(os.path.join(root, fname))
                        for link in meta.links:
                            if link.get("target") == uid:
                                result.append(
                                    {
                                        "uuid": meta.uuid,
                                        "title": meta.title,
                                        "type": meta.type,
                                    }
                                )
                    except Exception:
                        continue
        return result

    def get_description(self, uid: str) -> Optional[str]:
        """Get the description text for a node.

        Args:
            uid: UUID of the node (full or partial).

        Returns:
            Description text, or None if the node has no description.
        """
        uid = self._resolve_uuid(uid)
        return self.storage.read_description(uid)

    def list_nodes(self) -> list[NodeMetadata]:
        """List all nodes in the vault.

        Returns:
            List of NodeMetadata for all discovered nodes.
        """
        return _list_all_nodes(self.vault_path)

    def add_path_to_node(self, uid: str, path_str: str) -> bool:
        """Associate a node with a path.

        Args:
            uid: UUID of the node.
            path_str: Path string to associate.

        Returns:
            True if path was added, False if already associated.
        """
        uid = self._resolve_uuid(uid)
        resolver = PathResolver(self.vault_path)
        path_uuid = resolver.resolve(path_str)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        if path_uuid in meta.paths:
            return False
        meta.paths.append(path_uuid)
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        meta.save(meta_path)
        return True

    def remove_path_from_node(self, uid: str, path_str: str) -> bool:
        """Remove a path association from a node.

        Args:
            uid: UUID of the node.
            path_str: Path string to remove.

        Returns:
            True if path was removed, False if not associated.
        """
        uid = self._resolve_uuid(uid)
        resolver = PathResolver(self.vault_path)
        path_uuid = resolver.resolve(path_str)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        if path_uuid not in meta.paths:
            return False
        meta.paths = [p for p in meta.paths if p != path_uuid]
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        meta.save(meta_path)
        return True

    def add_tag(self, uid: str, tag: str) -> bool:
        """Add a tag to a node.

        Args:
            uid: UUID of the node.
            tag: Tag string to add.

        Returns:
            True if tag was added, False if already present.

        Raises:
            ValueError: If tag format is invalid.
        """
        uid = self._resolve_uuid(uid)
        if not TAG_PATTERN.match(tag):
            raise ValueError(f"Invalid tag: {tag!r}")
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            raise ValueError(f"Node not found: {uid}")
        meta = NodeMetadata.from_toml(meta_path)
        if tag in meta.tags:
            return False
        meta.tags.append(tag)
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        meta.save(meta_path)
        return True

    def remove_tag(self, uid: str, tag: str) -> bool:
        """Remove a tag from a node.

        Args:
            uid: UUID of the node.
            tag: Tag string to remove.

        Returns:
            True if tag was removed, False if not present.
        """
        uid = self._resolve_uuid(uid)
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            raise ValueError(f"Node not found: {uid}")
        meta = NodeMetadata.from_toml(meta_path)
        if tag not in meta.tags:
            return False
        meta.tags = [t for t in meta.tags if t != tag]
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        meta.save(meta_path)
        return True

    def list_tags(self) -> dict[str, int]:
        """List all unique tags across the vault with counts.

        Returns:
            Dictionary mapping tag name to node count.
        """
        tag_counts: dict[str, int] = {}
        for node in self.list_nodes():
            for tag in node.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return dict(sorted(tag_counts.items()))

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        """Rename a tag across all nodes in the vault.

        Args:
            old_tag: Current tag name.
            new_tag: New tag name.

        Returns:
            Number of nodes affected.

        Raises:
            ValueError: If new tag format is invalid.
        """
        if not TAG_PATTERN.match(new_tag):
            raise ValueError(f"Invalid tag: {new_tag!r}")
        if old_tag == new_tag:
            return 0
        affected = 0
        for node in self.list_nodes():
            if old_tag not in node.tags:
                continue
            storage_dir = compute_storage_path(self.vault_path, node.uuid)
            meta_path = NodeMetadata.metadata_path(storage_dir)
            meta = NodeMetadata.from_toml(meta_path)
            new_tags = [t for t in meta.tags if t != old_tag]
            if new_tag not in new_tags:
                new_tags.append(new_tag)
            meta.tags = new_tags
            meta.updated_at = datetime.now(timezone.utc).isoformat()
            meta.sync_dirty = True
            meta.save(meta_path)
            affected += 1
        return affected
