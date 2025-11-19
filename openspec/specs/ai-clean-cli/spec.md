# ai-clean-cli Specification

## Purpose
TBD - created by archiving change add-phase-7-1-cli-analyze. Update Purpose after archive.
## Requirements
### Requirement: Phase 7.1 Analyze Command
- Phase 7.1 `/analyze` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Analyze lists findings
- **GIVEN** a repository with analyzer-detectable issues
- **WHEN** ai-clean analyze PATH is executed
- **THEN** the CLI prints each finding's ID, category, description, and location summary without creating plans

### Requirement: Phase 7.2 Plan Command
- Phase 7.2 `/plan` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Plan command creates and saves plan
- **GIVEN** an existing finding ID
- **WHEN** ai-clean plan FINDING_ID is executed
- **THEN** the CLI generates a CleanupPlan for that finding, saves it, and prints the plan details

### Requirement: Phase 7.3 Apply Command
- Phase 7.3 `/apply` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Apply runs spec and tests with git summary
- **GIVEN** a stored plan ID and configured git branches
- **WHEN** ai-clean apply PLAN_ID is executed
- **THEN** the command ensures the refactor branch, writes an openspec file, applies it, runs tests, and shows results plus diff stat

### Requirement: Phase 7.4 Clean Command
- Phase 7.4 `/clean` Command (Basic Cleanup Wrapper) deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Clean guides finding selection and plan creation
- **GIVEN** analyze results with duplicates or large structures
- **WHEN** ai-clean clean PATH runs
- **THEN** the CLI presents filtered findings, lets the user pick, builds plans, and offers to apply or store each

### Requirement: Phase 7.5 Annotate Command
- Phase 7.5 `/annotate` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Annotate surfaces docstring targets
- **GIVEN** doc analyzer findings for missing or weak docstrings
- **WHEN** ai-clean annotate PATH [--mode all] executes
- **THEN** the CLI shows targets, lets users choose scope, generates docstring plans, and can optionally apply them

### Requirement: Phase 7.6 Organize Command
- Phase 7.6 `/organize` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Organize guides small file moves
- **GIVEN** organize_candidate findings for a folder
- **WHEN** ai-clean organize PATH runs
- **THEN** the CLI lists suggestions, lets users pick, generates move plans, and offers to apply or store them

### Requirement: Phase 7.7 Cleanup Advanced Command
- Phase 7.7 `/cleanup-advanced` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Cleanup-advanced lists advisory plans
- **GIVEN** advanced_cleanup findings
- **WHEN** ai-clean cleanup-advanced PATH runs
- **THEN** the CLI shows limited suggestions, creates plans for them, and reports plan IDs without applying

### Requirement: Phase 7.8 Changes Review Command
- Phase 7.8 `/changes-review` Command deliverables MUST be completed as described in the proposal and tasks.

#### Scenario: Changes-review outputs summary and risks
- **GIVEN** a plan ID, corresponding diff, and execution result
- **WHEN** ai-clean changes-review PLAN_ID runs
- **THEN** the CLI invokes the review executor and prints summary, risks, and suggested manual checks
