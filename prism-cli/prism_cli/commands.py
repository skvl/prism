import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Optional

from prism.node.manager import NodeManager, resolve_uuid
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path, sha256_file
from prism.graph.links import BacklinkIndex, GraphExporter
from prism.path.resolver import PathResolver
from prism.query.parser import QueryParser
from prism.query.engine import QueryEngine
from prism.tracking import ChangeTracker
from prism.vault.vault import Vault
from prism.vault.registry import VaultRegistry


@dataclass
class CmdResult:
    ok: bool
    error: str = ""
    code: str = ""
    data: dict = field(default_factory=dict)


def write_builtin_types(vault: Vault) -> CmdResult:
    from prism.types.builtins import NOTE_TOML, CONTACT_TOML, BOOKMARK_TOML, FILE_TOML, PATH_TOML

    types_dir = os.path.join(vault.path, ".metadata", "types")
    os.makedirs(types_dir, exist_ok=True)

    types = {
        "note.toml": NOTE_TOML,
        "contact.toml": CONTACT_TOML,
        "bookmark.toml": BOOKMARK_TOML,
        "file.toml": FILE_TOML,
        "path.toml": PATH_TOML,
    }
    created = []
    skipped = []
    for fname, content in types.items():
        path = os.path.join(types_dir, fname)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(content)
            created.append(fname)
        else:
            skipped.append(fname)

    return CmdResult(ok=True, data={"created": created, "skipped": skipped})


def find_by_hash(manager: NodeManager, file_hash: str) -> CmdResult:
    for node in manager.list_nodes():
        if node.blob_sha256 == file_hash:
            return CmdResult(ok=True, data={"uuid": node.uuid, "title": node.title})
    return CmdResult(ok=False, code="NOT_FOUND", data={})


def init_vault(path: str) -> CmdResult:
    try:
        vault = Vault.init(path)
        write_builtin_types(vault)
        return CmdResult(ok=True, data={
            "vault": vault,
            "path": vault.path,
            "vault_uuid": vault.vault_uuid,
        })
    except FileExistsError as e:
        return CmdResult(ok=False, error=str(e), code="ALREADY_EXISTS", data={})


def open_vault(path: str) -> CmdResult:
    try:
        vault = Vault.open(path)
        return CmdResult(ok=True, data={"vault": vault, "path": vault.path})
    except FileNotFoundError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})


def show_node(vault: Vault, uuid: str) -> CmdResult:
    manager = NodeManager(vault.path)
    output = manager.show_node(uuid)
    if output is None:
        return CmdResult(ok=False, error=f"Node not found: {uuid}", code="NOT_FOUND", data={})
    return CmdResult(ok=True, data={"output": output})


def delete_node(vault: Vault, uuid: str, force: bool = False) -> CmdResult:
    manager = NodeManager(vault.path)
    try:
        if manager.delete_node(uuid, force=force):
            return CmdResult(ok=True, data={"uuid": uuid})
        return CmdResult(ok=False, error=f"Node not found: {uuid}", code="NOT_FOUND", data={})
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="CONFIRM_REQUIRED", data={"uuid": uuid})


def verify_node(vault: Vault, uuid: str) -> CmdResult:
    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

    all_nodes = manager.list_nodes()
    node = next((n for n in all_nodes if n.uuid == full_uuid), None)
    if node is None:
        return CmdResult(ok=False, error=f"Node not found: {uuid}", code="NOT_FOUND", data={})

    ok = manager.storage.verify_integrity(full_uuid, node.blob_sha256)
    if ok:
        return CmdResult(ok=True, data={"result": "OK"})
    return CmdResult(ok=False, error="CORRUPTED", code="CORRUPTED", data={})


def export_graph(vault: Vault, output_format: str = "dot", include_paths: bool = False) -> CmdResult:
    manager = NodeManager(vault.path)
    nodes = manager.list_nodes()
    exporter = GraphExporter(vault.path)

    if output_format == "dot":
        output = exporter.export_dot(nodes, include_paths=include_paths)
    else:
        output = exporter.export_json(nodes, include_paths=include_paths)

    return CmdResult(ok=True, data={"output": output, "format": output_format})


def list_backlinks(vault: Vault, uuid: str) -> CmdResult:
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

    index = BacklinkIndex(vault.path)
    links = index.get_backlinks(full_uuid)
    return CmdResult(ok=True, data={"uuid": full_uuid, "backlinks": links})


