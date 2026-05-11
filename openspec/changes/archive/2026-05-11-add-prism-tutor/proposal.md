## Why

Prism has a steep onboarding curve for users new to PKM (Personal Knowledge Management). The README shows 14 commands, but there's no guided path from "never used a PKM" to "fluent Prism user." A `prism tutor` command — inspired by `vimtutor` — gives beginners a safe, interactive, step-by-step walkthrough that teaches both PKM concepts and Prism's CLI in parallel.

## What Changes

- **New `prism tutor` command** — interactive terminal tutorial for PKM beginners
- **New `prism_cli/tutor.py` module** — all tutorial logic (lessons, verification, interaction)
- **7 lessons, ~25 steps** covering: vault init, creating nodes, types, linking/graph, query/search, file import, change tracking
- **Hybrid interaction model** — shows command, user can type or press ENTER to auto-run; warns on mismatch with one retry
- **Command output displayed** — each step shows the command's stdout, so users learn what output to expect (not just that it "worked")
- **Deep state verification** — each step validates vault state via library API after running
- **Temp vault lifecycle** — creates sandbox vault in `/tmp/`, asks to keep or discard at end
- **Lesson navigation** — `prism tutor` starts at lesson 1; `prism tutor --lesson N` jumps to any lesson
- **Edit step** — tutorial writes note body directly and shows `prism status` detecting the change (avoids $EDITOR complication)
- **New `onboarding` capability spec** — captures the tutorial/interactive-learning requirements

## Capabilities

### New Capabilities
- `onboarding`: Interactive tutorial system for teaching Prism to new users via guided lessons with sandbox vault

### Modified Capabilities
(none)

## Impact

- **New module**: `prism-cli/prism_cli/tutor.py` — self-contained tutorial engine
- **CLI wiring**: one new `@cli.command()` in `prism-cli/prism_cli/main.py`
- **No new dependencies** — uses only stdlib + existing `prism` library API + `subprocess` for CLI invocations
- **Tests**: new test file `prism-core/tests/test_tutor.py` for lesson logic and verification helpers
