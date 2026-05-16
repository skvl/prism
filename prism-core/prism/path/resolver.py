"""Path hierarchy resolution.

Resolves, creates, and traverses path segments in the vault's
path node tree.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import tomlkit

from prism.node.metadata import SEGMENT_PATTERN, NodeMetadata
from prism.node.storage import compute_storage_path
from prism.vault.vault import generate_uuid


class PathResolver:
    """Resolves, creates, and traverses path segments in the vault's path node tree.

    Paths are hierarchical (/foo/bar/baz) and resolved through linked path nodes.
    """
    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path
        self._root_uuid: Optional[str] = None

    def _load_root_uuid(self) -> str:
        if self._root_uuid is not None:
            return self._root_uuid
        vault_toml_path = os.path.join(self.vault_path, ".metadata", "vault.toml")
        with open(vault_toml_path) as f:
            doc = tomlkit.load(f)
        root: str = doc.get("path_root_uuid")  # type: ignore[assignment]
        if not root:
            raise ValueError("No path root configured in vault. Re-initialize vault.")
        self._root_uuid = root
        return root

    def all_nodes(self) -> list[NodeMetadata]:
        nodes: list[NodeMetadata] = []
        storage_dir = os.path.join(self.vault_path, ".storage")
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

    def find_children(self, parent_uuid: str, nodes: list[NodeMetadata]) -> list[NodeMetadata]:
        children: list[NodeMetadata] = []
        for n in nodes:
            for link in n.links:
                if link.get("target") == parent_uuid and link.get("type") == "path-parent":
                    children.append(n)
                    break
        return children

    def resolve(self, path_string: str) -> str:
        """Resolve a path string to a node UUID.

        Args:
            path_string: Absolute path starting with /.

        Returns:
            UUID of the leaf path node.

        Raises:
            ValueError: If path is invalid or a segment doesn't exist.
        """
        path_string = path_string.strip()
        if not path_string.startswith("/"):
            raise ValueError("Path must start with /")

        if path_string == "/":
            return self._load_root_uuid()

        segments = [s for s in path_string.strip("/").split("/") if s]
        root_uuid = self._load_root_uuid()
        nodes = self.all_nodes()

        current_uuid = root_uuid
        for segment in segments:
            children = self.find_children(current_uuid, nodes)
            found = False
            for child in children:
                if child.fields.get("name") == segment:
                    current_uuid = child.uuid
                    found = True
                    break
            if not found:
                segment_path = '/'.join(segments[:segments.index(segment) + 1])
                raise ValueError(f"Path segment not found: /{segment_path}")

        return current_uuid

    def resolve_or_create(self, path_string: str) -> str:
        """Resolve a path, creating any missing segments (mkdir -p style).

        Args:
            path_string: Absolute path starting with /.

        Returns:
            UUID of the leaf path node.

        Raises:
            ValueError: If path is invalid or contains invalid characters.
        """
        path_string = path_string.strip()
        if not path_string.startswith("/"):
            raise ValueError("Path must start with /")

        if path_string == "/":
            return self._load_root_uuid()

        segments = [s for s in path_string.strip("/").split("/") if s]
        for seg in segments:
            if not SEGMENT_PATTERN.match(seg):
                raise ValueError(f"Invalid path segment character: {seg!r}")

        root_uuid = self._load_root_uuid()
        nodes = self.all_nodes()

        current_uuid = root_uuid
        for segment in segments:
            children = self.find_children(current_uuid, nodes)
            found = False
            for child in children:
                if child.fields.get("name") == segment:
                    current_uuid = child.uuid
                    found = True
                    break
            if not found:
                uid = str(generate_uuid())
                now = datetime.now(timezone.utc).isoformat()
                meta = NodeMetadata(
                    uuid=uid,
                    type="path",
                    title=segment,
                    fields={"name": segment},
                    links=[{"target": current_uuid, "type": "path-parent", "title": ".."}],
                    created_at=now,
                    updated_at=now,
                    sync_dirty=True,
                )
                storage_dir = compute_storage_path(self.vault_path, uid)
                os.makedirs(storage_dir, exist_ok=True)
                meta_path = NodeMetadata.metadata_path(storage_dir)
                meta.save(meta_path)
                nodes.append(meta)
                current_uuid = uid

        return current_uuid

    def collect_descendants(self, uuid: str) -> list[str]:
        """Collect all descendant path UUIDs under the given path node.

        Args:
            uuid: UUID of the parent path node.

        Returns:
            List of descendant UUIDs (BFS traversal).
        """
        nodes = self.all_nodes()
        descendants: list[str] = []
        queue = [uuid]
        visited: set[str] = {uuid}

        while queue:
            current = queue.pop(0)
            children = self.find_children(current, nodes)
            for child in children:
                if child.uuid not in visited:
                    visited.add(child.uuid)
                    descendants.append(child.uuid)
                    queue.append(child.uuid)

        return descendants

    def _would_create_cycle(self, parent_uuid: str, child_uuid: str) -> bool:
        descendants = self.collect_descendants(child_uuid)
        return parent_uuid in descendants

    def complete(self, prefix_path: str) -> list[str]:
        """Tab-complete partial paths.

        Args:
            prefix_path: Partial path to complete.

        Returns:
            Sorted list of matching full paths.
        """
        prefix_path = prefix_path.strip()
        if not prefix_path.startswith("/"):
            return []

        parent_path, _, partial_segment = prefix_path.rpartition("/")
        if parent_path == "":
            parent_path = "/"

        try:
            parent_uuid = self.resolve(parent_path if parent_path else "/")
        except (ValueError, KeyError):
            return []

        nodes = self.all_nodes()
        children = self.find_children(parent_uuid, nodes)

        matches: list[str] = []
        for child in children:
            name = child.fields.get("name", "")
            if name.startswith(partial_segment):
                full = f"{parent_path}/{name}" if parent_path != "/" else f"/{name}"
                matches.append(full)

        return sorted(matches)

    def resolve_uuid_to_path(self, uuid: str) -> str:
        """Resolve a node UUID back to its path string.

        Args:
            uuid: UUID of the path node.

        Returns:
            Full path string like /foo/bar.
        """
        nodes = self.all_nodes()
        nodes_by_uuid = {n.uuid: n for n in nodes}
        segments: list[str] = []
        current_uuid = uuid

        while current_uuid:
            node = nodes_by_uuid.get(current_uuid)
            if node is None:
                return ""
            name = node.fields.get("name", node.title or current_uuid[:8])

            if name == "/" and not segments:
                return "/"
            if name == "/":
                break

            segments.insert(0, name)
            parent_uuid = ""
            for link in node.links:
                if link.get("type") == "path-parent":
                    parent_uuid = link.get("target", "")
                    break
            current_uuid = parent_uuid

        return "/" + "/".join(segments)
