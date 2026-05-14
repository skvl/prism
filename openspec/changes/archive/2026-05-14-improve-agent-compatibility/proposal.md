## Why

The project has strong internal architecture but almost no structured agent-facing documentation. As more AI agents interact with this codebase (for implementation, review, and maintenance), they lack the navigation aids, conventions, and system-level context needed to work efficiently. This leads to wasted context window, inconsistent code, and repeated discovery of the same information.

## What Changes

- Restructure root `AGENTS.md` as a hub linking to per-package agent guides
- Add `prism-core/AGENTS.md` with deep module reference
- Add `prism-cli/AGENTS.md` with command reference and CLI patterns
- Add root `INDEX.md` as navigable project index
- Add `ARCHITECTURE.md` documenting system design for agent consumption
- Add docstrings to all modules, classes, and functions across both packages
- Document agent constraint: no files outside project root; use `.tmp/` for temp files

## Capabilities

### New Capabilities
- `agent-documentation`: Project-level conventions and artifacts that make the codebase navigable and actionable for AI agents

### Modified Capabilities

None. This change does not alter any functional capability — it adds documentation infrastructure.

## Impact

- Every `.py` file in `prism-core/prism/` and `prism-cli/prism_cli/` gets docstrings
- Three new markdown files at root level: `INDEX.md`, `ARCHITECTURE.md`, `prism-core/AGENTS.md`, `prism-cli/AGENTS.md`
- Root `AGENTS.md` restructured (content preserved, links added, temp-dir constraint documented)
- No runtime code changes, no dependency changes, no behavior changes
