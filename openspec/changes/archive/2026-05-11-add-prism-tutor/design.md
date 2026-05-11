## Context

Prism has 14 CLI commands but no onboarding path. New users — especially those new to PKM — must learn both PKM concepts (vaults, typed nodes, links, backlinks) and CLI syntax simultaneously from a static README. A `prism tutor` command fills this gap with an interactive, sandboxed walkthrough.

The tutorial must:
- Work in a temp vault (no risk to real data)
- Teach through action, not just reading
- Be self-contained (no new dependencies)
- Verify each step actually worked

## Goals / Non-Goals

**Goals:**
- Interactive terminal tutorial teaching Prism to PKM beginners
- Sandboxed: creates temp vault, cleans up or optionally persists
- 7 lessons covering core workflows (init, create, types, link, query, files, tracking)
- Hybrid interaction: show command, user types or presses ENTER to auto-run
- Deep state verification after each step
- Lesson selection via `--lesson N`
- Single English, no i18n

**Non-Goals:**
- Not a replacement for `--help` or man pages
- Not an in-depth type-system tutorial (custom types are beyond scope)
- Not a multi-user or web-based tutorial
- No gamification (scores, streaks, achievements)
- No rich TUI framework dependency (uses `print`/`input`)

## Decisions

### Architecture: Self-contained module

`prism-cli/prism_cli/tutor.py` owns all tutorial logic. The CLI command is a thin wrapper:

```
main.py                      tutor.py
─────────                    ────────
@cli.command()               Lessons (data)
def tutor():                  ├── Lesson dataclass
    tutor = Tutor()           ├── Step dataclass
    tutor.run()               │
                              Engine (logic)
                               ├── run_lesson()
                               ├── run_step() → prompt → verify → next
                               ├── VaultManager (temp vault lifecycle)
                               └── Verifier (state checks)
```

**Rationale**: Keeps tutorial logic separate from CLI wiring. Easy to test independently. No new files to import in main.py beyond a single `from .tutor import tutor` function.

### Lesson data model

```python
@dataclass
class Step:
    number: int
    concept: str                # Short explanation shown to user
    command: str                # The CLI command to run
    verify: Callable[[Vault], bool]  # Deep state check via library API
    warning: str = ""           # Shown if verification fails (1 retry)

@dataclass
class Lesson:
    number: int
    title: str
    concept: str                # Big-picture intro for this lesson
    steps: list[Step]
    summary: str = ""           # Shown after all steps complete
```

**Rationale**: Data-driven lessons. Adding/modifying lessons means editing a list, not control flow. `verify` callables encapsulate the state check per step.

### Interaction flow

```
show_concept()
show_command()
prompt "Type command (or ENTER to auto-run): $ "
    ↓
user_input = input()
    ↓
if user_input.strip():
    actual = user_input              # user typed it
else:
    actual = command                 # auto-run
    ↓
subprocess.run(actual, shell=True)
    ↓
if verify(vault):
    → show stdout (if non-empty)
    → ✓ next step
else:
    show warning
    prompt "Try again? [Y/n]"
    if yes: retry (same command, same verify)
    if no: skip step
```

**Rationale**: Hybrid model lets eager learners type while allowing passive learners to follow. Single retry avoids frustration spiral.

### Verification approach

Each step's `verify` function checks vault state via the library API, not CLI output:

| Step | Library check |
|------|--------------|
| `prism init` | `Vault.open(path)` succeeds, `vault.toml` exists |
| `prism new note` | `NodeManager.list_nodes()` count increased, type matches |
| `prism show` | `NodeManager.show_node()` returns expected content |
| `prism link` | `NodeMetadata.from_toml()` shows link entry |
| `prism backlinks` | `BacklinkIndex.get_backlinks()` returns source |
| `prism query` | `QueryEngine.execute()` returns expected node |
| `prism add` | `list_nodes()` has node with matching `blob_sha256` |
| `prism verify` | `StorageEngine.verify_integrity()` returns True |
| `prism status` | `ChangeTracker.status()` shows change detected |

**Rationale**: Verifying against the library (not CLI output) is more robust — it catches cases where the CLI output format changes but the underlying state is correct. Also avoids brittle string matching.

### Command output display

After verification succeeds, the command's stdout is shown to the user. This serves a pedagogical purpose — the user learns what each command's output looks like, not just that it "worked."

```
if verify(vault):
    if stdout.strip():
        show_output(stdout)        # ← teach via evidence
    show_success("Step complete!")
```

Output is printed with a `→ ` prefix to distinguish it from the tutor's own prose. If stdout is empty (e.g. `echo ... > file` is a shell redirect with no output), nothing is shown.

**Rationale**: The `vimtutor` experience teaches through direct feedback — you see the effect of every action. Hiding command output creates a black-box trust exercise. Showing it turns each step into a learning moment: the user sees "Created note node: abc123..." and internalizes that `prism new note` produces a UUID, that `prism status` reports "Vault is clean," that `prism show` reveals the full node structure.

### Temp vault lifecycle

```python
Tutor.__init__():
    self.temp_dir = tempfile.mkdtemp(prefix="prism-tutor-")
    self.vault = Vault.init(self.temp_dir / ".vault")

Tutor.cleanup():
    if keep:
        click.echo(f"Vault saved at {self.vault.path}")
    else:
        shutil.rmtree(self.temp_dir)
```

**Prompt at end**: "Tutorial complete! Keep your practice vault? [y/N]"

**Rationale**: Tempdir guarantees no pollution of user's real vaults. The keep-prompt gives beginners a souvenir of what they built.

### Edit step approach

Lesson 7 includes edit. Instead of opening `$EDITOR` (breaks flow), the tutor writes directly to `data.md`:

```
tutor writes "## Ideas\n\n- Learn Prism" to data.md
→ "I've written a quick update to your note. See what Prism noticed:"
→ $ prism status
→ "✓ The vault detected the change automatically!"
```

**Rationale**: Avoiding `$EDITOR` keeps the flow linear and predictable. The point of the edit lesson is teaching change tracking, not text editing.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| User types wrong command | Show warning + diff of what they typed vs expected; offer retry |
| User interrupts (Ctrl+C) mid-lesson | Catch KeyboardInterrupt, show "Tutorial paused. Run `prism tutor --lesson N` to resume." |
| Temp vault orphaned on crash | Use `tempfile.mkdtemp()` — OS cleans /tmp on reboot; offer `--vault-path` for explicit dir |
| `subprocess` shell injection from user input | User is running commands in their own terminal — no security boundary needed |
| Lesson drift (CLI output changes) | Verification uses library API, not output parsing; lessons only need updating if command syntax changes |
| Long lessons feel tedious | Keep each lesson to 3-4 steps; show progress indicator per lesson |
| CLI stdout format changes between releases | Shown output is informational only — verification still uses library API. Format drift is cosmetic, not functional. |

## Open Questions

(none — all decisions resolved in exploration)
