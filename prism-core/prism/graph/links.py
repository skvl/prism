"""Link extraction, backlink indexing, and graph export.

Extracts [[uuid]] links from node bodies, builds reverse indexes,
and exports graphs in DOT or JSON format.
"""

import json
import os
import re
from typing import Any, Optional

from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.vault.registry import VaultRegistry

UUID_RE = re.compile(r"\[\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]\]")
CROSS_VAULT_RE = re.compile(
    r"\[\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})::"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]\]"
)


class LinkExtractor:
    """Extracts [[uuid]] links from node body text.

    Supports both vault-internal links and cross-vault references.
    """

    @staticmethod
    def extract_links(body: str) -> list[dict[str, str]]:
        """Extract [[uuid]] links from a body string.

        Args:
            body: Text content to scan for links.

        Returns:
            List of link dicts with target, type, and title keys.
        """
        links: list[dict[str, str]] = []
        seen: set[str] = set()

        for match in UUID_RE.finditer(body):
            uid = match.group(1)
            if uid not in seen:
                seen.add(uid)
                links.append({"target": uid, "type": "", "title": ""})

        for match in CROSS_VAULT_RE.finditer(body):
            vault_uid = match.group(1)
            target_uid = match.group(2)
            key = f"{vault_uid}::{target_uid}"
            if key not in seen:
                seen.add(key)
                links.append({"target": target_uid, "vault": vault_uid, "type": "", "title": ""})

        return links

    @staticmethod
    def extract_from_file(path: str) -> list[dict[str, str]]:
        """Extract [[uuid]] links from a file.

        Args:
            path: Path to the file to scan.

        Returns:
            List of link dicts.
        """
        with open(path) as f:
            body = f.read()
        return LinkExtractor.extract_links(body)


class BacklinkIndex:
    """Builds and queries a reverse index of links targeting each node."""

    def __init__(self, vault_path: str) -> None:
        """Initialize the backlink index.

        Args:
            vault_path: Root path of the vault.
        """
        self.vault_path = vault_path

    def build(self) -> dict[str, list[dict[str, str]]]:
        """Build the full backlink index.

        Walks all metadata.toml files and indexes links by target.

        Returns:
            Dict mapping target UUID to list of source node info.
        """
        index: dict[str, list[dict[str, str]]] = {}
        storage_dir = os.path.join(self.vault_path, ".storage")
        if not os.path.exists(storage_dir):
            return index

        for root, _dirs, files in os.walk(storage_dir):
            for fname in files:
                if fname == "metadata.toml":
                    try:
                        meta = NodeMetadata.from_toml(os.path.join(root, fname))
                        for link in meta.links:
                            target = link.get("target", "")
                            if target:
                                if target not in index:
                                    index[target] = []
                                index[target].append(
                                    {
                                        "uuid": meta.uuid,
                                        "title": meta.title,
                                        "type": meta.type,
                                    }
                                )
                    except Exception:
                        continue
        return index

    def get_backlinks(self, uid: str) -> list[dict[str, str]]:
        """Get all nodes that link to the given UUID.

        Args:
            uid: Target UUID to find backlinks for.

        Returns:
            List of source node info dicts.
        """
        index = self.build()
        return index.get(uid, [])


class GraphExporter:
    """Exports the node graph in DOT or JSON format."""

    def __init__(self, vault_path: str) -> None:
        """Initialize the graph exporter.

        Args:
            vault_path: Root path of the vault.
        """
        self.vault_path = vault_path

    def export_dot(self, nodes: list[NodeMetadata], include_paths: bool = False) -> str:
        """Export the graph as DOT format.

        Args:
            nodes: List of all nodes to include.
            include_paths: Whether to include path nodes.

        Returns:
            DOT graph string.
        """
        filtered = self._filter_nodes(nodes, include_paths)
        lines = ["digraph Prism {", "  rankdir=LR;", "  node [shape=box, style=rounded];"]
        for node in filtered:
            label = node.title or node.uuid[:8]
            lines.append(f'  "{node.uuid}" [label="{label}\\n({node.type})"];')
        for node in filtered:
            for link in node.links:
                lines.append(f'  "{node.uuid}" -> "{link.get("target", "")}";')
        lines.append("}")
        return "\n".join(lines)

    def export_json(self, nodes: list[NodeMetadata], include_paths: bool = False) -> str:
        """Export the graph as JSON format.

        Args:
            nodes: List of all nodes to include.
            include_paths: Whether to include path nodes.

        Returns:
            JSON string with nodes and edges arrays.
        """
        filtered = self._filter_nodes(nodes, include_paths)
        export_nodes: list[dict[str, Any]] = []
        for node in filtered:
            export_nodes.append(
                {
                    "uuid": node.uuid,
                    "title": node.title,
                    "type": node.type,
                    "tags": node.tags,
                }
            )

        export_edges: list[dict[str, Any]] = []
        for node in filtered:
            for link in node.links:
                export_edges.append(
                    {
                        "source": node.uuid,
                        "target": link.get("target", ""),
                    }
                )

        return json.dumps({"nodes": export_nodes, "edges": export_edges}, indent=2)

    @staticmethod
    def _filter_nodes(nodes: list[NodeMetadata], include_paths: bool) -> list[NodeMetadata]:
        if include_paths:
            return nodes
        return [n for n in nodes if n.type != "path"]

    @staticmethod
    def resolve_cross_vault_link(vault_uuid: str, target_uuid: str) -> Optional[dict[str, str]]:
        """Resolve a cross-vault link to another vault.

        Args:
            vault_uuid: UUID of the source vault.
            target_uuid: UUID of the target node.

        Returns:
            Dict with uuid, title, type or None if not found.
        """
        registry = VaultRegistry()
        vault_info = registry.get_by_uuid(vault_uuid)
        if vault_info is None:
            return None

        vault_path = vault_info.get("path", "")
        storage_dir = compute_storage_path(vault_path, target_uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return None

        try:
            meta = NodeMetadata.from_toml(meta_path)
            return {"uuid": meta.uuid, "title": meta.title, "type": meta.type}
        except Exception:
            return None