def query_nodes(vault: Vault, query_str: str) -> CmdResult:
    parser = QueryParser()
    try:
        ast = parser.parse(query_str)
    except Exception as e:
        return CmdResult(ok=False, error=str(e), code="PARSE_ERROR", data={})
    engine = QueryEngine(vault.path)
    results = engine.execute(ast)
    return CmdResult(ok=True, data={"results": results})


def vault_status(vault: Vault) -> CmdResult:
    tracker = ChangeTracker(vault.path)
    report = tracker.status()
    return CmdResult(ok=True, data=report)


def add_vault(path: str) -> CmdResult:
    try:
        v = Vault.open(path)
    except FileNotFoundError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

    registry = VaultRegistry()
    registry.add(v.vault_uuid, v.path)
    return CmdResult(ok=True, data={"uuid": v.vault_uuid, "path": v.path})


def list_vaults() -> CmdResult:
    registry = VaultRegistry()
    vaults = registry.list()
    return CmdResult(ok=True, data={"vaults": vaults})


def create_node(
    vault: Vault,
    type_name: str,
    title: str = "",
    fields: Optional[dict[str, object]] = None,
    tags: Optional[list[str]] = None,
    add_path: Optional[str] = None,
) -> CmdResult:
    manager = NodeManager(vault.path)
    try:
        meta = manager.create_node(
            type_name=type_name,
            title=title,
            fields=fields or {},
            tags=tags,
        )
        path_added = None
        if add_path:
            resolver = PathResolver(vault.path)
            try:
                path_uuid = resolver.resolve(add_path)
            except ValueError:
                return CmdResult(ok=True, data={
                    "meta": meta,
                    "warning": f"Path does not exist: {add_path}",
                })
            meta.paths.append(path_uuid)
            storage_dir = compute_storage_path(vault.path, meta.uuid)
            meta_path = NodeMetadata.metadata_path(storage_dir)
            meta.save(meta_path)
            path_added = add_path

        return CmdResult(ok=True, data={
            "meta": meta,
            "path_added": path_added,
        })
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="VALIDATION_ERROR", data={})


def edit_node(
    vault: Vault,
    uuid: str,
    add_path: Optional[str] = None,
    remove_path: Optional[str] = None,
) -> CmdResult:
    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

    if add_path is not None:
        try:
            if manager.add_path_to_node(full_uuid, add_path):
                return CmdResult(ok=True, data={"action": "add_path", "path": add_path})
            return CmdResult(ok=True, data={"action": "add_path_skipped", "path": add_path})
        except ValueError as e:
            return CmdResult(ok=False, error=str(e), code="VALIDATION_ERROR", data={})

    if remove_path is not None:
        try:
            if manager.remove_path_from_node(full_uuid, remove_path):
                return CmdResult(ok=True, data={"action": "remove_path", "path": remove_path})
            return CmdResult(ok=True, data={"action": "remove_path_skipped", "path": remove_path})
        except ValueError as e:
            return CmdResult(ok=False, error=str(e), code="VALIDATION_ERROR", data={})

    return CmdResult(ok=False, error="No operation specified", code="NO_OP", data={})


def edit_node_body(vault: Vault, uuid: str) -> CmdResult:
    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

    try:
        body_info = manager.get_body_info(full_uuid)
    except (FileNotFoundError, OSError):
        return CmdResult(ok=False, error=f"Node not found: {uuid}", code="NOT_FOUND", data={})

    if body_info is not None:
        body_path, original_mtime = body_info
        return CmdResult(ok=True, data={
            "type": "body",
            "uuid": full_uuid,
            "body_path": body_path,
            "original_mtime": original_mtime,
        })

    return CmdResult(ok=False, error="Node has no body", code="NO_BODY", data={"uuid": full_uuid})


def edit_node_fields(vault: Vault, uuid: str) -> CmdResult:
    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

    try:
        schema, current_values = manager.get_field_info(full_uuid)
    except (FileNotFoundError, OSError):
        return CmdResult(ok=False, error=f"Node not found: {uuid}", code="NOT_FOUND", data={})
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="VALIDATION_ERROR", data={})

    return CmdResult(ok=True, data={
        "type": "fields",
        "uuid": full_uuid,
        "schema": schema,
        "current_values": current_values,
    })


def commit_body_edit(
    vault: Vault,
    uuid: str,
    new_mtime: float,
    new_size: int,
    new_sha256: str,
) -> CmdResult:
    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})
    manager.commit_body_edit(full_uuid, new_mtime, new_size, new_sha256)
    return CmdResult(ok=True, data={"uuid": full_uuid})


