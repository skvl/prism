import os
import readline
from typing import Optional

from prism.node.manager import NodeManager, resolve_uuid
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path, sha256_file
from prism.graph.links import LinkExtractor, BacklinkIndex, GraphExporter
from prism.path.resolver import PathResolver
from prism.query.parser import QueryParser
from prism.query.engine import QueryEngine
from prism.tracking import ChangeTracker
from prism.types.loader import TypeLoader
from prism.vault.vault import Vault

HISTORY_FILE = os.path.expanduser("~/.prism_repl_history")
MAX_HISTORY = 1000

ALIASES = {
    "n": "new",
    "s": "show",
    "q": "query",
    "l": "link",
    "bl": "backlinks",
    "g": "graph",
    "st": "status",
    "e": "edit",
    "af": "add-file",
    "v": "verify",
}

DEGRADED_COMMANDS = {"init", "open", "help", "exit", "quit", "history"}

UNSUPPORTED_IN_REPL = {"tutor"}


def _write_builtin_types(vault: Vault) -> None:
    from prism.types.builtins import BOOKMARK_TOML, CONTACT_TOML, FILE_TOML, NOTE_TOML, PATH_TOML

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


class Repl:
    def __init__(self, vault: Optional[Vault] = None) -> None:
        self.vault = vault
        self.last_uuid: Optional[str] = None
        self._completion_matches: list[str] = []
        self._setup_history()
        self._setup_completion()

    def _setup_history(self) -> None:
        readline.set_history_length(MAX_HISTORY)
        if os.path.exists(HISTORY_FILE):
            try:
                readline.read_history_file(HISTORY_FILE)
            except FileNotFoundError:
                pass

    def _setup_completion(self) -> None:
        readline.set_completer(self._complete)
        readline.parse_and_bind("tab: complete")

    def _save_history(self) -> None:
        try:
            readline.write_history_file(HISTORY_FILE)
        except IOError:
            pass

    def _resolve_underscore(self, args: list[str]) -> Optional[list[str]]:
        resolved: list[str] = []
        for arg in args:
            if arg == "_":
                if self.last_uuid is None:
                    print("Error: No previous node")
                    return None
                resolved.append(self.last_uuid)
            else:
                resolved.append(arg)
        return resolved

    def run(self) -> None:
        print("Prism REPL. Type 'help' for commands, 'exit' to quit.")
        if self.vault:
            print(f"Connected to vault: {self.vault.path}")
        else:
            print("No vault connected. Run 'init' or 'open' to connect.")

        while True:
            try:
                line = input("prism> ").strip()
            except EOFError:
                print()
                self._save_history()
                break
            except KeyboardInterrupt:
                print()
                continue

            if not line:
                continue

            if self._handle_line(line):
                break

        self._save_history()

    def _handle_line(self, line: str) -> bool:
        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("exit", "quit"):
            return True

        if cmd in UNSUPPORTED_IN_REPL:
            print(f"The {cmd} command cannot run inside the REPL. Run `prism {cmd}` from your shell.")
            return False

        if cmd in ALIASES:
            cmd = ALIASES[cmd]

        if self.vault is None and cmd not in DEGRADED_COMMANDS:
            print("No vault connected. Use 'init' or 'open' first.")
            return False

        if cmd not in ("init", "open"):
            resolved = self._resolve_underscore(args)
            if resolved is None:
                return False
            args = resolved

        dispatch = {
            "init": self._cmd_init,
            "open": self._cmd_open,
            "new": self._cmd_new,
            "show": self._cmd_show,
            "edit": self._cmd_edit,
            "rm": self._cmd_rm,
            "query": self._cmd_query,
            "link": self._cmd_link,
            "backlinks": self._cmd_backlinks,
            "graph": self._cmd_graph,
            "status": self._cmd_status,
            "add-file": self._cmd_add_file,
            "verify": self._cmd_verify,
            "help": self._cmd_help,
            "history": self._cmd_history,
            "path": self._cmd_path,
        }

        handler = dispatch.get(cmd)
        if handler:
            handler(args)
        else:
            print(f"Unknown command: {cmd}. Type 'help' for available commands.")

        return False

    def _cmd_init(self, args: list[str]) -> None:
        path = args[0] if args else "."
        try:
            vault = Vault.init(path)
            _write_builtin_types(vault)
            self.vault = vault
            print(f"Vault initialized at {vault.path}")
            print(f"Vault UUID: {vault.vault_uuid}")
        except FileExistsError as e:
            print(f"Error: {e}")

    def _cmd_open(self, args: list[str]) -> None:
        if not args:
            print("Usage: open <path>")
            return
        try:
            self.vault = Vault.open(args[0])
            print(f"Connected to vault: {self.vault.path}")
        except FileNotFoundError as e:
            print(f"Error: {e}")

    def _cmd_new(self, args: list[str]) -> None:
        if not args:
            print("Usage: new <type> [title] [--tag <tag> ...] [--add-path <path>] [--field=value ...]")
            return

        type_name = args[0]
        title = ""
        tags: list[str] = []
        add_path: Optional[str] = None
        extra: list[str] = []
        i = 1
        while i < len(args):
            if args[i] == "--tag" and i + 1 < len(args):
                tags.append(args[i + 1])
                i += 2
            elif args[i] in ("--add-path", "-a") and i + 1 < len(args):
                add_path = args[i + 1]
                i += 2
            elif args[i].startswith("--") and "=" in args[i]:
                extra.append(args[i])
                i += 1
            else:
                title = args[i]
                i += 1

        extra_fields: dict[str, str] = {}
        for arg in extra:
            key, val = arg.lstrip("-").split("=", 1)
            extra_fields[key] = val

        assert self.vault is not None
        manager = NodeManager(self.vault.path)
        try:
            meta = manager.create_node(
                type_name=type_name,
                title=title,
                fields=extra_fields,
                tags=tags if tags else None,
            )
            self.last_uuid = meta.uuid
            print(f"Created {type_name} node: {meta.uuid}")
            if add_path:
                resolver = PathResolver(self.vault.path)
                try:
                    path_uuid = resolver.resolve(add_path)
                except ValueError:
                    print(f"Path does not exist: {add_path}")
                else:
                    meta.paths.append(path_uuid)
                    storage_dir = compute_storage_path(self.vault.path, meta.uuid)
                    meta_path = NodeMetadata.metadata_path(storage_dir)
                    meta.save(meta_path)
                    print(f"Added path: {add_path}")
        except ValueError as e:
            print(f"Error: {e}")

    def _cmd_show(self, args: list[str]) -> None:
        if not args:
            print("Usage: show <uuid>")
            return
        assert self.vault is not None
        manager = NodeManager(self.vault.path)
        output = manager.show_node(args[0])
        if output is None:
            print(f"Node not found: {args[0]}")
        else:
            print(output)

    def _cmd_edit(self, args: list[str]) -> None:
        if not args:
            print("Usage: edit <uuid> [--add-path <path>] [--remove-path <path>]")
            return
        assert self.vault is not None

        uuid_arg = args[0]
        add_path: Optional[str] = None
        remove_path: Optional[str] = None
        i = 1
        while i < len(args):
            if args[i] in ("--add-path", "-a") and i + 1 < len(args):
                add_path = args[i + 1]
                i += 2
            elif args[i] in ("--remove-path", "-r") and i + 1 < len(args):
                remove_path = args[i + 1]
                i += 2
            else:
                i += 1

        manager = NodeManager(self.vault.path)
        try:
            full_uuid = resolve_uuid(self.vault.path, uuid_arg)
        except ValueError as e:
            print(f"Error: {e}")
            return

        storage_dir = os.path.join(self.vault.path, ".storage")
        meta_path = None
        for root, _dirs, files in os.walk(storage_dir):
            for fname in files:
                if fname == "metadata.toml":
                    try:
                        meta = NodeMetadata.from_toml(os.path.join(root, fname))
                        if meta.uuid == full_uuid:
                            meta_path = os.path.join(root, fname)
                            break
                    except Exception:
                        continue
            if meta_path:
                break

        if meta_path is None:
            print(f"Node not found: {uuid_arg}")
            return

        meta = NodeMetadata.from_toml(meta_path)

        if add_path is not None:
            try:
                path_uuid = PathResolver(self.vault.path).resolve(add_path)
            except ValueError:
                print(f"Path does not exist: {add_path}")
                return
            if path_uuid not in meta.paths:
                meta.paths.append(path_uuid)
                meta.sync_dirty = True
                meta.save(meta_path)
                print(f"Added path: {add_path}")
            else:
                print("Node already associated with this path.")
            return

        if remove_path is not None:
            try:
                path_uuid = PathResolver(self.vault.path).resolve(remove_path)
            except ValueError:
                print(f"Path does not exist: {remove_path}")
                return
            if path_uuid in meta.paths:
                meta.paths = [p for p in meta.paths if p != path_uuid]
                meta.sync_dirty = True
                meta.save(meta_path)
                print(f"Removed path: {remove_path}")
            else:
                print("Node not associated with this path.")
            return

        if meta.blob_extension == "md":
            if manager.edit_node_body(meta.uuid):
                body_root = os.path.dirname(meta_path)
                body_path = os.path.join(body_root, f"data.{meta.blob_extension}")
                if os.path.exists(body_path):
                    new_links = LinkExtractor.extract_from_file(body_path)
                    meta.links = new_links
                    meta.save(meta_path)
                print("Body updated.")
                self.last_uuid = meta.uuid
            else:
                print("No changes detected.")
        else:
            if manager.edit_node_fields(meta.uuid):
                print("Fields updated.")
                self.last_uuid = meta.uuid
            else:
                print("No changes detected.")

    def _cmd_path(self, args: list[str]) -> None:
        if not args:
            print("Usage: path create <path> | path rm <path> | path tree [<path>]")
            return
        assert self.vault is not None
        resolver = PathResolver(self.vault.path)
        sub = args[0].lower()

        if sub == "create":
            if len(args) < 2:
                print("Usage: path create <path>")
                return
            try:
                leaf_uuid = resolver.resolve_or_create(args[1])
                print(f"Path created: {args[1]}")
                print(f"Leaf UUID: {leaf_uuid}")
            except ValueError as e:
                print(f"Error: {e}")

        elif sub == "rm":
            if len(args) < 2:
                print("Usage: path rm <path>")
                return
            try:
                leaf_uuid = resolver.resolve(args[1])
            except ValueError as e:
                print(f"Error: {e}")
                return
            descendants = resolver.collect_descendants(leaf_uuid)
            all_uuids = [leaf_uuid] + descendants
            manager = NodeManager(self.vault.path)
            nodes = manager.list_nodes()
            for n in nodes:
                matching = [p for p in all_uuids if p in n.paths]
                if matching:
                    n.paths = [p for p in n.paths if p not in all_uuids]
                    storage_dir = compute_storage_path(self.vault.path, n.uuid)
                    meta_path = NodeMetadata.metadata_path(storage_dir)
                    n.save(meta_path)
            import shutil
            for uid in all_uuids:
                sdir = compute_storage_path(self.vault.path, uid)
                if os.path.exists(sdir):
                    shutil.rmtree(sdir)
            print(f"Removed path: {args[1]}")

        elif sub == "tree":
            path_str = args[1] if len(args) > 1 else ""
            try:
                root_uuid = resolver.resolve(path_str if path_str else "/")
            except ValueError as e:
                print(f"Error: {e}")
                return

            nodes = resolver._all_nodes()
            nodes_by_uuid = {n.uuid: n for n in nodes}

            root_node = nodes_by_uuid.get(root_uuid)
            if root_node is None:
                print("No path found.")
                return

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
                print(f"{prefix}{connector}{name}{suffix}")
                children = sorted(
                    resolver._find_children(uuid, nodes),
                    key=lambda c: c.fields.get("name", ""),
                )
                child_prefix = prefix + ("    " if is_last else "│   ")
                for i, child in enumerate(children):
                    _render(child.uuid, child_prefix, i == len(children) - 1)

            name = root_node.fields.get("name", "/")
            ref_count = _count_referencing(root_uuid)
            suffix = f" ({ref_count} nodes)" if ref_count > 0 else ""
            print(f"{name}{suffix}")
            children = sorted(
                resolver._find_children(root_uuid, nodes),
                key=lambda c: c.fields.get("name", ""),
            )
            for i, child in enumerate(children):
                _render(child.uuid, "", i == len(children) - 1)

        else:
            print(f"Unknown path subcommand: {sub}")
            print("Usage: path create <path> | path rm <path> | path tree [<path>]")

    def _cmd_rm(self, args: list[str]) -> None:
        if not args:
            print("Usage: rm <uuid>")
            return
        assert self.vault is not None
        manager = NodeManager(self.vault.path)
        if manager.delete_node(args[0]):
            print(f"Deleted node {args[0]}")
        else:
            print(f"Node not found: {args[0]}")

    def _cmd_query(self, args: list[str]) -> None:
        if not args:
            print("Usage: query <query>")
            return
        query_str = " ".join(args)
        assert self.vault is not None
        parser = QueryParser()
        ast = parser.parse(query_str)
        engine = QueryEngine(self.vault.path)
        results = engine.execute(ast)

        if not results:
            print("No results found")
            return

        print(f"{'UUID':<12} {'Type':<12} {'Title':<30} {'Tags':<20} {'Updated':<25}")
        print("-" * 99)
        for node in results:
            tags = ", ".join(node.tags) if node.tags else ""
            print(
                f"{node.uuid[:12]:<12} "
                f"{node.type:<12} "
                f"{node.title[:30]:<30} "
                f"{tags[:20]:<20} "
                f"{node.updated_at[:25]:<25}"
            )

    def _cmd_link(self, args: list[str]) -> None:
        if len(args) < 2:
            print("Usage: link <source-uuid> <target-uuid>")
            return
        source_uuid, target_uuid = args[0], args[1]
        assert self.vault is not None
        try:
            full_source = resolve_uuid(self.vault.path, source_uuid)
            full_target = resolve_uuid(self.vault.path, target_uuid)
        except ValueError as e:
            print(f"Error: {e}")
            return

        manager = NodeManager(self.vault.path)
        all_nodes = manager.list_nodes()
        source = next((n for n in all_nodes if n.uuid == full_source), None)
        target = next((n for n in all_nodes if n.uuid == full_target), None)

        if source is None:
            print(f"Source node not found: {source_uuid}")
            return
        if target is None:
            print("Warning: Target node does not exist in any registered vault")

        storage_dir = os.path.join(self.vault.path, ".storage")
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
            print(f"Could not find metadata for {source_uuid}")
            return

        source_meta = NodeMetadata.from_toml(meta_path)
        link_entry = {
            "target": target_uuid,
            "type": target.type if target else "",
            "title": target.title if target else "",
        }

        for existing in source_meta.links:
            if existing.get("target") == target_uuid:
                print("Link already exists.")
                return

        source_meta.links.append(link_entry)
        source_meta.sync_dirty = True
        source_meta.save(meta_path)
        self.last_uuid = full_source
        print(f"Linked {full_source[:8]} -> {full_target[:8]}")

    def _cmd_backlinks(self, args: list[str]) -> None:
        if not args:
            print("Usage: backlinks <uuid>")
            return
        assert self.vault is not None
        try:
            full_uuid = resolve_uuid(self.vault.path, args[0])
        except ValueError as e:
            print(f"Error: {e}")
            return

        index = BacklinkIndex(self.vault.path)
        links = index.get_backlinks(full_uuid)
        if not links:
            print("No backlinks found.")
            return
        for link in links:
            print(f"  {link['uuid'][:8]}  {link.get('title', '?')}  ({link.get('type', '?')})")

    def _cmd_graph(self, args: list[str]) -> None:
        fmt = "dot"
        if args and args[0] in ("dot", "json"):
            fmt = args[0]
        assert self.vault is not None

        manager = NodeManager(self.vault.path)
        nodes = manager.list_nodes()
        exporter = GraphExporter(self.vault.path)

        if fmt == "dot":
            print(exporter.export_dot(nodes))
        else:
            print(exporter.export_json(nodes))

    def _cmd_status(self, args: list[str]) -> None:
        assert self.vault is not None
        tracker = ChangeTracker(self.vault.path)
        report = tracker.status()

        changed = report.get("changed", [])
        new_files = report.get("new_files", [])
        orphaned = report.get("orphaned", [])

        if changed:
            print("Changed nodes:")
            for node in changed:
                print(f"  {node['uuid'][:8]} {node.get('title', '?')}")
        if new_files:
            print("New files detected:")
            for f in new_files:
                print(f"  {f['path']}")
        if orphaned:
            print("Missing nodes (index references deleted storage):")
            for o in orphaned:
                print(f"  {o['uuid']}")
        if not changed and not new_files and not orphaned:
            print("Vault is clean.")

        for node in changed:
            resp = input(f"Re-extract links from changed note {node['uuid']}? [y/N]: ").strip().lower()
            if resp == "y":
                tracker.re_extract_links(node["uuid"])

    def _cmd_add_file(self, args: list[str]) -> None:
        if not args:
            print("Usage: add-file <path> [--type <type>]")
            return
        assert self.vault is not None

        source_path = args[0]
        type_name = "file"
        if "--type" in args:
            idx = args.index("--type")
            if idx + 1 < len(args):
                type_name = args[idx + 1]

        source_path = os.path.abspath(source_path)
        if not os.path.exists(source_path):
            print(f"File not found: {source_path}")
            return

        file_hash = sha256_file(source_path)
        manager = NodeManager(self.vault.path)

        for node in manager.list_nodes():
            if node.blob_sha256 == file_hash:
                print(f"File already exists as node {node.uuid}")
                confirm = input("Create a second reference? [y/N]: ").strip().lower()
                if confirm != "y":
                    return
                break

        try:
            meta = manager.create_node(
                type_name=type_name,
                title=os.path.basename(source_path),
                blob_path=source_path,
            )
            self.last_uuid = meta.uuid
            print(f"Imported as node {meta.uuid}")
        except ValueError as e:
            print(f"Error: {e}")

    def _cmd_verify(self, args: list[str]) -> None:
        if not args:
            print("Usage: verify <uuid>")
            return
        assert self.vault is not None
        try:
            full_uuid = resolve_uuid(self.vault.path, args[0])
        except ValueError as e:
            print(f"Error: {e}")
            return

        manager = NodeManager(self.vault.path)
        all_nodes = manager.list_nodes()
        node = next((n for n in all_nodes if n.uuid == full_uuid), None)
        if node is None:
            print(f"Node not found: {args[0]}")
            return

        ok = manager.storage.verify_integrity(full_uuid, node.blob_sha256)
        if ok:
            print("OK")
        else:
            print("CORRUPTED")

    def _cmd_help(self, args: list[str]) -> None:
        if args:
            cmd = args[0]
            if cmd in ALIASES:
                cmd = ALIASES[cmd]
            help_texts = {
                "init": "Initialize a new vault at the given path.",
                "open": "Open an existing vault.",
                "new": "Create a new typed node. Usage: new <type> [title] [--tag <tag> ...] [--add-path <path>]",
                "show": "Display node details. Usage: show <uuid>",
                "edit": "Edit a node's body or fields. Usage: edit <uuid> [--add-path <path>] [--remove-path <path>]",
                "rm": "Delete a node. Usage: rm <uuid>",
                "query": "Search nodes. Usage: query <query>",
                "link": "Create a directed link. Usage: link <source> <target>",
                "backlinks": "Show backlinks for a node. Usage: backlinks <uuid>",
                "graph": "Export the node graph. Usage: graph [dot|json]",
                "status": "Show vault status.",
                "add-file": "Import a file. Usage: add-file <path> [--type <type>]",
                "verify": "Verify blob integrity. Usage: verify <uuid>",
                "path": "Manage path hierarchy. Usage: path create <path> | path rm <path> | path tree [<path>]",
                "history": "Show command history.",
                "help": "Show this help message. Use 'help <command>' for specific help.",
                "exit": "Exit the REPL.",
                "quit": "Exit the REPL.",
            }
            print(help_texts.get(cmd, f"No help available for '{cmd}'."))
            return

        print("Available commands:")
        print()
        cmds = [
            ("init", "Initialize a new vault"),
            ("open", "Open an existing vault"),
            ("new (n)", "Create a new typed node"),
            ("show (s)", "Display node details"),
            ("edit (e)", "Edit a node"),
            ("rm", "Delete a node"),
            ("query (q)", "Search nodes"),
            ("link (l)", "Create a directed link"),
            ("backlinks (bl)", "Show backlinks"),
            ("graph (g)", "Export the node graph"),
            ("status (st)", "Show vault status"),
            ("add-file (af)", "Import a file"),
            ("verify (v)", "Verify blob integrity"),
            ("path", "Manage path hierarchy (create/rm/tree)"),
            ("history", "Show command history"),
            ("exit / quit", "Exit the REPL"),
        ]
        for cmd, desc in cmds:
            print(f"  {cmd:<20} {desc}")

        if self.vault is None:
            print()
            print("Note: No vault connected. Only init, open, help, history, exit are available.")

        print()
        print("Use 'help <command>' for detailed usage.")
        print("Use '_' in place of a UUID to reference the last used node.")

    def _cmd_history(self, args: list[str]) -> None:
        length = readline.get_current_history_length()
        for i in range(1, length):
            print(f"{i:4}  {readline.get_history_item(i)}")

    def _complete(self, text: str, state: int) -> Optional[str]:
        if state == 0:
            self._completion_matches = self._get_completions(text)
        try:
            return self._completion_matches[state]
        except IndexError:
            return None

    def _get_completions(self, text: str) -> list[str]:
        line = readline.get_line_buffer()
        parts = line.split()

        if len(parts) <= 1:
            return self._complete_command(text)

        cmd = ALIASES.get(parts[0], parts[0])

        if cmd == "path":
            subs = ["create", "rm", "tree"]
            if len(parts) == 2:
                if text:
                    return [s for s in subs if s.startswith(text)]
                return subs
            if len(parts) >= 3 and parts[1] in subs:
                return self._complete_path(text)
            return []

        if text.startswith("path:"):
            return self._complete_path(text)

        for i, part in enumerate(parts):
            if part in ("--tag", "-t") and i + 1 >= len(parts):
                return self._complete_tag(text)
            if part in ("--add-path", "-a", "--remove-path", "-r") and i + 1 >= len(parts):
                return self._complete_path(text)

        if cmd == "new" and len(parts) <= 2 and text:
            return self._complete_type_name(text)

        return self._complete_uuid(text)

    def _complete_command(self, text: str) -> list[str]:
        all_commands = sorted(set(list(ALIASES.keys()) + list(ALIASES.values()) + list(UNSUPPORTED_IN_REPL) + ["init", "open", "help", "history", "exit", "quit", "rm", "path"]))
        if not text:
            return all_commands
        return [c for c in all_commands if c.startswith(text)]

    def _complete_uuid(self, text: str) -> list[str]:
        if self.vault is None:
            return []
        manager = NodeManager(self.vault.path)
        try:
            nodes = manager.list_nodes()
        except Exception:
            return []
        if not text:
            return [n.uuid for n in nodes]
        return [n.uuid for n in nodes if n.uuid.startswith(text)]

    def _complete_type_name(self, text: str) -> list[str]:
        if self.vault is None:
            return []
        types_dir = os.path.join(self.vault.path, ".metadata", "types")
        loader = TypeLoader(types_dir)
        schemas = loader.load_all()
        names = list(schemas.keys())
        if not text:
            return names
        return [n for n in names if n.startswith(text)]

    def _complete_tag(self, text: str) -> list[str]:
        if self.vault is None:
            return []
        tags: set[str] = set()
        manager = NodeManager(self.vault.path)
        try:
            for node in manager.list_nodes():
                tags.update(node.tags)
        except Exception:
            return []
        if not text:
            return sorted(tags)
        return sorted(t for t in tags if t.startswith(text))

    def _complete_path(self, text: str) -> list[str]:
        if self.vault is None:
            return []
        path_prefix = text
        if text.startswith("path:"):
            path_prefix = text[5:]
        resolver = PathResolver(self.vault.path)
        try:
            completions = resolver.complete(path_prefix)
        except Exception:
            return []
        if text.startswith("path:"):
            return [f"path:{p}" for p in completions]
        return completions
