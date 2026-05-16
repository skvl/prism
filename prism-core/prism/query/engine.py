"""Query execution engine.

Evaluates QueryAST against a vault's nodes,
supporting tag/type/path filters and full-text search.
"""

import os
import subprocess
from typing import Any, Optional

from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.path.resolver import PathResolver
from prism.query.parser import QueryAST


class QueryEngine:
    """Executes QueryAST against a vault's nodes.

    Supports tag, type, path, and text search with AND/OR/NOT logic.
    """

    def __init__(self, vault_path: str) -> None:
        """Initialize the query engine.

        Args:
            vault_path: Root path of the vault.
        """
        self.vault_path = vault_path

    def execute(self, ast: QueryAST) -> list[NodeMetadata]:
        """Execute a query AST against the vault.

        Args:
            ast: The parsed query AST.

        Returns:
            List of matching NodeMetadata.
        """
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
                if current_op == "NOT":
                    exclude_ids = {id(n) for n in matched}
                    result = [n for n in nodes if id(n) not in exclude_ids]
                else:
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
            elif filter_type == "path":
                resolver = PathResolver(self.vault_path)
                try:
                    leaf_uuid = resolver.resolve(filter_value)
                except (ValueError, KeyError):
                    return []
                return [n for n in nodes if leaf_uuid in n.paths]
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
        storage_dir = compute_storage_path(self.vault_path, node.uuid)
        search_paths: list[str] = []
        if node.blob_extension == "md":
            body_path = os.path.join(storage_dir, f"data.{node.blob_extension}")
            if os.path.exists(body_path):
                search_paths.append(body_path)
        desc_path = os.path.join(storage_dir, "description.md")
        if os.path.exists(desc_path):
            search_paths.append(desc_path)
        for path in search_paths:
            try:
                result = subprocess.run(
                    ["grep", "-l", text, path],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return True
            except Exception:
                with open(path) as f:
                    if text in f.read().lower():
                        return True
        return False
