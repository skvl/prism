import json
import os
import sys
from typing import Optional

import click

from prism import VERSION
from prism.vault.vault import Vault, generate_uuid
from prism.vault.registry import VaultRegistry
from prism.vault.context import detect_vault
from prism.node.manager import NodeManager, resolve_uuid, _list_all_nodes
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path, sha256_file
from prism.graph.links import BacklinkIndex, GraphExporter
from prism.path.resolver import PathResolver
from prism.query.parser import QueryParser
from prism.query.engine import QueryEngine
from prism.tracking import ChangeTracker

from .repl import Repl
from .tutor import Tutor


@click.group()
@click.option("--vault", "-v", default=None, help="Path to vault directory")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.version_option(VERSION, prog_name="prism")
@click.pass_context
def cli(ctx: click.Context, vault: Optional[str], verbose: bool, output_format: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["format"] = output_format

    current_vault = None
    if vault:
        try:
            current_vault = Vault.open(vault)
        except FileNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    else:
        current_vault = detect_vault(os.getcwd())

    ctx.obj["vault"] = current_vault


@cli.command()
@click.argument("path", default=".")
@click.pass_context
def init(ctx: click.Context, path: str) -> None:
    """Initialize a new vault at PATH."""
    try:
        vault = Vault.init(path)
        _write_builtin_types(vault)
        click.echo(f"Vault initialized at {vault.path}")
        click.echo(f"Vault UUID: {vault.vault_uuid}")
    except FileExistsError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
@click.pass_context
def path_cmd(ctx: click.Context) -> None:
    """Manage path hierarchy."""


@path_cmd.command()
@click.argument("path_str")
@click.pass_context
def create(ctx: click.Context, path_str: str) -> None:
    """Create a path segment hierarchy (mkdir -p)."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)
    resolver = PathResolver(vault.path)
    try:
        leaf_uuid = resolver.resolve_or_create(path_str)
        click.echo(f"Path created: {path_str}")
        click.echo(f"Leaf UUID: {leaf_uuid}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@path_cmd.command()
@click.argument("path_str")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def rm(ctx: click.Context, path_str: str, yes: bool) -> None:
    """Remove a path segment and its subtree."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)
    resolver = PathResolver(vault.path)
    try:
        leaf_uuid = resolver.resolve(path_str)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    descendants = resolver.collect_descendants(leaf_uuid)

    nodes = _list_all_nodes(vault.path)
    referencing: set[str] = set()
    for n in nodes:
        all_p = [leaf_uuid] + descendants
        if any(p in n.paths for p in all_p):
            referencing.add(n.uuid)

    if not yes:
        msg = f"Remove path '{path_str}'"
        if descendants:
            msg += f" ({len(descendants)} descendant segments)"
        if referencing:
            msg += f", removed from {len(referencing)} node(s)"
        msg += ". Continue? [y/N]: "
        click.echo(msg, nl=False)
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm != "y":
            click.echo("Aborted.")
            return

    all_uuids = [leaf_uuid] + descendants
    for n in nodes:
        if any(p in n.paths for p in all_uuids):
            n.paths = [p for p in n.paths if p not in all_uuids]
            meta_dir = os.path.dirname(NodeMetadata.metadata_path(
                compute_storage_path(vault.path, n.uuid)
            ))
            n.save(os.path.join(meta_dir, "metadata.toml"))

    for uid in all_uuids:
        storage_dir = compute_storage_path(vault.path, uid)
        if os.path.exists(storage_dir):
            import shutil
            shutil.rmtree(storage_dir)

    click.echo(f"Removed path: {path_str}")


@path_cmd.command()
@click.argument("path_str", default="")
@click.pass_context
def tree(ctx: click.Context, path_str: str) -> None:
    """Display the path hierarchy as a tree."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)
    resolver = PathResolver(vault.path)
    try:
        root_uuid = resolver.resolve(path_str if path_str else "/")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    nodes = resolver._all_nodes()
    nodes_by_uuid = {n.uuid: n for n in nodes}

    def _count_referencing(uuid: str) -> int:
        return sum(1 for n in nodes if uuid in n.paths)

    def _render(uuid: str, prefix: str = "", is_last: bool = True) -> None:
        node = nodes_by_uuid.get(uuid)
        if node is None:
            return
        name = node.fields.get("name", node.title or uuid[:8])
        ref_count = _count_referencing(uuid)
        suffix = f" ({ref_count} nodes)" if ref_count > 0 else ""
        connector = "└── " if is_last else "├── "
        click.echo(f"{prefix}{connector}{name}{suffix}")
        children = sorted(resolver._find_children(uuid, nodes), key=lambda c: c.fields.get("name", ""))
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(children):
            _render(child.uuid, child_prefix, i == len(children) - 1)

    root_node = nodes_by_uuid.get(root_uuid)
    if root_node is None:
        click.echo("No path found.")
        return

    name = root_node.fields.get("name", "/")
    ref_count = _count_referencing(root_uuid)
    suffix = f" ({ref_count} nodes)" if ref_count > 0 else ""
    click.echo(f"{name}{suffix}")
    children = sorted(resolver._find_children(root_uuid, nodes), key=lambda c: c.fields.get("name", ""))
    for i, child in enumerate(children):
        _render(child.uuid, "", i == len(children) - 1)


@cli.group()
@click.pass_context
def tag(ctx: click.Context) -> None:
    """Manage tags on nodes."""


@tag.command()
@click.argument("uuid")
@click.argument("tags", nargs=-1, required=True)
@click.pass_context
def add(ctx: click.Context, uuid: str, tags: tuple[str, ...]) -> None:
    """Add one or more tags to a node."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    for tag_str in tags:
        try:
            if manager.add_tag(full_uuid, tag_str):
                click.echo(f"Added tag: {tag_str}")
            else:
                click.echo(f"Tag already present: {tag_str}")
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@tag.command()
@click.argument("uuid")
@click.argument("tags", nargs=-1, required=True)
@click.pass_context
def rm(ctx: click.Context, uuid: str, tags: tuple[str, ...]) -> None:
    """Remove one or more tags from a node."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    for tag_str in tags:
        if manager.remove_tag(full_uuid, tag_str):
            click.echo(f"Removed tag: {tag_str}")
        else:
            click.echo(f"Tag not present: {tag_str}")


@tag.command("list")
@click.option("--count", is_flag=True, help="Show tag counts")
@click.pass_context
def list_tags(ctx: click.Context, count: bool) -> None:
    """List all unique tags across the vault."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    tags_dict = manager.list_tags()

    if not tags_dict:
        return

    for tag_name, tag_count in tags_dict.items():
        if count:
            click.echo(f"{tag_name} ({tag_count})")
        else:
            click.echo(tag_name)


@tag.command()
@click.argument("old_tag")
@click.argument("new_tag")
@click.pass_context
def rename(ctx: click.Context, old_tag: str, new_tag: str) -> None:
    """Rename a tag across all nodes."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    try:
        affected = manager.rename_tag(old_tag, new_tag)
        click.echo(f"Renamed tag '{old_tag}' to '{new_tag}' across {affected} node(s)")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _write_builtin_types(vault: Vault) -> None:
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
    for fname, content in types.items():
        path = os.path.join(types_dir, fname)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(content)


@cli.group()
@click.pass_context
def vault(ctx: click.Context) -> None:
    """Manage vaults."""


@vault.command()
@click.argument("path")
@click.pass_context
def add(ctx: click.Context, path: str) -> None:
    """Register an existing vault."""
    try:
        v = Vault.open(path)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    registry = VaultRegistry()
    registry.add(v.vault_uuid, v.path)
    click.echo(f"Vault {v.vault_uuid[:8]} registered at {v.path}")


@vault.command()
@click.pass_context
def list_vaults(ctx: click.Context) -> None:
    """List registered vaults."""
    registry = VaultRegistry()
    vaults = registry.list()
    if not vaults:
        click.echo("No vaults registered.")
        return

    for v in vaults:
        node_count = 0
        try:
            manager = NodeManager(v["path"])
            node_count = len(manager.list_nodes())
        except Exception:
            pass
        click.echo(f"  {v['uuid'][:8]}  {v['path']}  ({node_count} nodes)")


@cli.command()
@click.argument("source_path")
@click.option("--type", "type_name", default=None, help="Node type (default: auto-detect)")
@click.pass_context
def add_file(ctx: click.Context, source_path: str, type_name: Optional[str]) -> None:
    """Import a file into the vault."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    source_path = os.path.abspath(source_path)
    if not os.path.exists(source_path):
        click.echo(f"File not found: {source_path}", err=True)
        sys.exit(1)

    file_hash = sha256_file(source_path)
    manager = NodeManager(vault.path)

    existing = _find_by_hash(manager, file_hash)
    if existing:
        click.echo(f"File already exists as node {existing['uuid']}")
        click.echo("Create a second reference? [y/N]: ", nl=False)
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm != "y":
            return

    actual_type = type_name or "file"
    meta = manager.create_node(
        type_name=actual_type,
        title=os.path.basename(source_path),
        blob_path=source_path,
    )
    click.echo(f"Imported as node {meta.uuid}")


def _find_by_hash(manager: NodeManager, file_hash: str) -> Optional[dict]:
    for node in manager.list_nodes():
        if node.blob_sha256 == file_hash:
            return {"uuid": node.uuid, "title": node.title}
    return None


@cli.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.argument("type_name")
@click.argument("title", default="")
@click.option("--tag", "-t", "tags", multiple=True, help="Tags to add")
@click.option("--add-path", "-a", "add_path", default=None, help="Associate node with a path")
@click.pass_context
def new(ctx: click.Context, type_name: str, title: str, tags: tuple[str, ...], add_path: Optional[str]) -> None:
    """Create a new typed node."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)

    extra_fields: dict[str, str] = {}
    for arg in ctx.args:
        if arg.startswith("--") and "=" in arg:
            key, val = arg.lstrip("-").split("=", 1)
            extra_fields[key] = val

    click_ctx = click.get_current_context()
    for param, value in click_ctx.params.items():
        if param.startswith("field_") and value:
            extra_fields[param[6:]] = value

    explicit_fields: dict[str, object] = {}
    explicit_fields.update(extra_fields)

    try:
        meta = manager.create_node(
            type_name=type_name,
            title=title,
            fields=explicit_fields,
            tags=list(tags) if tags else None,
        )
        if add_path:
            resolver = PathResolver(vault.path)
            try:
                path_uuid = resolver.resolve(add_path)
            except ValueError:
                click.echo("Error: Path does not exist", err=True)
                sys.exit(1)
            storage_dir = os.path.join(vault.path, ".storage")
            meta_path = None
            for root, _dirs, files in os.walk(storage_dir):
                for fname in files:
                    if fname == "metadata.toml":
                        try:
                            m = NodeMetadata.from_toml(os.path.join(root, fname))
                            if m.uuid == meta.uuid:
                                meta_path = os.path.join(root, fname)
                                break
                        except Exception:
                            continue
                if meta_path:
                    break
            if meta_path:
                meta.paths.append(path_uuid)
                meta.save(meta_path)
            click.echo(f"Added path: {add_path}")
        click.echo(f"Created {type_name} node: {meta.uuid}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("uuid")
@click.option("--add-path", "-a", "add_path", default=None, help="Associate node with a path")
@click.option("--remove-path", "-r", "remove_path", default=None, help="Remove node from a path")
@click.pass_context
def edit(ctx: click.Context, uuid: str, add_path: Optional[str], remove_path: Optional[str]) -> None:
    """Edit a node's body or fields."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if add_path is not None:
        try:
            if manager.add_path_to_node(full_uuid, add_path):
                click.echo(f"Added path: {add_path}")
            else:
                click.echo("Node already associated with this path.")
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        return

    if remove_path is not None:
        try:
            if manager.remove_path_from_node(full_uuid, remove_path):
                click.echo(f"Removed path: {remove_path}")
            else:
                click.echo("Node not associated with this path.")
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        return

    try:
        body_info = manager.get_body_info(full_uuid)
    except (FileNotFoundError, OSError):
        click.echo(f"Node not found: {uuid}", err=True)
        sys.exit(1)
    if body_info is not None:
        body_path, original_mtime = body_info
        editor = os.environ.get("EDITOR", "vi")
        import subprocess
        subprocess.call([editor, body_path])
        new_mtime = os.stat(body_path).st_mtime
        if new_mtime == original_mtime:
            click.echo("No changes detected.")
            return
        new_size = os.stat(body_path).st_size
        new_sha256 = sha256_file(body_path)
        manager.commit_body_edit(full_uuid, new_mtime, new_size, new_sha256)
        click.echo("Body updated.")
    else:
        try:
            schema, current_values = manager.get_field_info(full_uuid)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        changes: dict[str, Any] = {}
        for field_def in schema.fields:
            current = current_values.get(field_def.name, "")
            try:
                new_val = input(f"Enter new {field_def.name} or press ENTER to keep [{current}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if new_val:
                changes[field_def.name] = new_val
        if manager.update_node_fields(full_uuid, changes):
            click.echo("Fields updated.")
        else:
            click.echo("No changes detected.")


@cli.command()
@click.argument("uuid")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def rm(ctx: click.Context, uuid: str, yes: bool) -> None:
    """Delete a node."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    try:
        if manager.delete_node(uuid, force=yes):
            click.echo(f"Deleted node {uuid}")
        else:
            click.echo(f"Node not found: {uuid}", err=True)
            sys.exit(1)
    except ValueError as e:
        click.echo(f"Warning: {e}", err=True)
        click.echo("Delete anyway? [y/N]: ", nl=False)
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm == "y":
            manager.delete_node(uuid, force=True)
            click.echo(f"Deleted node {uuid}")
        else:
            click.echo("Aborted.")


@cli.command()
@click.argument("uuid")
@click.pass_context
def show(ctx: click.Context, uuid: str) -> None:
    """Display a node's details."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    output = manager.show_node(uuid)
    if output is None:
        click.echo(f"Node not found: {uuid}", err=True)
        sys.exit(1)
    click.echo(output)


@cli.command()
@click.argument("source_uuid")
@click.argument("target_uuid")
@click.pass_context
def link(ctx: click.Context, source_uuid: str, target_uuid: str) -> None:
    """Create a directed link from source to target."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    try:
        full_source = resolve_uuid(vault.path, source_uuid)
        full_target = resolve_uuid(vault.path, target_uuid)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    all_nodes = manager.list_nodes()

    source = next((n for n in all_nodes if n.uuid == full_source), None)
    target = next((n for n in all_nodes if n.uuid == full_target), None)

    if source is None:
        click.echo(f"Source node not found: {source_uuid}", err=True)
        sys.exit(1)

    if target is None:
        click.echo("Warning: Target node does not exist in any registered vault", err=True)

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
        click.echo(f"Could not find metadata for {source_uuid}", err=True)
        sys.exit(1)

    source_meta = NodeMetadata.from_toml(meta_path)
    link_entry = {
        "target": target_uuid,
        "type": target.type if target else "",
        "title": target.title if target else "",
    }

    for existing in source_meta.links:
        if existing.get("target") == target_uuid:
            click.echo("Link already exists.")
            return

    source_meta.links.append(link_entry)
    source_meta.sync_dirty = True
    source_meta.save(meta_path)
    click.echo(f"Linked {full_source[:8]} -> {full_target[:8]}")


@cli.command()
@click.argument("uuid")
@click.pass_context
def backlinks(ctx: click.Context, uuid: str) -> None:
    """Show nodes that link to the given UUID."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    index = BacklinkIndex(vault.path)
    links = index.get_backlinks(full_uuid)
    if not links:
        click.echo("No backlinks found.")
        return

    for link in links:
        click.echo(f"  {link['uuid'][:8]}  {link.get('title', '?')}  ({link.get('type', '?')})")


@cli.command()
@click.option("--format", "output_format", type=click.Choice(["dot", "json"]), default="dot", help="Graph format")
@click.option("--include-paths", "-p", is_flag=True, default=False, help="Include path nodes in export")
@click.pass_context
def graph(ctx: click.Context, output_format: str, include_paths: bool) -> None:
    """Export the node graph."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    nodes = manager.list_nodes()
    exporter = GraphExporter(vault.path)

    if output_format == "dot":
        click.echo(exporter.export_dot(nodes, include_paths=include_paths))
    else:
        click.echo(exporter.export_json(nodes, include_paths=include_paths))


@cli.command()
@click.argument("query_str")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.pass_context
def query(ctx: click.Context, query_str: str, output_format: str) -> None:
    """Search nodes by tags, type, and text."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    parser = QueryParser()
    ast = parser.parse(query_str)
    engine = QueryEngine(vault.path)
    results = engine.execute(ast)

    if not results:
        click.echo("No results found")
        return

    if output_format == "json":
        data = [
            {
                "uuid": n.uuid,
                "type": n.type,
                "title": n.title,
                "tags": n.tags,
                "updated_at": n.updated_at,
            }
            for n in results
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"{'UUID':<12} {'Type':<12} {'Title':<30} {'Tags':<20} {'Updated':<25}")
        click.echo("-" * 99)
        for node in results:
            tags = ", ".join(node.tags) if node.tags else ""
            click.echo(
                f"{node.uuid[:12]:<12} "
                f"{node.type:<12} "
                f"{node.title[:30]:<30} "
                f"{tags[:20]:<20} "
                f"{node.updated_at[:25]:<25}"
            )


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show vault status: changed, new, orphaned nodes."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    tracker = ChangeTracker(vault.path)
    report = tracker.status()

    changed = report.get("changed", [])
    new_files = report.get("new_files", [])
    orphaned = report.get("orphaned", [])

    if changed:
        click.echo("Changed nodes:")
        for node in changed:
            click.echo(f"  {node['uuid'][:8]} {node.get('title', '?')}")

    if new_files:
        click.echo("New files detected:")
        for f in new_files:
            click.echo(f"  {f['path']}")

    if orphaned:
        click.echo("Missing nodes (index references deleted storage):")
        for o in orphaned:
            click.echo(f"  {o['uuid']}")

    if not changed and not new_files and not orphaned:
        click.echo("Vault is clean.")

    for node in changed:
        click.echo(f"Re-extract links from changed note {node['uuid']}? [y/N]: ", nl=False)
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm == "y":
            tracker.re_extract_links(node["uuid"])


@cli.command()
@click.argument("uuid")
@click.pass_context
def verify(ctx: click.Context, uuid: str) -> None:
    """Verify blob integrity by comparing SHA-256 hash."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    manager = NodeManager(vault.path)
    all_nodes = manager.list_nodes()
    node = next((n for n in all_nodes if n.uuid == full_uuid), None)

    if node is None:
        click.echo(f"Node not found: {uuid}", err=True)
        sys.exit(1)

    ok = manager.storage.verify_integrity(full_uuid, node.blob_sha256)
    if ok:
        click.echo("OK")
    else:
        click.echo("CORRUPTED")
        sys.exit(1)


@cli.command()
@click.option("--lesson", "-L", default=1, type=int, help="Lesson number to start from")
def tutor(lesson: int) -> None:
    """Launch interactive tutorial in a sandbox vault."""
    t = Tutor(lesson_number=lesson)
    t.run()


@cli.command()
@click.option("--vault", "-v", default=None, help="Path to vault directory")
@click.pass_context
def repl(ctx: click.Context, vault: Optional[str]) -> None:
    """Launch an interactive REPL session."""
    current_vault = ctx.obj.get("vault")
    if vault:
        try:
            current_vault = Vault.open(vault)
        except FileNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    r = Repl(vault=current_vault)
    r.run()


def main() -> None:
    cli()

if __name__ == "__main__":
    main()
