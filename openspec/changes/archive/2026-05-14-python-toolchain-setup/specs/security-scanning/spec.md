## ADDED Requirements

### Requirement: Source code security scanning with bandit

The system SHALL run `bandit` on all Python source files in both packages to detect common security vulnerabilities.

#### Scenario: Bandit scans prism-core source
- **WHEN** `bandit -r prism-core/prism/` is run
- **THEN** it SHALL not report any HIGH or MEDIUM severity issues

#### Scenario: Bandit scans prism-cli source
- **WHEN** `bandit -r prism-cli/prism_cli/` is run
- **THEN** it SHALL not report any HIGH or MEDIUM severity issues

### Requirement: Bandit configuration skips test assert warnings

The bandit configuration SHALL suppress `B101` (assert_used) for test files, as asserts are standard in pytest tests.

#### Scenario: Bandit ignores asserts in test files
- **WHEN** `bandit -r prism-core/tests/ prism-cli/tests/` is run
- **THEN** it SHALL not report B101 issues in test files
