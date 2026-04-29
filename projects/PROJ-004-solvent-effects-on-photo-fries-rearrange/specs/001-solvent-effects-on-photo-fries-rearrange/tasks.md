# Tasks: Solvent Effects on Photo-Fries Rearrangement Kinetics

**Input**: Design documents from `/specs/001-solvent-effects/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks based on acceptance scenarios from spec.md. Tests are included because the spec defines explicit acceptance criteria that require verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- **Source Code**: `code/` at project root
- **Tests**: `code/tests/`
- **Data**: `data/` (raw, compute, chemicals, processed)
- **State**: `state/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange.yaml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (code/, data/, docs/, state/)
- [ ] T002 Initialize Python 3.11 project with requirements.txt (numpy, scipy, pandas, scikit-learn, pymatgen, ase, openbabel, pyyaml, pytest)
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort)
- [ ] T004 [P] Setup pytest configuration and test directory structure in code/tests/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Setup SQLite database schema for experimental metadata (state/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange.yaml)
- [ ] T006 [P] Create base data models/entities (SolventCondition, KineticTrace, ReactionMetric) in code/models/
- [ ] T007 Configure environment configuration management for instrument and compute resources
- [ ] T008 Setup error handling and logging infrastructure for both experimental and computational workflows
- [ ] T009 [P] Initialize solvent_registry.yaml in data/chemicals/ with standard solvent properties (dielectric constants, etc.)
- [ ] T010 Setup data directory structure (raw/laser_flash_photolysis/, compute/dft_inputs/, processed/)
- [ ] T011 Implement checksum/hashing utility for data hygiene (data/ directory)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configure and Execute Solvent Series (Priority: P1) 🎯 MVP

**Goal**: Define a series of solvents ranging from non-polar to polar and initiate the experimental protocol for each condition

**Independent Test**: Configure a solvent list (e.g., cyclohexane, methanol) and verify the system logs the dielectric constant and temperature settings for each run

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Unit test for solvent configuration validation in code/tests/test_solvent_config.py
- [ ] T013 [P] [US1] Contract test for solvent properties logging in code/tests/test_solvent_config.py
- [ ] T014 [US1] Integration test for solvent series setup with instrument parameters in code/tests/test_solvent_config.py

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create SolventCondition model in code/models/solvent_condition.py (Dielectric Constant, Temperature, Volume)
- [ ] T016 [P] [US1] Create solvent configuration service in code/solvent_config.py
- [ ] T017 [US1] Implement solvent validation (ε ≈ 2 to ε ≈ 33 range, minimum 5 solvents per FR-001)
- [ ] T018 [US1] Implement instrument parameter preparation for each solvent condition
- [ ] T019 [US1] Add logging for solvent configuration and experiment initiation
- [ ] T020 [US1] Integrate with SQLite metadata storage for solvent conditions

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract Radical-Pair Lifetime (Priority: P2)

**Goal**: Process the raw spectroscopic data to extract the singlet-radical-pair intermediate lifetime via global kinetic analysis

**Independent Test**: Upload a set of decay traces and verify the system outputs a lifetime value derived from exponential fitting

### Tests for User Story 2

- [ ] T021 [P] [US2] Unit test for exponential fitting algorithm in code/tests/test_kinetic_analysis.py
- [ ] T022 [P] [US2] Contract test for lifetime extraction with confidence interval in code/tests/test_kinetic_analysis.py
- [ ] T023 [US2] Integration test for multiple replicates (n ≥ 3) mean/std calculation in code/tests/test_kinetic_analysis.py

### Implementation for User Story 2

- [ ] T024 [P] [US2] Create KineticTrace model in code/models/kinetic_trace.py (raw transient-absorption data)
- [ ] T025 [P] [US2] Create kinetic analysis service in code/kinetic_analysis.py
- [ ] T026 [US2] Implement data ingestion for raw decay traces (200–800 nm, 1 ns–10 μs per FR-002)
- [ ] T027 [US2] Implement global kinetic analysis with exponential fitting (FR-003)
- [ ] T028 [US2] Implement lifetime extraction with confidence interval calculation
- [ ] T029 [US2] Implement replicate aggregation (mean, std deviation for n ≥ 3)
- [ ] T030 [US2] Write processed lifetimes to data/processed/lifetimes.csv
- [ ] T031 [US2] Add logging for kinetic analysis operations and performance tracking (5-minute goal)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate Solvation Energy with Product Distribution (Priority: P3)

**Goal**: Correlate computed solvation free energies with the experimentally determined lifetimes and product distributions

**Independent Test**: Input solvation energy values and lifetime data, verify the system generates a regression plot and statistical significance test

### Tests for User Story 3

- [ ] T032 [P] [US3] Unit test for regression analysis (R² calculation) in code/tests/test_correlation_analysis.py
- [ ] T033 [P] [US3] Contract test for ANOVA statistical significance (p < 0.01) in code/tests/test_correlation_analysis.py
- [ ] T034 [US3] Integration test for full correlation workflow (lifetimes + solvation energies) in code/tests/test_correlation_analysis.py

### Implementation for User Story 3

- [ ] T035 [P] [US3] Create ReactionMetric model in code/models/reaction_metric.py (lifetime, product distribution)
- [ ] T036 [P] [US3] Create DFT solvation integration service in code/dft_solvation.py
- [ ] T037 [P] [US3] Create correlation analysis service in code/correlation_analysis.py
- [ ] T038 [US3] Implement DFT solvation energy ingestion (SMD/PCM implicit solvent models per FR-004)
- [ ] T039 [US3] Implement regression analysis (lifetime vs. solvation energy, R² > 0.8 per SC-001)
- [ ] T040 [US3] Implement ANOVA statistical testing across solvent conditions (FR-005, SC-003)
- [ ] T041 [US3] Generate regression plots and statistical summary outputs
- [ ] T042 [US3] Write processed solvation energies to data/processed/solvation_energies.csv
- [ ] T043 [US3] Add logging for correlation analysis operations

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in docs/ (deviation_analysis.md, chemical_provenance.md)
- [ ] T045 Code cleanup and refactoring across all modules
- [ ] T046 Performance optimization (verify kinetic analysis < 5 min, DFT < 24 hours)
- [ ] T047 [P] Additional unit tests for edge cases (solvent evaporation, photodegradation, DFT failures)
- [ ] T048 Security hardening for instrument interface and compute cluster access
- [ ] T049 Run Constitution Check re-verification (all 7 principles)
- [ ] T050 [P] Update state/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange.yaml with content hashes
- [ ] T051 Validate quickstart.md documentation for new researchers
- [ ] T052 Run end-to-end integration test with sample solvent series

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 data but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (lifetimes) and US2 (solvation energies) data for correlation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before integration
- Core implementation before logging
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for solvent configuration validation in code/tests/test_solvent_config.py"
Task: "Contract test for solvent properties logging in code/tests/test_solvent_config.py"

# Launch all models for User Story 1 together:
Task: "Create SolventCondition model in code/models/solvent_condition.py"
Task: "Create solvent configuration service in code/solvent_config.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (solvent configuration)
   - Developer B: User Story 2 (kinetic analysis)
   - Developer C: User Story 3 (correlation analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All data files must be checksummed per Constitution Principle III (Data Hygiene)
- All code must be reproducible with pinned random seeds per Constitution Principle I (Reproducibility)
