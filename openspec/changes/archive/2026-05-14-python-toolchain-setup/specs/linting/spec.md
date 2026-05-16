## ADDED Requirements

### Requirement: Code quality enforced by flake8

The system SHALL run `flake8` on all Python source files in both `prism-core` and `prism-cli` packages with a maximum line length of 100.

#### Scenario: Flake8 passes on prism-core source
- **WHEN** `flake8 prism-core/prism/ --max-line-length=100` is run
- **THEN** it SHALL exit with code 0

#### Scenario: Flake8 passes on prism-core tests
- **WHEN** `flake8 prism-core/tests/ --max-line-length=100` is run
- **THEN** it SHALL exit with code 0

#### Scenario: Flake8 passes on prism-cli source
- **WHEN** `flake8 prism-cli/prism_cli/ --max-line-length=100` is run
- **THEN** it SHALL exit with code 0

#### Scenario: Flake8 passes on prism-cli tests
- **WHEN** `flake8 prism-cli/tests/ --max-line-length=100` is run
- **THEN** it SHALL exit with code 0

### Requirement: Code quality enforced by pylint

The system SHALL run `pylint` on all Python source files in both packages with a minimum score of 9.5/10 and no errors.

#### Scenario: Pylint passes on prism-core source
- **WHEN** `pylint prism-core/prism/ --max-line-length=100 --disable=C,R` is run
- **THEN** it SHALL exit with code 0

#### Scenario: Pylint passes on prism-cli source
- **WHEN** `pylint prism-cli/prism_cli/ --max-line-length=100 --disable=C,R` is run
- **THEN** it SHALL exit with code 0
