# Tasks: Mindfulness and Social Skills in Children with ASD

**Input**: Design documents from `/specs/psychology-20250704-001/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included per `plan.md` technical context (pytest, jsonschema validators).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Research Data**: `data/raw/`, `data/processed/`
- **Contracts**: `contracts/` (YAML schemas)
- **Docs**: `docs/` (IRB, protocol, analysis plan)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (root `src/`, `tests/`, `data/`, `docs/`, `contracts/`)
- [X] T002 Initialize Python 3.11 project with pydantic, pandas, scipy, pingouin dependencies
- [X] T003 [P] Configure linting and formatting tools (black, flake8, isort) in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Finalize Intervention Protocol Details (resolve 8 vs 12 session conflict) in `docs/protocol.md`
- [X] T005 [P] Create `contracts/participant.schema.yaml` defining participant demographics and consent data
- [X] T006 [P] Create `contracts/assessment.schema.yaml` defining outcome measures and timepoints
- [X] T007 [P] Create `contracts/intervention.schema.yaml` defining session logs and adherence metrics
- [X] T008 Implement Pydantic models in `src/models/data_models.py` reflecting contracts
- [X] T009 Implement validation utilities in `src/lib/validators.py` for schema compliance checks
- [X] T010 Configure environment configuration management for IRB-protected paths in `.env.example`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection & Validation (Priority: P1) 🎯 MVP

**Goal**: Enable safe, schema-compliant data entry for the 60 participants across 3 timepoints

**Independent Test**: Validation rejects malformed data and accepts valid JSON/CSV inputs

### Tests for User Story 1 (Required) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for `src/lib/validators.py` in `tests/unit/test_validators.py`
- [X] T012 [P] [US1] Contract test for participant schema in `tests/contract/test_participant_schema.py`
- [X] T013 [P] [US1] Contract test for assessment schema in `tests/contract/test_assessment_schema.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Create data collector interface in `src/services/data_collector.py`
- [X] T015 [P] [US1] Implement raw data storage logic in `data/raw/` with HIPAA-compliant naming
- [X] T016 [US1] Add validation and error handling for data ingestion pipeline
- [X] T017 [US1] Add logging for data collection operations in `src/services/data_collector.py`

**Checkpoint**: At this point, Data Collection should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Process collected data and generate RCT statistical results (pre/post/follow-up)

**Independent Test**: Analysis script produces expected output on synthetic dataset

### Tests for User Story 2 (Required) ⚠️

- [X] T018 [P] [US2] Integration test for analysis pipeline in `tests/integration/test_analysis_pipeline.py`
- [X] T019 [P] [US2] Unit test for statistical routines in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Create analysis service in `src/services/analysis.py`
- [X] T021 [US2] Implement statistical routines (t-tests, ANOVA for RCT) using scipy/pingouin
- [X] T022 [US2] Implement report generation (Markdown/PDF) in `docs/analysis-plan.md`
- [X] T023 [US2] Integrate with User Story 1 components (load processed data from `data/processed/`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compliance & Documentation (Priority: P3)

**Goal**: Generate IRB-ready documentation and verify research citations

**Independent Test**: Docs validate against IRB checklist requirements

### Tests for User Story 3 (Optional) ⚠️

- [X] T024 [P] [US3] Validation test for consent form templates in `tests/unit/test_docs.py`

### Implementation for User Story 3

- [X] T025 [P] [US3] Create protocol documentation in `docs/protocol.md`
- [X] T026 [P] [US3] Generate consent form templates in `docs/consent-forms/` (Parent/Child)
- [X] T027 [US3] Verify and update research citations (resolve `[UNVERIFIED]` flags) in `spec.md` <!-- ATOMIZE: requested -->
- [X] T028 [US3] Finalize analysis plan document in `docs/analysis-plan.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Create CLI interface for researchers in `src/cli/cli.py`
- [ ] T030 Code cleanup and refactoring across `src/`
- [ ] T031 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T032 Run quickstart.md validation to ensure reproducibility
- [ ] T033 Security hardening for data access permissions in `data/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005-T007) can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for validators in tests/unit/test_validators.py"
Task: "Contract test for participant schema in tests/contract/test_participant_schema.py"

# Launch all implementation for User Story 1 together:
Task: "Create data collector interface in src/services/data_collector.py"
Task: "Implement raw data storage logic in data/raw/ with HIPAA-compliant naming"
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
   - Developer A: User Story 1 (Data Collection)
   - Developer B: User Story 2 (Analysis)
   - Developer C: User Story 3 (Docs/Compliance)
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
- **Critical**: Resolve session count conflict (8 vs 12) in T004 before schema design
