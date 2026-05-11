## 1. Module scaffold and CLI wiring

- [x] 1.1 Create `prism-cli/prism_cli/tutor.py` with `Tutor` class skeleton
- [x] 1.2 Add `prism tutor` command to `main.py` as a `@cli.command()` calling `tutor()` function
- [x] 1.3 Add `--lesson` / `-L` option with integer argument defaulting to 1

## 2. Data model

- [x] 2.1 Define `Step` dataclass: `number`, `concept`, `command`, `verify`, `warning`
- [x] 2.2 Define `Lesson` dataclass: `number`, `title`, `concept`, `steps`, `summary`
- [x] 2.3 Define `StepResult` enum: `SUCCESS`, `WARNING_RETRY`, `SKIP`

## 3. Vault management

- [x] 3.1 Implement `_create_temp_vault()` using `tempfile.mkdtemp` and `Vault.init`
- [x] 3.2 Implement `_cleanup(keep: bool)` — keep or `shutil.rmtree` the temp dir
- [x] 3.3 Implement `_prompt_keep_vault()` at tutorial end with y/N input

## 4. Interaction engine

- [x] 4.1 Implement `run_lesson(lesson, vault)` — prints intro, iterates steps, prints summary
- [x] 4.2 Implement `run_step(step, vault)` — show concept, show command, prompt user
- [x] 4.3 Implement `_execute_command(command_str)` — subprocess.run, capture output
- [x] 4.4 Implement hybrid input: if user types → use that; if ENTER → auto-run expected command
- [x] 4.5 Implement wrong-command handling: show warning, offer [R]etry/[S]kip
- [x] 4.6 Implement KeyboardInterrupt catch → "Tutorial paused" message
- [x] 4.7 Verify `subprocess.run` calls `prism` from the same environment (sys.executable + `-m prism_cli`)
- [x] 4.8 After verification succeeds, display `result.stdout` (if non-empty) via `_show_output()`

## 5. Verification helpers

- [x] 5.1 Implement `_verify_vault_init(vault)` — check `vault.toml` exists
- [x] 5.2 Implement `_verify_node_count(vault, expected_count, expected_type)` — list_nodes check
- [x] 5.3 Implement `_verify_node_has_tag(vault, uuid, tag)` — tag present in metadata
- [x] 5.4 Implement `_verify_link_exists(vault, source_uuid, target_uuid)` — link in metadata
- [x] 5.5 Implement `_verify_backlink(vault, target_uuid, expected_source_uuid)`
- [x] 5.6 Implement `_verify_query_result(vault, query_str, expected_uuid)`
- [x] 5.7 Implement `_verify_file_imported(vault, file_hash)` — blob_sha256 match
- [x] 5.8 Implement `_verify_blob_integrity(vault, uuid)` — verify_integrity check
- [x] 5.9 Implement `_verify_change_detected(vault)` — ChangeTracker.status non-empty

## 6. Lesson content

- [x] 6.1 Define Lesson 1 — "What's a vault?" (init, status with 3 steps)
- [x] 6.2 Define Lesson 2 — "Your first note" (new note, show, tag query with 3 steps)
- [x] 6.3 Define Lesson 3 — "Different kinds of things" (new contact, new bookmark, type query with 3 steps)
- [x] 6.4 Define Lesson 4 — "Connecting ideas" (link, backlinks, graph with 3 steps)
- [x] 6.5 Define Lesson 5 — "Finding things" (AND/OR/NOT query, full-text with 3-4 steps)
- [x] 6.6 Define Lesson 6 — "Files in the vault" (create temp file, prism add, prism verify with 3 steps)
- [x] 6.7 Define Lesson 7 — "Your vault is alive" (tutor writes body, status, final summary with 2-3 steps)
- [x] 6.8 Wire all lessons into a `LESSONS` list in the `_build_lesson_plan()` method

## 7. Output rendering

- [x] 7.1 Implement `_show_header(lesson_number, lesson_title, total_lessons)` — lesson header
- [x] 7.2 Implement `_show_concept(text)` — prints concept explanation with wrapping
- [x] 7.3 Implement `_show_command(cmd)` — prints command in a bordered box (plain ASCII)
- [x] 7.4 Implement `_show_success(message)` — success indicator
- [x] 7.5 Implement `_show_warning(message)` — warning indicator
- [x] 7.6 Implement `_show_progress(current, total)` — step indicator per lesson
- [x] 7.7 Implement `_show_final_summary()` — wrap-up text across all lessons
- [x] 7.8 Implement `_show_output(text)` — prints command stdout with `→ ` prefix

## 8. Capability spec

- [x] 8.1 Create `openspec/specs/onboarding/spec.md` with the onboarding capability spec
- [x] 8.2 Validate the spec with `openspec spec validate onboarding`

## 9. Tests

- [x] 9.1 Write tests for `Step` and `Lesson` dataclass construction
- [x] 9.2 Write tests for each `_verify_*` helper against a real temp vault
- [x] 9.3 Write tests for `_execute_command` returning correct output
- [x] 9.4 Write tests for hybrid input branching (typed vs auto-run)
- [x] 9.5 Write tests for wrong-command warning and retry/skip flow
- [x] 9.6 Write integration test: full Lesson 1 runs end-to-end in temp vault
- [x] 9.7 Write integration test: `prism tutor --lesson` correctly skips lessons
- [x] 9.8 Write integration test: cleanup — keep and discard both work
- [x] 9.9 Write tests for `_show_output()` — empty stdout shows nothing, non-empty shows prefixed output
- [x] 9.10 Run `ruff check prism/` and `mypy prism/` from prism-core/ to verify no regressions
