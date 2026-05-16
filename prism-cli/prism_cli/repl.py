"""Interactive REPL for Prism.

Wraps CLI commands in an interactive shell with command dispatch,
UUID shorthand (`_`), tab completion, and history persistence.
"""

import os
import readline
import subprocess
import sys
from typing import Any, Optional, TextIO

from prism.node.storage import sha256_file
from prism.vault.vault import Vault

from . import commands, completions

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


class Repl:
    """Interactive REPL session for Prism.

    Wraps CLI commands with tab completion, history, alias resolution,
    UUID shorthand (`_`), and degraded-mode operation without a vault.
    """

    def __init__(
        self,
        vault: Optional[Vault] = None,
        input_stream: Optional[TextIO] = None,
        output_stream: Optional[TextIO] = None,
    ) -> None:
        """Initialize the REPL session.

        Args:
            vault: Optional vault to connect to.
            input_stream: Custom input stream (for testing).
            output_stream: Custom output stream (for testing).
        """
        self.vault = vault
        self.last_uuid: Optional[str] = None
        self._completion_matches: list[str] = []
        self._input = input_stream
        self._output = output_stream
        self._setup_history()
        self._setup_completion()

    def _p(self, *objects: object, sep: str = " ", end: str = "\n") -> None:
        out = self._output if self._output is not None else sys.stdout
        out.write(sep.join(str(o) for o in objects) + end)
        out.flush()

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
                    self._p("Error: No previous node")
                    return None
                resolved.append(self.last_uuid)
            else:
                resolved.append(arg)
        return resolved

    def run(self) -> None:
        """Run the main REPL event loop.

        Reads commands from input, dispatches them to handler methods,
        and persists history on exit.
        """
        inp = self._input if self._input is not None else sys.stdin
        out = self._output if self._output is not None else sys.stdout
        out.write("Prism REPL. Type 'help' for commands, 'exit' to quit.\n")
        if self.vault:
            out.write(f"Connected to vault: {self.vault.path}\n")
        else:
            out.write("No vault connected. Run 'init' or 'open' to connect.\n")
        out.flush()

        while True:
            try:
                out.write("prism> ")
                out.flush()
                raw = inp.readline()
            except KeyboardInterrupt:
                out.write("\n")
                continue

            if not raw:
                out.write("\n")
                self._save_history()
                break

            line = raw.strip()
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
            self._p(
                f"The {cmd} command cannot run inside the REPL. Run `prism {cmd}` from your shell."
            )
            return False

        if cmd in ALIASES:
            cmd = ALIASES[cmd]

        if self.vault is None and cmd not in DEGRADED_COMMANDS:
            self._p("No vault connected. Use 'init' or 'open' first.")
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
            "tag": self._cmd_tag,
        }

        handler = dispatch.get(cmd)
        if handler:
            handler(args)
        else:
            self._p(f"Unknown command: {cmd}. Type 'help' for available commands.")

        return False

    def _cmd_init(self, args: list[str]) -> None:
        path = args[0] if args else "."
        result = commands.init_vault(path)
        if result.ok:
            self.vault = result.data["vault"]
            self._p(f"Vault initialized at {result.data['path']}")
            self._p(f"Vault UUID: {result.data['vault_uuid']}")
        else:
            self._p(f"Error: {result.error}")

    def _cmd_open(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: open <path>")
            return
        result = commands.open_vault(args[0])
        if result.ok:
            self.vault = result.data["vault"]
            self._p(f"Connected to vault: {self.vault.path}")
        else:
            self._p(f"Error: {result.error}")

    def _cmd_new(self, args: list[str]) -> None:
        if not args:
            self._p(
                "Usage: new <type> [title] [--tag <tag> ...] "
                "[--add-path <path>] [--field=value ...]"
            )
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
        result = commands.create_node(
            self.vault,
            type_name,
            title,
            fields=extra_fields,  # type: ignore[arg-type]
            tags=tags if tags else None,
            add_path=add_path,
        )
        if result.ok:
            meta = result.data["meta"]
            self.last_uuid = meta.uuid
            self._p(f"Created {type_name} node: {meta.uuid}")
            if result.data.get("path_added"):
                self._p(f"Added path: {add_path}")
            elif "warning" in result.data:
                self._p(f"Path does not exist: {add_path}")
        else:
            self._p(f"Error: {result.error}")

    def _cmd_show(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: show <uuid>")
            return
        assert self.vault is not None
        result = commands.show_node(self.vault, args[0])
        if result.ok:
            self._p(result.data["output"])
        else:
            self._p(result.error)

    def _cmd_edit(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: edit <uuid> [--add-path <path>] [--remove-path <path>]")
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

        if add_path is not None or remove_path is not None:
            result = commands.edit_node(
                self.vault,
                uuid_arg,
                add_path=add_path,
                remove_path=remove_path,
            )
            if result.ok:
                action = result.data.get("action", "")
                path = result.data.get("path", "")
                if action == "add_path":
                    self._p(f"Added path: {path}")
                elif action == "add_path_skipped":
                    self._p("Node already associated with this path.")
                elif action == "remove_path":
                    self._p(f"Removed path: {path}")
                elif action == "remove_path_skipped":
                    self._p("Node not associated with this path.")
            else:
                self._p(f"Error: {result.error}")
            return

        body_result = commands.edit_node_body(self.vault, uuid_arg)
        if body_result.ok and body_result.data.get("type") == "body":
            body_path: str = body_result.data["body_path"]
            original_mtime: float = body_result.data["original_mtime"]
            editor = os.environ.get("EDITOR", "vi")
            subprocess.call([editor, body_path])
            new_mtime = os.stat(body_path).st_mtime
            if new_mtime == original_mtime:
                self._p("No changes detected.")
                return
            new_size = os.stat(body_path).st_size
            new_sha256 = sha256_file(body_path)
            result = commands.commit_body_edit(
                self.vault,
                uuid_arg,
                new_mtime,
                new_size,
                new_sha256,
            )
            if result.ok:
                self._p("Body updated.")
                self.last_uuid = uuid_arg
            return

        fields_result = commands.edit_node_fields(self.vault, uuid_arg)
        if fields_result.ok and fields_result.data.get("type") == "fields":
            schema = fields_result.data["schema"]
            current_values: dict[str, str] = fields_result.data["current_values"]
            changes: dict[str, str] = {}
            for field_def in schema.fields:
                current = current_values.get(field_def.name, "")
                inp = self._input or sys.stdin
                out = self._output or sys.stdout
                out.write(f"Enter new {field_def.name} or press ENTER to keep [{current}]: ")
                out.flush()
                try:
                    raw = inp.readline()
                except KeyboardInterrupt:
                    out.write("\n")
                    break
                if not raw:
                    break
                new_val = raw.strip()
                if new_val:
                    changes[field_def.name] = new_val
            result = commands.update_node_fields(self.vault, uuid_arg, changes)
            if result.ok:
                self._p("Fields updated.")
                self.last_uuid = uuid_arg
            else:
                self._p("No changes detected.")
            return

        self._p(f"Node not found: {uuid_arg}")

    def _cmd_path(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: path create <path> | path rm <path> | path tree [<path>]")
            return
        assert self.vault is not None
        sub = args[0].lower()

        if sub == "create":
            if len(args) < 2:
                self._p("Usage: path create <path>")
                return
            result = commands.manage_paths(self.vault, "create", args[1])
            if result.ok:
                self._p(f"Path created: {args[1]}")
                self._p(f"Leaf UUID: {result.data['leaf_uuid']}")
            else:
                self._p(f"Error: {result.error}")

        elif sub == "rm":
            if len(args) < 2:
                self._p("Usage: path rm <path>")
                return
            result = commands.manage_paths(self.vault, "rm", args[1])
            if result.ok:
                self._p(f"Removed path: {args[1]}")
            else:
                self._p(f"Error: {result.error}")

        elif sub == "tree":
            path_str = args[1] if len(args) > 1 else ""
            result = commands.manage_paths(self.vault, "tree", path_str)
            if not result.ok:
                self._p(f"Error: {result.error}")
                return
            tree_data = result.data.get("tree")
            if tree_data is None:
                self._p("No path found.")
                return

            def _render(node: dict[str, Any], prefix: str = "", is_last: bool = True) -> None:
                name = node.get("name", node.get("uuid", "")[:8])
                ref_count = node.get("ref_count", 0)
                suffix = f" ({ref_count} nodes)" if ref_count > 0 else ""
                connector = "└── " if is_last else "├── "
                self._p(f"{prefix}{connector}{name}{suffix}")
                children = node.get("children", [])
                child_prefix = prefix + ("    " if is_last else "│   ")
                for i, child in enumerate(children):
                    _render(child, child_prefix, i == len(children) - 1)

            suffix = f" ({tree_data['ref_count']} nodes)" if tree_data["ref_count"] > 0 else ""
            self._p(f"{tree_data['name']}{suffix}")
            for i, child in enumerate(tree_data.get("children", [])):
                _render(child, "", i == len(tree_data["children"]) - 1)

        else:
            self._p(f"Unknown path subcommand: {sub}")
            self._p("Usage: path create <path> | path rm <path> | path tree [<path>]")

    def _cmd_tag(self, args: list[str]) -> None:
        if not args:
            self._p(
                "Usage: tag add <uuid> <tag> [<tag>...] | "
                "tag rm <uuid> <tag> [<tag>...] | "
                "tag list [--count] | tag rename <old> <new>"
            )
            return
        assert self.vault is not None
        sub = args[0].lower()
        sub_args = args[1:]

        if sub == "add":
            if len(sub_args) < 2:
                self._p("Usage: tag add <uuid> <tag> [<tag>...]")
                return
            result = commands.manage_tags(self.vault, "add", sub_args[0], sub_args[1:])
            if not result.ok:
                self._p(f"Error: {result.error}")
                return
            for r in result.data.get("results", []):
                if r["status"] == "added":
                    self._p(f"Added tag: {r['tag']}")
                elif r["status"] == "already_present":
                    self._p(f"Tag already present: {r['tag']}")
                elif r["status"] == "error":
                    self._p(f"Error: {r['error']}")

        elif sub == "rm":
            if len(sub_args) < 2:
                self._p("Usage: tag rm <uuid> <tag> [<tag>...]")
                return
            result = commands.manage_tags(self.vault, "rm", sub_args[0], sub_args[1:])
            if not result.ok:
                self._p(f"Error: {result.error}")
                return
            for r in result.data.get("results", []):
                if r["status"] == "removed":
                    self._p(f"Removed tag: {r['tag']}")
                elif r["status"] == "not_present":
                    self._p(f"Tag not present: {r['tag']}")

        elif sub == "list":
            show_counts = "--count" in sub_args
            result = commands.manage_tags(self.vault, "list")
            tags_dict = result.data.get("tags", {})
            if not tags_dict:
                return
            for tag_name, tag_count in tags_dict.items():
                if show_counts:
                    self._p(f"{tag_name} ({tag_count})")
                else:
                    self._p(tag_name)

        elif sub == "rename":
            if len(sub_args) < 2:
                self._p("Usage: tag rename <old-tag> <new-tag>")
                return
            result = commands.manage_tags(self.vault, "rename", tags=[sub_args[0], sub_args[1]])
            if result.ok:
                affected = result.data["affected"]
                self._p(f"Renamed tag '{sub_args[0]}' to '{sub_args[1]}' across {affected} node(s)")
            else:
                self._p(f"Error: {result.error}")

        else:
            self._p(f"Unknown tag subcommand: {sub}")

    def _cmd_rm(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: rm <uuid>")
            return
        assert self.vault is not None
        result = commands.delete_node(self.vault, args[0], force=False)
        if result.ok:
            self._p(f"Deleted node {result.data['uuid']}")
        elif result.code == "CONFIRM_REQUIRED":
            self._p(f"Warning: {result.error}")
            out = self._output or sys.stdout
            inp = self._input or sys.stdin
            out.write("Delete anyway? [y/N]: ")
            out.flush()
            confirm = inp.readline().strip().lower()
            if confirm == "y":
                result2 = commands.delete_node(self.vault, args[0], force=True)
                if result2.ok:
                    self._p(f"Deleted node {result2.data['uuid']}")
                else:
                    self._p(f"Node not found: {args[0]}")
            else:
                self._p("Aborted.")
        else:
            self._p(result.error)

    def _cmd_query(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: query <query>")
            return
        query_str = " ".join(args)
        assert self.vault is not None
        result = commands.query_nodes(self.vault, query_str)
        if not result.ok:
            self._p(f"Error: {result.error}")
            return
        results = result.data.get("results", [])
        if not results:
            self._p("No results found")
            return
        self._p(f"{'UUID':<12} {'Type':<12} {'Title':<30} {'Tags':<20} {'Updated':<25}")
        self._p("-" * 99)
        for node in results:
            tags = ", ".join(node.tags) if node.tags else ""
            self._p(
                f"{node.uuid[:12]:<12} "
                f"{node.type:<12} "
                f"{node.title[:30]:<30} "
                f"{tags[:20]:<20} "
                f"{node.updated_at[:25]:<25}"
            )

    def _cmd_link(self, args: list[str]) -> None:
        if len(args) < 2:
            self._p("Usage: link <source-uuid> <target-uuid>")
            return
        assert self.vault is not None
        result = commands.link_nodes(self.vault, args[0], args[1])
        if result.ok:
            data = result.data
            if "warning" in data:
                self._p(f"Warning: {data['warning']}")
            self._p(f"Linked {data['source'][:8]} -> {data['target'][:8]}")
            self.last_uuid = data["source"]
        else:
            if result.code == "ALREADY_EXISTS":
                self._p("Link already exists.")
                return
            self._p(result.error)

    def _cmd_backlinks(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: backlinks <uuid>")
            return
        assert self.vault is not None
        result = commands.list_backlinks(self.vault, args[0])
        if not result.ok:
            self._p(result.error)
            return
        links = result.data.get("backlinks", [])
        if not links:
            self._p("No backlinks found.")
            return
        for link in links:
            self._p(f"  {link['uuid'][:8]}  {link.get('title', '?')}  ({link.get('type', '?')})")

    def _cmd_graph(self, args: list[str]) -> None:
        fmt = "dot"
        if args and args[0] in ("dot", "json"):
            fmt = args[0]
        assert self.vault is not None
        result = commands.export_graph(self.vault, fmt)
        if result.ok:
            self._p(result.data["output"])

    def _cmd_status(self, _args: list[str]) -> None:
        assert self.vault is not None
        result = commands.vault_status(self.vault)
        report = result.data
        changed = report.get("changed", [])
        new_files = report.get("new_files", [])
        orphaned = report.get("orphaned", [])
        if changed:
            self._p("Changed nodes:")
            for node in changed:
                self._p(f"  {node['uuid'][:8]} {node.get('title', '?')}")
        if new_files:
            self._p("New files detected:")
            for f in new_files:
                self._p(f"  {f['path']}")
        if orphaned:
            self._p("Missing nodes (index references deleted storage):")
            for o in orphaned:
                self._p(f"  {o['uuid']}")
        if not changed and not new_files and not orphaned:
            self._p("Vault is clean.")
        out = self._output or sys.stdout
        inp = self._input or sys.stdin
        for node in changed:
            out.write(f"Re-extract links from changed note {node['uuid']}? [y/N]: ")
            out.flush()
            resp = inp.readline().strip().lower()
            if resp == "y":
                from prism.tracking import ChangeTracker

                tracker = ChangeTracker(self.vault.path)
                tracker.re_extract_links(node["uuid"])

    def _cmd_add_file(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: add-file <path> [--type <type>]")
            return
        assert self.vault is not None
        source_path = args[0]
        type_name: Optional[str] = None
        if "--type" in args:
            idx = args.index("--type")
            if idx + 1 < len(args):
                type_name = args[idx + 1]
        result = commands.import_file(self.vault, source_path, type_name)
        if result.code == "ALREADY_EXISTS":
            self._p(f"File already exists as node {result.data['uuid']}")
            out = self._output or sys.stdout
            inp = self._input or sys.stdin
            out.write("Create a second reference? [y/N]: ")
            out.flush()
            confirm = inp.readline().strip().lower()
            if confirm != "y":
                return
            result = commands.import_file(self.vault, source_path, type_name, force=True)
        if result.ok:
            self.last_uuid = result.data["uuid"]
            self._p(f"Imported as node {result.data['uuid']}")
        else:
            self._p(f"Error: {result.error}")

    def _cmd_verify(self, args: list[str]) -> None:
        if not args:
            self._p("Usage: verify <uuid>")
            return
        assert self.vault is not None
        result = commands.verify_node(self.vault, args[0])
        if result.ok:
            self._p("OK")
        else:
            self._p(result.error)

    def _cmd_help(self, args: list[str]) -> None:
        if args:
            cmd = args[0]
            if cmd in ALIASES:
                cmd = ALIASES[cmd]
            help_texts = {
                "init": "Initialize a new vault at the given path.",
                "open": "Open an existing vault.",
                "new": (
                    "Create a new typed node. Usage: new <type> [title] "
                    "[--tag <tag> ...] [--add-path <path>]"
                ),
                "show": "Display node details. Usage: show <uuid>",
                "edit": (
                    "Edit a node's body or fields. Usage: edit <uuid> "
                    "[--add-path <path>] [--remove-path <path>]"
                ),
                "rm": "Delete a node. Usage: rm <uuid>",
                "query": "Search nodes. Usage: query <query>",
                "link": "Create a directed link. Usage: link <source> <target>",
                "backlinks": "Show backlinks for a node. Usage: backlinks <uuid>",
                "graph": "Export the node graph. Usage: graph [dot|json]",
                "status": "Show vault status.",
                "add-file": "Import a file. Usage: add-file <path> [--type <type>]",
                "verify": "Verify blob integrity. Usage: verify <uuid>",
                "tag": (
                    "Manage tags. Usage: tag add <uuid> <tag> [<tag>...] | "
                    "tag rm <uuid> <tag> [<tag>...] | "
                    "tag list [--count] | tag rename <old> <new>"
                ),
                "path": (
                    "Manage path hierarchy. Usage: path create <path> | "
                    "path rm <path> | path tree [<path>]"
                ),
                "history": "Show command history.",
                "help": "Show this help message. Use 'help <command>' for specific help.",
                "exit": "Exit the REPL.",
                "quit": "Exit the REPL.",
            }
            self._p(help_texts.get(cmd, f"No help available for '{cmd}'."))
            return

        self._p("Available commands:")
        self._p()
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
            ("tag", "Manage tags (add/rm/list/rename)"),
            ("path", "Manage path hierarchy (create/rm/tree)"),
            ("history", "Show command history"),
            ("exit / quit", "Exit the REPL"),
        ]
        for cmd, desc in cmds:
            self._p(f"  {cmd:<20} {desc}")

        if self.vault is None:
            self._p()
            self._p("Note: No vault connected. Only init, open, help, history, exit are available.")

        self._p()
        self._p("Use 'help <command>' for detailed usage.")
        self._p("Use '_' in place of a UUID to reference the last used node.")

    def _cmd_history(self, _args: list[str]) -> None:
        length = readline.get_current_history_length()
        for i in range(1, length):
            self._p(f"{i:4}  {readline.get_history_item(i)}")

    def _complete(self, text: str, state: int) -> Optional[str]:
        if state == 0:
            line = readline.get_line_buffer()
            parts = line.split()
            self._completion_matches = completions.resolve_completions(
                parts,
                text,
                self.vault,
                ALIASES,
            )
        try:
            return self._completion_matches[state]
        except IndexError:
            return None
