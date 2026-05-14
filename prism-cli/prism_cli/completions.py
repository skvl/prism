import os
from typing import Optional

from prism.node.manager import NodeManager
from prism.path.resolver import PathResolver
from prism.types.loader import TypeLoader

__all__ = [
    "resolve_completions",
    "complete_command",
    "complete_uuid",
    "complete_type_name",
    "complete_tag",
    "complete_path",
]


def complete_command(text: str, aliases: dict[str, str]) -> list[str]:
    all_commands = sorted(set(
        list(aliases.keys())
        + list(aliases.values())
        + ["init", "open", "help", "history", "exit", "quit", "rm", "path"]
    ))
    if not text:
        return all_commands
    return [c for c in all_commands if c.startswith(text)]


def complete_uuid(vault: Optional[object], text: str) -> list[str]:
    if vault is None:
        return []
    manager = NodeManager(vault.path)
    try:
        nodes = manager.list_nodes()
    except Exception:
        return []
    if not text:
        return [n.uuid for n in nodes]
    return [n.uuid for n in nodes if n.uuid.startswith(text)]


def complete_type_name(vault: Optional[object], text: str) -> list[str]:
    if vault is None:
        return []
    types_dir = os.path.join(vault.path, ".metadata", "types")
    loader = TypeLoader(types_dir)
    schemas = loader.load_all()
    names = list(schemas.keys())
    if not text:
        return names
    return [n for n in names if n.startswith(text)]


def complete_tag(vault: Optional[object], text: str) -> list[str]:
    if vault is None:
        return []
    tags: set[str] = set()
    manager = NodeManager(vault.path)
    try:
        for node in manager.list_nodes():
            tags.update(node.tags)
    except Exception:
        return []
    if not text:
        return sorted(tags)
    return sorted(t for t in tags if t.startswith(text))


def complete_path(vault: Optional[object], text: str) -> list[str]:
    if vault is None:
        return []
    path_prefix = text
    if text.startswith("path:"):
        path_prefix = text[5:]
    resolver = PathResolver(vault.path)
    try:
        completions = resolver.complete(path_prefix)
    except Exception:
        return []
    if text.startswith("path:"):
        return [f"path:{p}" for p in completions]
    return completions


def resolve_completions(
    parts: list[str],
    text: str,
    vault: Optional[object],
    aliases: dict[str, str],
) -> list[str]:
    if not parts or (len(parts) == 1 and text):
        return complete_command(text, aliases)

    cmd = aliases.get(parts[0], parts[0])

    if cmd == "path":
        subs = ["create", "rm", "tree"]
        if len(parts) == 1:
            return [s for s in subs if s.startswith(text)] if text else subs
        if len(parts) == 2:
            if text:
                return [s for s in subs if s.startswith(text)]
            return subs
        if len(parts) >= 3 and parts[1] in subs:
            return complete_path(vault, text)
        return []

    if cmd == "tag":
        subs = ["add", "rm", "list", "rename"]
        if len(parts) == 1:
            return [s for s in subs if s.startswith(text)] if text else subs
        if len(parts) == 2:
            if text:
                return [s for s in subs if s.startswith(text)]
            return subs
        if len(parts) >= 3:
            sub = parts[1]
            if sub in ("add", "rm"):
                if len(parts) == 3:
                    return complete_uuid(vault, text)
                if sub == "rm":
                    return complete_tag(vault, text)
            elif sub == "rename":
                return complete_tag(vault, text)
        return []

    if text.startswith("path:"):
        return complete_path(vault, text)

    for i, part in enumerate(parts):
        if part in ("--tag", "-t") and i + 1 >= len(parts):
            return complete_tag(vault, text)
        if part in ("--add-path", "-a", "--remove-path", "-r") and i + 1 >= len(parts):
            return complete_path(vault, text)

    if cmd == "new" and len(parts) <= 2 and text:
        return complete_type_name(vault, text)

    return complete_uuid(vault, text)
