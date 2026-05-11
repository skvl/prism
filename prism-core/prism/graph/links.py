import json
import os
import re
from pathlib import Path
from typing import Optional

from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.vault.registry import VaultRegistry

UUID_RE = re.compile(r"\[\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]\]")
CROSS_VAULT_RE = re.compile(
    r"\[\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})::"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]\]"
)


class LinkExtractor:
    @staticmethod
    def extract_links(body: str) -> list[dict[str, str]]:
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
        with open(path) as f:
            body = f.read()
        return LinkExtractor.extract_links(body)


class BacklinkIndex:
    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path

    def build(self) -> dict[str, list[dict[str, str]]]:
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
                                index[target].append({
                                    "uuid": meta.uuid,
                                    "title": meta.title,
                                    "type": meta.type,
                                })
                    except Exception:
                        continue
        return index

    def get_backlinks(self, uid: str) -> list[dict[str, str]]:
        index = self.build()
        return index.get(uid, [])


class GraphExporter:
    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path

    def export_dot(self, nodes: list[NodeMetadata]) -> str:
        lines = ['digraph Prism {', '  rankdir=LR;', '  node [shape=box, style=rounded];']
        for node in nodes:
            label = node.title or node.uuid[:8]
            lines.append(f'  "{node.uuid}" [label="{label}\\n({node.type})"];')
        for node in nodes:
            for link in node.links:
                lines.append(f'  "{node.uuid}" -> "{link.get("target", "")}";')
        lines.append('}')
        return "\n".join(lines)

    def export_json(self, nodes: list[NodeMetadata]) -> str:
        export_nodes: list[dict] = []
        for node in nodes:
            export_nodes.append({
                "uuid": node.uuid,
                "title": node.title,
                "type": node.type,
                "tags": node.tags,
            })

        export_edges: list[dict] = []
        for node in nodes:
            for link in node.links:
                export_edges.append({
                    "source": node.uuid,
                    "target": link.get("target", ""),
                })

        return json.dumps({"nodes": export_nodes, "edges": export_edges}, indent=2)

    @staticmethod
    def resolve_cross_vault_link(vault_uuid: str, target_uuid: str) -> Optional[dict[str, str]]:
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
