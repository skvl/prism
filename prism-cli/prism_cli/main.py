"""Click-based CLI entry point for Prism.

Defines all CLI commands, groups (tag, path, vault), and the main
entry point. Delegates business logic to `commands.py`.
"""
import json
import os
import subprocess
import sys
from typing import Optional

import click

from prism import VERSION
from prism.node.manager import NodeManager, resolve_uuid
from prism.node.storage import sha256_file
from prism.path.resolver import PathResolver
from prism.vault.vault import Vault
from prism.vault.context import detect_vault

from . import commands
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
    result = commands.init_vault(path)
    if result.ok:
        click.echo(f"Vault initialized at {result.data['path']}")
        click.echo(f"Vault UUID: {result.data['vault_uuid']}")
    else:
        click.echo(f"Error: {result.error}", err=True)
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
    result = commands.manage_paths(vault, "create", path_str)
    if result.ok:
        click.echo(f"Path created: {path_str}")
        click.echo(f"Leaf UUID: {result.data['leaf_uuid']}")
    else:
        click.echo(f"Error: {result.error}", err=True)
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
    all_uuids = [leaf_uuid] + descendants

    manager = NodeManager(vault.path)
    nodes = manager.list_nodes()
    referencing: set[str] = set()
    for n in nodes:
        if any(p in n.paths for p in all_uuids):
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

    result = commands.manage_paths(vault, "rm", path_str)
    if result.ok:
        click.echo(f"Removed path: {path_str}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)


@path_cmd.command()
@click.argument("path_str", default="")
@click.pass_context
def tree(ctx: click.Context, path_str: str) -> None:
    """Display the path hierarchy as a tree."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    result = commands.manage_paths(vault, "tree", path_str)
    if not result.ok:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

    tree_data = result.data.get("tree")
    if tree_data is None:
        click.echo("No path found.")
        return

    def _render(node: dict, prefix: str = "", is_last: bool = True) -> None:
        name = node.get("name", node.get("uuid", "")[:8])
        ref_count = node.get("ref_count", 0)
        suffix = f" ({ref_count} nodes)" if ref_count > 0 else ""
        connector = "└── " if is_last else "├── "
        click.echo(f"{prefix}{connector}{name}{suffix}")
        children = node.get("children", [])
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(children):
            _render(child, child_prefix, i == len(children) - 1)

    click.echo(f"{tree_data['name']}{' (' + str(tree_data['ref_count']) + ' nodes)' if tree_data['ref_count'] > 0 else ''}")
    for i, child in enumerate(tree_data.get("children", [])):
        _render(child, "", i == len(tree_data["children"]) - 1)


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
    result = commands.manage_tags(vault, "add", uuid, list(tags))
    if not result.ok:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)
    for r in result.data.get("results", []):
        if r["status"] == "added":
            click.echo(f"Added tag: {r['tag']}")
        elif r["status"] == "already_present":
            click.echo(f"Tag already present: {r['tag']}")
        elif r["status"] == "error":
            click.echo(f"Error: {r['error']}", err=True)
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
    result = commands.manage_tags(vault, "rm", uuid, list(tags))
    if not result.ok:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)
    for r in result.data.get("results", []):
        if r["status"] == "removed":
            click.echo(f"Removed tag: {r['tag']}")
        elif r["status"] == "not_present":
            click.echo(f"Tag not present: {r['tag']}")


@tag.command("list")
@click.option("--count", is_flag=True, help="Show tag counts")
@click.pass_context
def list_tags(ctx: click.Context, count: bool) -> None:
    """List all unique tags across the vault."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)
    result = commands.manage_tags(vault, "list")
    tags_dict = result.data.get("tags", {})
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
    result = commands.manage_tags(vault, "rename", tags=[old_tag, new_tag])
    if result.ok:
        affected = result.data["affected"]
        click.echo(f"Renamed tag '{old_tag}' to '{new_tag}' across {affected} node(s)")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)


@cli.group()
@click.pass_context
def vault(ctx: click.Context) -> None:
    """Manage vaults."""


