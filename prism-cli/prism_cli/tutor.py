import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from prism.vault.vault import Vault


class StepResult(Enum):
    SUCCESS = "success"
    WARNING_RETRY = "warning_retry"
    SKIP = "skip"


@dataclass
class Step:
    number: int
    concept: str
    command: str
    verify: Callable[[Vault], bool]
    warning: str = ""


@dataclass
class Lesson:
    number: int
    title: str
    concept: str
    steps: list[Step]
    summary: str = ""


TOTAL_LESSONS = 8


class Tutor:
    def __init__(self, lesson_number: int = 1) -> None:
        self.lesson_number = lesson_number
        self.temp_dir: str = ""
        self.vault: Optional[Vault] = None
        self._fmt: dict[str, str] = {}

    # --- Vault management ---

    def _create_temp_vault(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="prism-tutor-")

    def _ensure_vault_open(self) -> Optional[Vault]:
        meta_path = os.path.join(self.temp_dir, ".metadata", "vault.toml")
        if os.path.exists(meta_path):
            self.vault = Vault.open(self.temp_dir)
            return self.vault
        return None

    def _write_builtin_types(self, vault: Vault) -> None:
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

    def _cleanup(self, keep: bool) -> None:
        if keep and self.vault and self.temp_dir:
            print(f"Vault saved at {self.vault.path}")
        elif self.temp_dir:
            shutil.rmtree(self.temp_dir)

    def _prompt_keep_vault(self) -> bool:
        try:
            response = input("Tutorial complete! Keep your practice vault? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return response == "y"

    # --- Output rendering ---

    def _show_header(self, lesson_number: int, lesson_title: str, total_lessons: int) -> None:
        print()
        print("=" * 60)
        print(f"  Lesson {lesson_number}/{total_lessons}: {lesson_title}")
        print("=" * 60)
        print()

    def _show_concept(self, text: str) -> None:
        for paragraph in text.split("\n\n"):
            wrapped = textwrap.fill(paragraph.strip(), width=58)
            print(wrapped)
            print()

    def _show_command(self, cmd: str) -> None:
        print("." * 60)
        print(f"  $ {cmd}")
        print("." * 60)
        print()

    def _show_success(self, message: str) -> None:
        print(f"  OK {message}")
        print()

    def _show_warning(self, message: str) -> None:
        print(f"  ! {message}")
        print()

    def _show_progress(self, current: int, total: int) -> None:
        print(f"  Step {current}/{total}")
        print()

    def _show_final_summary(self) -> None:
        print("=" * 60)
        print("  Congratulations! You've completed all 8 lessons.")
        print()
        print("  You now know how to:")
        print("    - Create and initialize a vault")
        print("    - Create different types of nodes (notes, contacts, bookmarks)")
        print("    - Link nodes together and explore connections")
        print("    - Query your vault with tags, types, and full-text search")
        print("    - Import files and verify their integrity")
        print("    - Track changes in your vault")
        print("    - Manage tags on any node")
        print()
        print("  Next steps:")
        print("    - Run `prism --help` to see all commands")
        print("    - Check the README for advanced usage")
        print("    - Create your own vault with `prism init`")
        print("=" * 60)
        print()

    def _show_auto_run(self, cmd: str) -> None:
        print(f"  -> Auto-running: {cmd}")
        print()

    def _show_output(self, text: str) -> None:
        showed = False
        for line in text.split("\n"):
            stripped = line.rstrip()
            if stripped:
                print(f"  -> {stripped}")
                showed = True
        if showed:
            print()

    # --- Execution ---

    def _execute_command(self, command_str: str) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(
                command_str,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.temp_dir,
            )
        except KeyboardInterrupt:
            raise

        if result.returncode == -signal.SIGINT:
            raise KeyboardInterrupt()

        return result

    def _build_prism_cmd(self, cmd: str) -> str:
        inner = cmd.removeprefix("prism ")
        return f"{sys.executable} -m prism_cli.main {inner}"

    # --- Verification helpers ---

    def _verify_vault_init(self, vault: Vault) -> bool:
        return os.path.exists(os.path.join(vault.path, ".metadata", "vault.toml"))

    def _verify_node_count(self, vault: Vault, expected_count: int, expected_type: str) -> bool:
        from prism.node.manager import NodeManager
        manager = NodeManager(vault.path)
        nodes = manager.list_nodes()
        matching = [n for n in nodes if n.type == expected_type]
        return len(matching) == expected_count

    def _verify_node_has_tag(self, vault: Vault, uuid: str, tag: str) -> bool:
        from prism.node.metadata import NodeMetadata
        from prism.node.storage import compute_storage_path
        storage_dir = compute_storage_path(vault.path, uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return False
        meta = NodeMetadata.from_toml(meta_path)
        return tag in meta.tags

    def _verify_link_exists(self, vault: Vault, source_uuid: str, target_uuid: str) -> bool:
        from prism.node.manager import resolve_uuid
        from prism.node.metadata import NodeMetadata
        from prism.node.storage import compute_storage_path
        try:
            full_source = resolve_uuid(vault.path, source_uuid)
        except ValueError:
            return False
        storage_dir = compute_storage_path(vault.path, full_source)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return False
        meta = NodeMetadata.from_toml(meta_path)
        return any(link.get("target", "") == target_uuid for link in meta.links)

    def _verify_backlink(self, vault: Vault, target_uuid: str, expected_source_uuid: str) -> bool:
        from prism.graph.links import BacklinkIndex
        index = BacklinkIndex(vault.path)
        backlinks = index.get_backlinks(target_uuid)
        return any(bl["uuid"] == expected_source_uuid for bl in backlinks)

    def _verify_query_result(self, vault: Vault, query_str: str, expected_uuid: str) -> bool:
        from prism.query.parser import QueryParser
        from prism.query.engine import QueryEngine
        parser = QueryParser()
        ast = parser.parse(query_str)
        engine = QueryEngine(vault.path)
        results = engine.execute(ast)
        target_uuid_full = self._fmt.get("_full_" + expected_uuid[:12], expected_uuid)
        return any(n.uuid == target_uuid_full or n.uuid == expected_uuid for n in results)

    def _verify_file_imported(self, vault: Vault, file_hash: str) -> bool:
        from prism.node.manager import NodeManager
        manager = NodeManager(vault.path)
        nodes = manager.list_nodes()
        return any(n.blob_sha256 == file_hash for n in nodes)

    def _verify_blob_integrity(self, vault: Vault, uuid: str) -> bool:
        from prism.node.manager import NodeManager
        from prism.node.metadata import NodeMetadata
        from prism.node.storage import compute_storage_path
        storage_dir = compute_storage_path(vault.path, uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return False
        meta = NodeMetadata.from_toml(meta_path)
        manager = NodeManager(vault.path)
        return manager.storage.verify_integrity(uuid, meta.blob_sha256)

    def _verify_change_detected(self, vault: Vault) -> bool:
        from prism.tracking import ChangeTracker
        tracker = ChangeTracker(vault.path)
        report = tracker.status()
        return len(report.get("changed", [])) > 0

    def _verify_tag_count(self, vault: Vault, expected: int) -> bool:
        from prism.node.manager import NodeManager
        manager = NodeManager(vault.path)
        tags_dict = manager.list_tags()
        return len(tags_dict) >= expected

    def _verify_tag_renamed(self, vault: Vault, old_tag: str, new_tag: str) -> bool:
        from prism.node.manager import NodeManager
        manager = NodeManager(vault.path)
        tags_dict = manager.list_tags()
        return old_tag not in tags_dict and new_tag in tags_dict

    def _verify_always_true(self, vault: Vault) -> bool:
        return True

    def _get_node_uuid_by_title(self, vault: Vault, title: str) -> Optional[str]:
        from prism.node.manager import NodeManager
        manager = NodeManager(vault.path)
        nodes = manager.list_nodes()
        for n in nodes:
            if n.title == title:
                return n.uuid
        return None

    def _sha256(self, path: str) -> str:
        from prism.node.storage import sha256_file
        return sha256_file(path)

    def _init_blob_mtime(self, uid: str) -> None:
        if self.vault is None:
            return
        from prism.node.metadata import NodeMetadata
        from prism.node.storage import compute_storage_path
        storage_dir = compute_storage_path(self.vault.path, uid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        if not os.path.exists(meta_path):
            return
        meta = NodeMetadata.from_toml(meta_path)
        if meta.blob_mtime or not meta.blob_extension:
            return
        body_path = os.path.join(storage_dir, f"data.{meta.blob_extension}")
        if os.path.exists(body_path):
            meta.blob_mtime = str(os.stat(body_path).st_mtime)
            meta.save(meta_path)

    def _capture_uuid(self, title: str, key: str) -> None:
        if self.vault is None:
            return
        uid = self._get_node_uuid_by_title(self.vault, title)
        if uid:
            self._fmt[key] = uid[:8]
            self._fmt["_full_" + key] = uid
            self._init_blob_mtime(uid)

    def _resolve_uuid(self, short_or_key: str) -> str:
        full = self._fmt.get("_full_" + short_or_key, "")
        return full or short_or_key

    # --- Lesson and step execution ---

    def _run_lesson(self, lesson: Lesson) -> None:
        self._show_header(lesson.number, lesson.title, TOTAL_LESSONS)
        self._show_concept(lesson.concept)

        if lesson.number == 8 and self.vault:
            self._write_to_note_body("My first note", "## Ideas\n\n- Learn Prism\n")
            print("  I've written an update to your note. Run `prism status` to see what happened.")
            print()

        total_steps = len(lesson.steps)
        for i, step in enumerate(lesson.steps, 1):
            self._show_progress(i, total_steps)
            self._run_step(step)
            if lesson.number == 2 and i == 1:
                self._capture_uuid("My first note", "note1")
            elif lesson.number == 3 and i == 1:
                self._capture_uuid("Alice", "alice")
            elif lesson.number == 3 and i == 2:
                self._capture_uuid("Prism", "bookmark1")
            elif lesson.number == 4 and i == 1:
                self._capture_uuid("Second note", "note2")
            elif lesson.number == 6 and i == 2:
                self._capture_uuid("hello.txt", "file1")
            elif lesson.number == 7 and i == 1:
                self._capture_uuid("Monday notes", "note1")

        if lesson.summary:
            self._show_concept(lesson.summary)

    def _write_to_note_body(self, title: str, content: str) -> None:
        if self.vault is None:
            return
        from prism.node.storage import compute_storage_path
        uid = self._get_node_uuid_by_title(self.vault, title)
        if uid is None:
            return
        storage_dir = compute_storage_path(self.vault.path, uid)
        body_path = os.path.join(storage_dir, "data.md")
        if not os.path.exists(body_path):
            os.makedirs(storage_dir, exist_ok=True)
        with open(body_path, "w") as f:
            f.write(content)

    def _run_step(self, step: Step) -> StepResult:
        self._show_concept(step.concept)
        expected_cmd = step.command.format(**self._fmt)
        if expected_cmd.startswith("prism "):
            full_cmd = self._build_prism_cmd(expected_cmd)
            is_prism_cmd = True
        else:
            full_cmd = expected_cmd
            is_prism_cmd = False

        self._show_command(expected_cmd)

        try:
            user_input = input("Type command (or ENTER to auto-run): $ ").strip()
        except (EOFError, KeyboardInterrupt):
            raise

        if not user_input:
            self._show_auto_run(expected_cmd)
            actual_cmd = full_cmd
        elif is_prism_cmd and user_input == expected_cmd:
            actual_cmd = self._build_prism_cmd(user_input)
        elif not is_prism_cmd and user_input == expected_cmd:
            actual_cmd = user_input
        else:
            self._show_warning(step.warning or "That doesn't match the suggested command.")
            try:
                retry = input("Try again? [Y/n] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                raise
            if retry == "y" or retry == "":
                return self._run_step(step)
            self._show_auto_run(expected_cmd)
            actual_cmd = full_cmd

        result = self._execute_command(actual_cmd)

        if result.returncode != 0:
            if result.stderr:
                self._show_warning(result.stderr.strip())
            try:
                retry = input("Command failed. Try again? [Y/n] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                raise
            if retry == "y" or retry == "":
                return self._run_step(step)
            self._show_warning("Skipping step.")
            return StepResult.SKIP

        self._ensure_vault_open()
        if self.vault and step.verify(self.vault):
            if result.stdout.strip():
                self._show_output(result.stdout.strip())
            self._show_success("Step complete!")
            return StepResult.SUCCESS

        self._show_warning(step.warning or "Verification failed.")
        try:
            retry = input("Try again? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise
        if retry == "y" or retry == "":
            return self._run_step(step)
        self._show_warning("Skipping step.")
        return StepResult.SKIP

    # --- Lesson plan ---

    def _build_lesson_plan(self) -> list[Lesson]:
        l1 = Lesson(
            number=1,
            title="What's a vault?",
            concept="A vault is a folder that holds all your notes, contacts, and files. "
                    "Prism organizes everything inside this directory, with metadata and "
                    "storage managed automatically.",
            steps=[
                Step(
                    number=1,
                    concept="First, let's create a vault in this directory. "
                            "`prism init` sets up the .metadata and .storage directories "
                            "that Prism needs.",
                    command="prism init .",
                    verify=lambda v: self._verify_vault_init(v),
                    warning="Make sure you ran `prism init .`",
                ),
                Step(
                    number=2,
                    concept="`prism status` shows the current state of your vault. "
                            "Since we just created it, everything should be clean.",
                    command="prism status",
                    verify=lambda v: self._verify_vault_init(v),
                    warning="Try running `prism status`",
                ),
            ],
            summary="Your vault is ready. It has a .metadata directory for configuration "
                    "and a .storage directory where your data lives.",
        )

        l2 = Lesson(
            number=2,
            title="Your first note",
            concept="A node is a typed 'thing' in your vault. Notes are the most common "
                    "type — they have a title, optional tags, and a markdown body.",
            steps=[
                Step(
                    number=1,
                    concept="Let's create your first note. The `--tag` flag adds a tag, "
                            "which helps you find things later.",
                    command='prism new note "My first note" --tag ideas',
                    verify=lambda v: self._verify_node_count(v, 1, "note"),
                    warning="Try: prism new note \"My first note\" --tag ideas",
                ),
                Step(
                    number=2,
                    concept="`prism show` displays a node's details including its type, "
                            "tags, fields, and body content.",
                    command="prism show {note1}",
                    verify=lambda v: self._verify_node_count(v, 1, "note"),
                    warning="Use the UUID from the previous step",
                ),
                Step(
                    number=3,
                    concept="You can find nodes by tag using the query command. "
                            "`prism query tag:ideas` finds everything tagged 'ideas'.",
                    command="prism query tag:ideas",
                    verify=lambda v: self._verify_query_result(v, "tag:ideas",
                        self._resolve_uuid("note1")),
                    warning="Try: prism query tag:ideas",
                ),
            ],
            summary="You created a note, viewed its details, and found it with a tag query. "
                    "Every node in Prism works the same way.",
        )

        l3 = Lesson(
            number=3,
            title="Different kinds of things",
            concept="Types give nodes the right fields for their purpose. A contact has "
                    "a name and email, a bookmark has a URL. Prism comes with 4 built-in "
                    "types: note, contact, bookmark, and file.",
            steps=[
                Step(
                    number=1,
                    concept="Create a contact node. Contacts have structured fields "
                            "like name and email.",
                    command='prism new contact Alice --name=Alice --email=alice@example.com',
                    verify=lambda v: self._verify_node_count(v, 1, "contact"),
                    warning='Try: prism new contact Alice --name=Alice --email=alice@example.com',
                ),
                Step(
                    number=2,
                    concept="Create a bookmark to save a link. Bookmarks have a url field.",
                    command='prism new bookmark Prism --url=https://prism.ai --tag favorite',
                    verify=lambda v: self._verify_node_count(v, 1, "bookmark"),
                    warning='Try: prism new bookmark Prism --url=https://prism.ai --tag favorite',
                ),
                Step(
                    number=3,
                    concept="You can query by type too. "
                            "`prism query type:contact` shows only contact nodes.",
                    command="prism query type:contact",
                    verify=lambda v: self._verify_query_result(v, "type:contact",
                        self._resolve_uuid("alice")),
                    warning="Try: prism query type:contact",
                ),
            ],
            summary="Each type has its own set of fields. Contacts store contact info, "
                    "bookmarks store URLs, and notes store markdown content.",
        )

        l4 = Lesson(
            number=4,
            title="Connecting ideas",
            concept="Knowledge isn't isolated. You can link related nodes together "
                    "to show how they connect. Prism tracks these links and can "
                    "show you the big picture.",
            steps=[
                Step(
                    number=1,
                    concept="Create a second note so we have something to link to.",
                    command='prism new note "Second note" --tag ideas',
                    verify=lambda v: self._verify_node_count(v, 2, "note"),
                    warning="Try: prism new note \"Second note\" --tag ideas",
                ),
                Step(
                    number=2,
                    concept="Link the first note to the second. "
                            "`prism link <source> <target>` creates a directed connection.",
                    command="prism link {note1} {note2}",
                    verify=lambda v: self._verify_link_exists(v, self._fmt.get("note1", ""),
                        self._fmt.get("note2", "")),
                    warning="Use the UUIDs of your two notes",
                ),
                Step(
                    number=3,
                    concept="`prism graph` shows all nodes and their connections "
                            "as a graph. You can export as DOT or JSON.",
                    command="prism graph",
                    verify=self._verify_always_true,
                    warning="Try: prism graph",
                ),
            ],
            summary="Links show relationships between nodes. The graph command "
                    "visualizes your vault as a connected network of ideas.",
        )

        l5 = Lesson(
            number=5,
            title="Finding things",
            concept="Prism has a powerful query language. You can combine tags, types, "
                    "and text search with AND, OR, and NOT operators.",
            steps=[
                Step(
                    number=1,
                    concept="Combine conditions with AND. This finds nodes tagged "
                            "'ideas' that are also notes.",
                    command='prism query "tag:ideas AND type:note"',
                    verify=lambda v: self._verify_query_result(v, "tag:ideas AND type:note",
                        self._resolve_uuid("note1")),
                    warning='Try: prism query "tag:ideas AND type:note"',
                ),
                Step(
                    number=2,
                    concept="Use OR to find nodes matching any condition. "
                            "This finds contacts or bookmarks.",
                    command='prism query "type:contact OR type:bookmark"',
                    verify=lambda v: self._verify_query_result(v, "type:contact OR type:bookmark",
                        self._resolve_uuid("alice")),
                    warning='Try: prism query "type:contact OR type:bookmark"',
                ),
                Step(
                    number=3,
                    concept="Prism can also search inside note bodies. "
                            "Let's search for text in your notes.",
                    command='prism query "first"',
                    verify=self._verify_always_true,
                    warning="Try: prism query \"first\"",
                ),
            ],
            summary="The query language lets you find exactly what you need. "
                    "Combine tag:, type:, and text search with AND, OR, and NOT.",
        )

        l6 = Lesson(
            number=6,
            title="Files in the vault",
            concept="A vault can store any file. Prism tracks file integrity "
                    "using SHA-256 hashes, so you always know your files are intact.",
            steps=[
                Step(
                    number=1,
                    concept="First, let's create a simple text file "
                            "that we'll import into the vault.",
                    command="echo 'Hello from Prism' > hello.txt",
                    verify=self._verify_always_true,
                    warning="Try: echo 'Hello from Prism' > hello.txt",
                ),
                Step(
                    number=2,
                    concept="`prism add-file <path>` imports a file into the vault. "
                            "Prism copies it into .storage and computes its SHA-256 hash.",
                    command="prism add-file hello.txt",
                    verify=lambda v: self._verify_node_count(v, 1, "file"),
                    warning="Try: prism add-file hello.txt",
                ),
                Step(
                    number=3,
                    concept="`prism verify <uuid>` checks that the stored file's hash "
                            "matches. This confirms the file hasn't been corrupted.",
                    command="prism verify {file1}",
                    verify=lambda v: self._verify_blob_integrity(v, self._resolve_uuid("file1")),
                    warning="Use the UUID from the import step",
                ),
            ],
            summary="Files in Prism are content-addressed by SHA-256. "
                    "You can always verify that your files are intact.",
        )

        l7 = Lesson(
            number=7,
            title="Managing tags",
            concept="Tags help you organize and find nodes. You can add, remove, list, "
                    "and rename tags after creating a node. Tags are universal — any "
                    "node type can carry any tag.",
            steps=[
                Step(
                    number=1,
                    concept="First, create a couple of notes we can tag. "
                            "We'll use them to practice tag management.",
                    command='prism new note "Monday notes" --tag work',
                    verify=lambda v: self._verify_node_count(v, 1, "note"),
                    warning="Try: prism new note \"Monday notes\" --tag work",
                ),
                Step(
                    number=2,
                    concept="Add more tags to an existing node with `prism tag add`. "
                            "Tags are universal — you can add them to any node.",
                    command='prism tag add {note1} meeting',
                    verify=lambda v: self._verify_node_has_tag(v,
                        self._resolve_uuid("note1"), "meeting"),
                    warning="Use the UUID from the previous step",
                ),
                Step(
                    number=3,
                    concept="List all tags in your vault with `prism tag list`. "
                            "This shows every unique tag across all nodes.",
                    command="prism tag list",
                    verify=lambda v: self._verify_tag_count(v, 2),
                    warning="Try: prism tag list",
                ),
                Step(
                    number=4,
                    concept="You can remove tags too. `prism tag rm` removes a tag "
                            "from a node. It's safe — removing a non-existent tag "
                            "is a no-op.",
                    command='prism tag rm {note1} meeting',
                    verify=lambda v: not self._verify_node_has_tag(v,
                        self._resolve_uuid("note1"), "meeting"),
                    warning="Use the UUID of your note",
                ),
                Step(
                    number=5,
                    concept="Tags can be renamed across your entire vault with "
                            "`prism tag rename`. This updates all nodes at once.",
                    command='prism tag rename work tasks',
                    verify=lambda v: self._verify_tag_renamed(v, "work", "tasks"),
                    warning="Try: prism tag rename work tasks",
                ),
            ],
            summary="You can manage tags on any node at any time: add, remove, "
                    "list, and rename. Tags are universal and help you organize "
                    "your vault your way.",
        )

        l8 = Lesson(
            number=8,
            title="Your vault is alive",
            concept="Prism watches for changes to your nodes. When you modify a note's "
                    "body or fields, Prism detects it automatically.",
            steps=[
                Step(
                    number=1,
                    concept="I've written a quick update to your note's body behind the scenes. "
                            "Now run `prism status` to see what Prism noticed.",
                    command="prism status",
                    verify=lambda v: self._verify_change_detected(v),
                    warning="Try: prism status",
                ),
                Step(
                    number=2,
                    concept="The vault detected the change. This is Prism's change tracking "
                            "system at work — it notices when files are modified.",
                    command="prism status",
                    verify=self._verify_always_true,
                    warning="Try: prism status",
                ),
            ],
            summary="Your vault is alive! Prism automatically tracks changes to your "
                    "nodes. You've learned the core workflows: create, link, query, "
                    "import, track, and manage tags.",
        )

        return [l1, l2, l3, l4, l5, l6, l7, l8]

    # --- Main entry ---

    def run(self) -> None:
        try:
            self._create_temp_vault()
            lessons = self._build_lesson_plan()

            if self.lesson_number < 1 or self.lesson_number > TOTAL_LESSONS:
                print(f"Lesson not found. Available: 1-{TOTAL_LESSONS}.")
                print("Starting from lesson 1.")
                self.lesson_number = 1

            for lesson in lessons:
                if lesson.number < self.lesson_number:
                    continue
                self._ensure_vault_open()
                self._run_lesson(lesson)

            keep = self._prompt_keep_vault()
            self._cleanup(keep)
        except KeyboardInterrupt:
            print()
            print("Tutorial paused. Run `prism tutor --lesson N` to resume.")
            sys.exit(0)