def update_node_fields(vault: Vault, uuid: str, changes: dict[str, str]) -> CmdResult:
    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})
    if manager.update_node_fields(full_uuid, changes):
        return CmdResult(ok=True, data={"uuid": full_uuid})
    return CmdResult(ok=False, error="No changes detected", code="NO_CHANGES", data={})


def link_nodes(vault: Vault, source_uuid: str, target_uuid: str) -> CmdResult:
    try:
        full_source = resolve_uuid(vault.path, source_uuid)
        full_target = resolve_uuid(vault.path, target_uuid)
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

    manager = NodeManager(vault.path)
    all_nodes = manager.list_nodes()
    source = next((n for n in all_nodes if n.uuid == full_source), None)
    target = next((n for n in all_nodes if n.uuid == full_target), None)

    if source is None:
        return CmdResult(ok=False, error=f"Source node not found: {source_uuid}", code="NOT_FOUND", data={})

    warning = None
    if target is None:
        warning = "Target node does not exist in any registered vault"

    storage_dir = os.path.join(vault.path, ".storage")
    meta_path = None
    for root, _dirs, files in os.walk(storage_dir):
        for fname in files:
            if fname == "metadata.toml":
                try:
                    meta = NodeMetadata.from_toml(os.path.join(root, fname))
                    if meta.uuid == full_source:
                        meta_path = os.path.join(root, fname)
                        break
                except Exception:
                    continue
        if meta_path:
            break

    if meta_path is None:
        return CmdResult(ok=False, error=f"Could not find metadata for {source_uuid}", code="NOT_FOUND", data={})

    source_meta = NodeMetadata.from_toml(meta_path)
    link_entry = {
        "target": target_uuid,
        "type": target.type if target else "",
        "title": target.title if target else "",
    }

    for existing in source_meta.links:
        if existing.get("target") == target_uuid:
            return CmdResult(ok=False, error="Link already exists.", code="ALREADY_EXISTS", data={})

    source_meta.links.append(link_entry)
    source_meta.sync_dirty = True
    source_meta.save(meta_path)

    data: dict[str, object] = {"source": full_source, "target": full_target}
    if warning:
        data["warning"] = warning
    return CmdResult(ok=True, data=data)


def import_file(
    vault: Vault,
    source_path: str,
    type_name: Optional[str] = None,
    force: bool = False,
) -> CmdResult:
    source_path = os.path.abspath(source_path)
    if not os.path.exists(source_path):
        return CmdResult(ok=False, error=f"File not found: {source_path}", code="NOT_FOUND", data={})

    file_hash = sha256_file(source_path)
    manager = NodeManager(vault.path)

    if not force:
        existing = find_by_hash(manager, file_hash)
        if existing.ok:
            return CmdResult(ok=False, error=f"File already exists as node {existing.data['uuid']}",
                             code="ALREADY_EXISTS", data=existing.data)

    actual_type = type_name or "file"
    try:
        meta = manager.create_node(
            type_name=actual_type,
            title=os.path.basename(source_path),
            blob_path=source_path,
        )
        return CmdResult(ok=True, data={"uuid": meta.uuid, "title": meta.title})
    except ValueError as e:
        return CmdResult(ok=False, error=str(e), code="VALIDATION_ERROR", data={})


