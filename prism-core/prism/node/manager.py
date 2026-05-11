import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from prism.node.metadata import NodeMetadata
from prism.node.storage import StorageEngine, compute_storage_path, sha256_file
from prism.types.loader import TypeLoader
from prism.types.schema import TypeSchema
from prism.types.validator import FieldValidator
from prism.vault.vault import generate_uuid


class NodeManager:
    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path
        self.storage = StorageEngine(vault_path)
        self.types_dir = os.path.join(vault_path, ".metadata", "types")
        self.type_loader = TypeLoader(self.types_dir)
        self.index_path = os.path.join(vault_path, ".metadata", "index.txt")

    def create_node(
        self,
        type_name: str,
        title: str = "",
        fields: Optional[dict[str, Any]] = None,
        blob_path: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> NodeMetadata:
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

        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta.save(meta_path)

        self._index_add(uid)

        return meta

    def edit_node_body(self, uid: str) -> bool:
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)

        body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}") if meta.blob_extension else None
        if not body_path or not os.path.exists(body_path):
            return False

        original_mtime = os.stat(body_path).st_mtime

        editor = os.environ.get("EDITOR", "vi")
        subprocess.call([editor, body_path])

        new_mtime = os.stat(body_path).st_mtime
        if new_mtime == original_mtime:
            print("No changes detected")
            return False

        meta.blob_mtime = str(new_mtime)
        meta.blob_size = os.stat(body_path).st_size
        meta.blob_sha256 = sha256_file(body_path)
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        meta.sync_dirty = True
        meta.save(meta_path)
        return True

    def edit_node_fields(self, uid: str) -> bool:
        storage_dir = compute_storage_path(self.vault_path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)

        schema = self.type_loader.load(meta.type)
        if schema is None:
            print(f"Unknown type: {meta.type}")
            return False

        changed = False
        for field_def in schema.fields:
            current = meta.fields.get(field_def.name, "")
            try:
                new_val = input(f"Enter new {field_def.name} or press ENTER to keep [{current}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if new_val:
                meta.fields[field_def.name] = new_val
                changed = True

        if changed:
            meta.updated_at = datetime.now(timezone.utc).isoformat()
            meta.sync_dirty = True
            meta.save(meta_path)

        return changed

    def delete_node(self, uid: str, force: bool = False) -> bool:
        storage_dir = compute_storage_path(self.vault_path, uid)
        if not os.path.exists(storage_dir):
            return False

        backlinks = self._find_backlinks(uid)
        if backlinks and not force:
            print(f"Warning: {len(backlinks)} node(s) link to this node. Links will become unresolved.")
            try:
                confirm = input("Delete anyway? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return False
            if confirm != "y":
                return False

        shutil.rmtree(storage_dir)
        self._index_remove(uid)
        return True

    def show_node(self, uid: str) -> Optional[str]:
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
        if meta.fields:
            for k, v in meta.fields.items():
                lines.append(f"  {k}: {v}")
        if meta.links:
            lines.append("Links:")
            for link in meta.links:
                lines.append(f"  -> {link.get('target', '?')} ({link.get('title', 'untitled')})")
        lines.append(f"Created: {meta.created_at}")
        lines.append(f"Updated: {meta.updated_at}")

        if meta.blob_extension:
            body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
            if os.path.exists(body_path) and meta.blob_extension == "md":
                with open(body_path) as f:
                    body_lines = f.readlines()
                preview = "".join(body_lines[:20])
                lines.append(f"\nBody (first 20 lines):\n{preview}")

        return "\n".join(lines)

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
                                result.append({"uuid": meta.uuid, "title": meta.title, "type": meta.type})
                    except Exception:
                        continue
        return result

    def list_nodes(self) -> list[NodeMetadata]:
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
