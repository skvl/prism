import json
import os
import subprocess
from typing import Any, Optional

from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.query.parser import QueryAST


class QueryEngine:
    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path

    def execute(self, ast: QueryAST) -> list[NodeMetadata]:
        nodes = self._all_nodes()
        if not ast.terms:
            return nodes

        result: Optional[list[NodeMetadata]] = None
        current_op: str = "AND"

        for term in ast.terms:
            if "op" in term:
                current_op = term["op"]
                continue

            matched = self._match(nodes, term)

            if result is None:
                result = matched
            elif current_op == "AND":
                result = [n for n in result if n in matched]
            elif current_op == "OR":
                combined = {id(n): n for n in result}
                combined.update({id(n): n for n in matched})
                result = list(combined.values())
            elif current_op == "NOT":
                exclude_ids = {id(n) for n in matched}
                result = [n for n in result if id(n) not in exclude_ids]

        return result or []

    def _all_nodes(self) -> list[NodeMetadata]:
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

    def _match(self, nodes: list[NodeMetadata], term: dict[str, Any]) -> list[NodeMetadata]:
        if "filter" in term:
            filter_type = term["filter"]
            filter_value = term["value"]
            if filter_type == "tag":
                return [n for n in nodes if filter_value in n.tags]
            elif filter_type == "type":
                return [n for n in nodes if n.type == filter_value]
        elif "text" in term:
            text = term["text"].lower()
            return [n for n in nodes if self._text_match(n, text)]
        return []

    def _text_match(self, node: NodeMetadata, text: str) -> bool:
        if text in node.title.lower():
            return True
        for val in node.fields.values():
            if isinstance(val, str) and text in val.lower():
                return True
        if node.blob_extension == "md":
            storage_dir = compute_storage_path(self.vault_path, node.uuid)
            body_path = os.path.join(storage_dir, f"data.{node.blob_extension}")
            if os.path.exists(body_path):
                try:
                    result = subprocess.run(
                        ["grep", "-l", text, body_path],
                        capture_output=True, text=True,
                    )
                    if result.returncode == 0:
                        return True
                except Exception:
                    with open(body_path) as f:
                        if text in f.read().lower():
                            return True
        return False