@vault.command()
@click.argument("path")
@click.pass_context
def add(ctx: click.Context, path: str) -> None:
    """Register an existing vault."""
    result = commands.add_vault(path)
    if result.ok:
        click.echo(f"Vault {result.data['uuid'][:8]} registered at {result.data['path']}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)


@vault.command()
@click.pass_context
def list_vaults(ctx: click.Context) -> None:
    """List registered vaults."""
    result = commands.list_vaults()
    vaults = result.data.get("vaults", [])
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

    result = commands.import_file(vault, source_path, type_name)
    if result.code == "ALREADY_EXISTS":
        click.echo(f"File already exists as node {result.data['uuid']}")
        click.echo("Create a second reference? [y/N]: ", nl=False)
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm != "y":
            return
        result = commands.import_file(vault, source_path, type_name, force=True)

    if result.ok:
        click.echo(f"Imported as node {result.data['uuid']}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)


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

    result = commands.create_node(
        vault, type_name, title,
        fields=explicit_fields,
        tags=list(tags) if tags else None,
        add_path=add_path,
    )
    if result.ok:
        meta = result.data["meta"]
        if result.data.get("path_added"):
            click.echo(f"Added path: {result.data['path_added']}")
        elif "warning" in result.data:
            click.echo(f"Path does not exist: {add_path}")
            # Still return success - the node was created
        click.echo(f"Created {type_name} node: {meta.uuid}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)


def _do_edit_path_ops(vault: Vault, uuid: str, add_path: Optional[str], remove_path: Optional[str]) -> bool:
    """Handle add/remove path operations. Returns True if a path op was handled."""
    if add_path is not None or remove_path is not None:
        result = commands.edit_node(vault, uuid, add_path=add_path, remove_path=remove_path)
        if result.ok:
            action = result.data.get("action", "")
            path = result.data.get("path", "")
            if action == "add_path":
                click.echo(f"Added path: {path}")
            elif action == "add_path_skipped":
                click.echo("Node already associated with this path.")
            elif action == "remove_path":
                click.echo(f"Removed path: {path}")
            elif action == "remove_path_skipped":
                click.echo("Node not associated with this path.")
        else:
            click.echo(f"Error: {result.error}", err=True)
            sys.exit(1)
        return True
    return False


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

    try:
        full_uuid = resolve_uuid(vault.path, uuid)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if _do_edit_path_ops(vault, full_uuid, add_path, remove_path):
        return

    body_result = commands.edit_node_body(vault, full_uuid)
    if body_result.ok and body_result.data.get("type") == "body":
        body_path: str = body_result.data["body_path"]
        original_mtime: float = body_result.data["original_mtime"]
        editor = os.environ.get("EDITOR", "vi")
        subprocess.call([editor, body_path])
        new_mtime = os.stat(body_path).st_mtime
        if new_mtime == original_mtime:
            click.echo("No changes detected.")
            return
        new_size = os.stat(body_path).st_size
        new_sha256 = sha256_file(body_path)
        result = commands.commit_body_edit(vault, full_uuid, new_mtime, new_size, new_sha256)
        if result.ok:
            click.echo("Body updated.")
        return

    fields_result = commands.edit_node_fields(vault, full_uuid)
    if fields_result.ok and fields_result.data.get("type") == "fields":
        schema = fields_result.data["schema"]
        current_values: dict[str, str] = fields_result.data["current_values"]
        changes: dict[str, str] = {}
        for field_def in schema.fields:
            current = current_values.get(field_def.name, "")
            try:
                new_val = input(f"Enter new {field_def.name} or press ENTER to keep [{current}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if new_val:
                changes[field_def.name] = new_val
        update_result = commands.update_node_fields(vault, full_uuid, changes)
        if update_result.ok:
            click.echo("Fields updated.")
        else:
            click.echo("No changes detected.")
        return

    click.echo(f"Node not found: {uuid}", err=True)
    sys.exit(1)


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

    result = commands.delete_node(vault, uuid, force=yes)
    if result.ok:
        click.echo(f"Deleted node {result.data['uuid']}")
    elif result.code == "CONFIRM_REQUIRED":
        click.echo(f"Warning: {result.error}", err=True)
        click.echo("Delete anyway? [y/N]: ", nl=False)
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm == "y":
            result2 = commands.delete_node(vault, uuid, force=True)
            if result2.ok:
                click.echo(f"Deleted node {result2.data['uuid']}")
            else:
                click.echo(f"Node not found: {uuid}", err=True)
                sys.exit(1)
        else:
            click.echo("Aborted.")
    else:
        click.echo(result.error, err=True)
        sys.exit(1)


@cli.command()
@click.argument("uuid")
@click.pass_context
def show(ctx: click.Context, uuid: str) -> None:
    """Display a node's details."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    result = commands.show_node(vault, uuid)
    if result.ok:
        click.echo(result.data["output"])
    else:
        click.echo(result.error, err=True)
        sys.exit(1)


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

    result = commands.link_nodes(vault, source_uuid, target_uuid)
    if result.ok:
        data = result.data
        if "warning" in data:
            click.echo(f"Warning: {data['warning']}", err=True)
        click.echo(f"Linked {data['source'][:8]} -> {data['target'][:8]}")
    else:
        if result.code == "ALREADY_EXISTS":
            click.echo("Link already exists.")
            return
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("uuid")
@click.pass_context
def backlinks(ctx: click.Context, uuid: str) -> None:
    """Show nodes that link to the given UUID."""
    vault: Optional[Vault] = ctx.obj.get("vault")
    if vault is None:
        click.echo("No vault found. Run `prism init` to create one.", err=True)
        sys.exit(1)

    result = commands.list_backlinks(vault, uuid)
    if not result.ok:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

    links = result.data.get("backlinks", [])
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

    result = commands.export_graph(vault, output_format, include_paths)
    click.echo(result.data["output"])


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

    result = commands.query_nodes(vault, query_str)
    if not result.ok:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

    results = result.data.get("results", [])
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

    result = commands.vault_status(vault)
    report = result.data

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
            from prism.tracking import ChangeTracker
            tracker = ChangeTracker(vault.path)
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

    result = commands.verify_node(vault, uuid)
    if result.ok:
        click.echo("OK")
    else:
        click.echo(f"Error: {result.error}", err=True)
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
    """Entry point for the CLI. Delegates to the Click group."""
    cli()

if __name__ == "__main__":
    main()
