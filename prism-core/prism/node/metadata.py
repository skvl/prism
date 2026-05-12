import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import tomlkit


TAG_PATTERN = re.compile(r"\A[\w\-]+\Z")

SEGMENT_PATTERN = re.compile(r"\A[^\x00-\x1f\x7f/]+\Z")


@dataclass
class NodeMetadata:
    uuid: str
    type: str
    title: str = ""
    tags: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)
    links: list[dict[str, str]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    blob_extension: str = ""
    blob_mtime: str = ""
    blob_size: int = 0
    blob_sha256: str = ""
    sync_dirty: bool = False

    def __post_init__(self) -> None:
        for tag in self.tags:
            if not TAG_PATTERN.match(tag):
                raise ValueError(f"Invalid tag: {tag!r}")

    @classmethod
    def from_toml(cls, path: str) -> "NodeMetadata":
        with open(path) as f:
            doc = tomlkit.load(f)
        return cls(
            uuid=doc.get("uuid", ""),
            type=doc.get("type", ""),
            title=doc.get("title", ""),
            tags=list(doc.get("tags", [])),
            paths=list(doc.get("paths", [])),
            fields=dict(doc.get("fields", {})),
            links=list(doc.get("links", [])),
            created_at=doc.get("created_at", ""),
            updated_at=doc.get("updated_at", ""),
            blob_extension=doc.get("blob_extension", ""),
            blob_mtime=doc.get("blob_mtime", ""),
            blob_size=doc.get("blob_size", 0),
            blob_sha256=doc.get("blob_sha256", ""),
            sync_dirty=doc.get("sync_dirty", False),
        )

    def to_toml(self) -> str:
        doc = tomlkit.document()
        doc["uuid"] = self.uuid
        doc["type"] = self.type
        doc["title"] = self.title
        if self.tags:
            arr = tomlkit.array()
            for t in self.tags:
                arr.append(t)
            doc["tags"] = arr
        if self.paths:
            arr = tomlkit.array()
            for p in self.paths:
                arr.append(p)
            doc["paths"] = arr
        if self.fields:
            tbl = tomlkit.table()
            tbl.update(self.fields)
            doc["fields"] = tbl
        if self.links:
            arr = tomlkit.array()
            for link in self.links:
                itbl = tomlkit.inline_table()
                itbl.update(link)
                arr.append(itbl)
            arr.multiline(True)
            doc["links"] = arr
        doc["created_at"] = self.created_at or datetime.now(timezone.utc).isoformat()
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        if self.blob_extension:
            doc["blob_extension"] = self.blob_extension
        if self.blob_mtime:
            doc["blob_mtime"] = self.blob_mtime
        if self.blob_size:
            doc["blob_size"] = self.blob_size
        if self.blob_sha256:
            doc["blob_sha256"] = self.blob_sha256
        doc["sync_dirty"] = self.sync_dirty
        return tomlkit.dumps(doc)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_toml())

    @staticmethod
    def metadata_path(storage_dir: str) -> str:
        return os.path.join(storage_dir, "metadata.toml")