def manage_tags(
    vault: Vault,
    action: str,
    uuid: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> CmdResult:
    manager = NodeManager(vault.path)

    if action == "add":
        if not uuid or not tags:
            return CmdResult(ok=False, error="Usage: tag add <uuid> <tag> [<tag>...]", code="USAGE", data={})
        try:
            full_uuid = resolve_uuid(vault.path, uuid)
        except ValueError as e:
            return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

        results = []
        for tag_str in tags:
            try:
                if manager.add_tag(full_uuid, tag_str):
                    results.append({"tag": tag_str, "status": "added"})
                else:
                    results.append({"tag": tag_str, "status": "already_present"})
            except ValueError as e:
                results.append({"tag": tag_str, "status": "error", "error": str(e)})
        return CmdResult(ok=True, data={"action": "add", "uuid": full_uuid, "results": results})

    elif action == "rm":
        if not uuid or not tags:
            return CmdResult(ok=False, error="Usage: tag rm <uuid> <tag> [<tag>...]", code="USAGE", data={})
        try:
            full_uuid = resolve_uuid(vault.path, uuid)
        except ValueError as e:
            return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

        results = []
        for tag_str in tags:
            if manager.remove_tag(full_uuid, tag_str):
                results.append({"tag": tag_str, "status": "removed"})
            else:
                results.append({"tag": tag_str, "status": "not_present"})
        return CmdResult(ok=True, data={"action": "rm", "uuid": full_uuid, "results": results})

    elif action == "list":
        tags_dict = manager.list_tags()
        return CmdResult(ok=True, data={"action": "list", "tags": tags_dict})

    elif action == "rename":
        if not tags or len(tags) < 2:
            return CmdResult(ok=False, error="Usage: tag rename <old-tag> <new-tag>", code="USAGE", data={})
        old_tag, new_tag = tags[0], tags[1]
        try:
            affected = manager.rename_tag(old_tag, new_tag)
            return CmdResult(ok=True, data={"action": "rename", "old_tag": old_tag, "new_tag": new_tag, "affected": affected})
        except ValueError as e:
            return CmdResult(ok=False, error=str(e), code="VALIDATION_ERROR", data={})

    return CmdResult(ok=False, error=f"Unknown tag action: {action}", code="UNKNOWN_ACTION", data={})


def manage_paths(
    vault: Vault,
    action: str,
    path_str: str = "",
) -> CmdResult:
    resolver = PathResolver(vault.path)

    if action == "create":
        if not path_str:
            return CmdResult(ok=False, error="Usage: path create <path>", code="USAGE", data={})
        try:
            leaf_uuid = resolver.resolve_or_create(path_str)
            return CmdResult(ok=True, data={"action": "create", "path": path_str, "leaf_uuid": leaf_uuid})
        except ValueError as e:
            return CmdResult(ok=False, error=str(e), code="VALIDATION_ERROR", data={})

    elif action == "rm":
        if not path_str:
            return CmdResult(ok=False, error="Usage: path rm <path>", code="USAGE", data={})
        try:
            leaf_uuid = resolver.resolve(path_str)
        except ValueError as e:
            return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

        descendants = resolver.collect_descendants(leaf_uuid)
        all_uuids = [leaf_uuid] + descendants

        manager = NodeManager(vault.path)
        nodes = manager.list_nodes()
        for n in nodes:
            matching = [p for p in all_uuids if p in n.paths]
            if matching:
                n.paths = [p for p in n.paths if p not in all_uuids]
                storage_dir = compute_storage_path(vault.path, n.uuid)
                meta_path = NodeMetadata.metadata_path(storage_dir)
                n.save(meta_path)

        for uid in all_uuids:
            sdir = compute_storage_path(vault.path, uid)
            if os.path.exists(sdir):
                shutil.rmtree(sdir)

        return CmdResult(ok=True, data={
            "action": "rm", "path": path_str,
            "removed_uuids": all_uuids,
        })

    elif action == "tree":
        try:
            root_uuid = resolver.resolve(path_str if path_str else "/")
        except ValueError as e:
            return CmdResult(ok=False, error=str(e), code="NOT_FOUND", data={})

        nodes = resolver._all_nodes()
        nodes_by_uuid = {n.uuid: n for n in nodes}

        def _count_referencing(uuid: str) -> int:
            return sum(1 for n in nodes if uuid in n.paths)

        def _build_tree(uuid: str) -> dict[str, object]:
            node = nodes_by_uuid.get(uuid)
            if node is None:
                return {}
            name = node.fields.get("name", node.title or uuid[:8])
            ref_count = _count_referencing(uuid)
            children = sorted(
                resolver._find_children(uuid, nodes),
                key=lambda c: c.fields.get("name", ""),
            )
            return {
                "uuid": uuid,
                "name": name,
                "ref_count": ref_count,
                "children": [_build_tree(c.uuid) for c in children],
            }

        root_node = nodes_by_uuid.get(root_uuid)
        if root_node is None:
            return CmdResult(ok=True, data={"action": "tree", "tree": None})

        root_name = root_node.fields.get("name", "/")
        root_ref_count = _count_referencing(root_uuid)
        tree = {
            "uuid": root_uuid,
            "name": root_name,
            "ref_count": root_ref_count,
            "children": [],
        }
        children = sorted(
            resolver._find_children(root_uuid, nodes),
            key=lambda c: c.fields.get("name", ""),
        )
        tree["children"] = [_build_tree(c.uuid) for c in children]

        return CmdResult(ok=True, data={"action": "tree", "tree": tree})

    return CmdResult(ok=False, error=f"Unknown path action: {action}", code="UNKNOWN_ACTION", data={})
