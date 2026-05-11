import os
import readline
from typing import Optional

from prism.node.manager import NodeManager, resolve_uuid
from prism.node.metadata import NodeMetadata
from prism.node.storage import sha256_file
from prism.graph.links import LinkExtractor, BacklinkIndex, GraphExporter
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
    from prism.types.builtins import BOOKMARK_TOML, CONTACT_TOML, FILE_TOML, NOTE_TOML

    types_dir = os.path.join(vault.path, ".metadata", "types")
    os.makedirs(types_dir, exist_ok=True)

    types = {
        "note.toml": NOTE_TOML,
        "contact.toml": CONTACT_TOML,
        "bookmark.toml": BOOKMARK_TOML,
        "file.toml": FILE_TOML,
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
            print("Usage: new <type> [title] [--tag <tag> ...] [--field=value ...]")
            return

        type_name = args[0]
        title = ""
        tags: list[str] = []
        extra: list[str] = []
        i = 1
        while i < len(args):
            if args[i] == "--tag" and i + 1 < len(args):
                tags.append(args[i + 1])
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
            print("Usage: edit <uuid>")
            return
        assert self.vault is not None
        manager = NodeManager(self.vault.path)
        try:
            full_uuid = resolve_uuid(self.vault.path, args[0])
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
            print(f"Node not found: {args[0]}")
            return

        meta = NodeMetadata.from_toml(meta_path)
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
                "new": "Create a new typed node. Usage: new <type> [title] [--tag <tag> ...]",
                "show": "Display node details. Usage: show <uuid>",
                "edit": "Edit a node's body or fields. Usage: edit <uuid>",
                "rm": "Delete a node. Usage: rm <uuid>",
                "query": "Search nodes. Usage: query <query>",
                "link": "Create a directed link. Usage: link <source> <target>",
                "backlinks": "Show backlinks for a node. Usage: backlinks <uuid>",
                "graph": "Export the node graph. Usage: graph [dot|json]",
                "status": "Show vault status.",
                "add-file": "Import a file. Usage: add-file <path> [--type <type>]",
                "verify": "Verify blob integrity. Usage: verify <uuid>",
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

        for i, part in enumerate(parts):
            if part in ("--tag", "-t") and i + 1 >= len(parts):
                return self._complete_tag(text)

        if cmd == "new" and len(parts) <= 2 and text:
            return self._complete_type_name(text)

        return self._complete_uuid(text)

    def _complete_command(self, text: str) -> list[str]:
        all_commands = sorted(set(list(ALIASES.keys()) + list(ALIASES.values()) + list(UNSUPPORTED_IN_REPL) + ["init", "open", "help", "history", "exit", "quit", "rm"]))
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
