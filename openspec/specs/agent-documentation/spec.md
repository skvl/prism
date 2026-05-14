## Purpose

The agent-documentation capability provides structured guidance for AI agents working with the Prism codebase, including a root AGENTS.md navigation hub, per-package agent guides, comprehensive docstrings, a codebase index, and architecture documentation.

## Requirements

### Requirement: Root AGENTS.md as navigation hub

The root `/AGENTS.md` SHALL serve as the entry point for AI agents, containing project overview, setup instructions, agent constraints, and links to per-package agent guides.

#### Scenario: Agent reads root AGENTS.md
- **WHEN** an AI agent is first given context about the project
- **THEN** `/AGENTS.md` SHALL contain a project overview, setup commands, and links to `prism-core/AGENTS.md` and `prism-cli/AGENTS.md`
- **THEN** `/AGENTS.md` SHALL document that agents must not create files outside the project root and SHALL use `.tmp/` for temporary files

#### Scenario: Root AGENTS.md links to sub-package guides
- **WHEN** an agent navigates to `prism-core/` or `prism-cli/`
- **THEN** the root AGENTS.md SHALL reference the sub-package guide via relative path

### Requirement: Per-package agent guides

Each sub-package SHALL have its own `AGENTS.md` with details specific to that package.

#### Scenario: prism-core agent guide
- **WHEN** an agent works with files in `prism-core/prism/`
- **THEN** `prism-core/AGENTS.md` SHALL contain a module map with file-level descriptions
- **THEN** it SHALL document type system conventions, import patterns, and naming rules

#### Scenario: prism-cli agent guide
- **WHEN** an agent works with files in `prism-cli/prism_cli/`
- **THEN** `prism-cli/AGENTS.md` SHALL contain a command reference table
- **THEN** it SHALL document Click wiring patterns, REPL architecture, and tutor system

### Requirement: Module, class, and function docstrings

Every public module, class, and function in both packages SHALL have a docstring following Google-style conventions.

#### Scenario: Module-level docstring
- **WHEN** an agent reads any `.py` file in `prism-core/prism/` or `prism-cli/prism_cli/`
- **THEN** the file SHALL have a module-level docstring describing its purpose and exports

#### Scenario: Function docstring
- **WHEN** an agent reads a public function
- **THEN** the function SHALL have a docstring describing its purpose, Args, Returns, and Raises sections as applicable

#### Scenario: Class docstring
- **WHEN** an agent reads a class definition
- **THEN** the class SHALL have a docstring describing its purpose and usage

### Requirement: INDEX.md navigation index

The project root SHALL contain `INDEX.md` providing a navigable map of the entire codebase.

#### Scenario: Agent reads INDEX.md
- **WHEN** an agent needs to locate files or understand project layout
- **THEN** `INDEX.md` SHALL list every subdirectory with its contents and a brief description of each file

### Requirement: ARCHITECTURE.md system design

The project root SHALL contain `ARCHITECTURE.md` documenting the system design for agent consumption.

#### Scenario: Agent reads ARCHITECTURE.md
- **WHEN** an agent needs to understand system design
- **THEN** `ARCHITECTURE.md` SHALL contain an ASCII architecture diagram, data flow description, key design decisions, and module interaction patterns

### Requirement: Agent temp directory constraint

The project SHALL document that AI agents must not create files outside the project root directory and SHALL use `.tmp/` for any temporary files.

#### Scenario: Agent creates temporary files
- **WHEN** an agent needs to create temporary files during its work
- **THEN** the agent MUST place them in `.tmp/` within the project root
- **THEN** the agent MUST NOT create files outside the project root directory
