# Tasks: Evolutionary Pressure on Alternative Splicing in Comparative Genomics

**Input**: Design documents from `/specs/paper-evolutionary-pressure-alternative-splicing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `paper/` at repository root
- **LaTeX**: `paper/source/`, `paper/data/`, `paper/scripts/`
- Paths shown below assume single project - adjust based on plan.md structure

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic LaTeX structure

- [X] T001 [P] [Setup] Initialize LaTeX project structure per implementation plan in `paper/source/` [kind:latex-build]
- [X] T002 [P] [Setup] Create `main.tex` with arxiv-style class and required packages [kind:latex-build]
- [X] T003 [P] [Setup] Initialize `refs.bib` bibliography file scaffold in `paper/source/` [kind:reference-verification]

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data contracts and figure scripts that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] [Foundational] Create `figure-data.schema.yaml` contract in `paper/contracts/` [kind:statistics]
- [X] T005 [P] [Foundational] Create `bibliography.schema.yaml` contract in `paper/contracts/` [kind:reference-verification]
- [X] T006 [P] [Foundational] Scaffold Python scripts for Figures 1-5 in `paper/scripts/figures/` [kind:figure]
- [X] T007 [Foundational] Implement checksum verification script for `data/` artifacts per Principle III [kind:statistics]
- [X] T008 [P] [Foundational] Configure `pdflatex` build gate in CI/CD pipeline [kind:latex-build]

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducibility Verification (Priority: P1) 🎯 MVP

**Goal**: Peer reviewer can reproduce primary splicing quantification results from raw SRA data using documented pipeline and tool versions.

**Independent Test**: Reviewer can execute the pipeline script with fixed random seeds and generate identical alignment statistics (STAR throughput > 10M reads/min) and rMATS splicing event counts within acceptable variance.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for pipeline checksums in `tests/contract/test_checksums.py` [kind:statistics]
- [X] T010 [P] [US1] Integration test for pipeline reproducibility in `tests/integration/test_repro.py` [kind:statistics]

### Implementation for User Story 1

- [X] T011 [P] [US1] Draft Methods section - Pipeline description (STAR/rMATS) in `paper/source/sections/methods.tex` [kind:prose]
- [X] T012 [P] [US1] Document tool versions (STAR v2.7.10a, rMATS v4.1.2) in `paper/source/sections/methods.tex` [kind:prose]
- [X] T013 [US1] Document random seeds used for pipeline reproducibility in `paper/source/sections/methods.tex` [kind:prose]
- [X] T014 [US1] Generate alignment statistics checksums for `data/` artifacts [kind:statistics]
- [X] T015 [US1] Verify alignment throughput > 10M reads/min constraint in pipeline logs [kind:statistics]

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Methods Transparency (Priority: P1)

**Goal**: A student with basic bioinformatics knowledge can follow the Methods section without requiring prior context about the project setup.

**Independent Test**: Student can independently identify all tool versions, data sources, and processing steps from the Methods section alone.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Validation test for tool version consistency in `tests/contract/test_versions.py` [kind:statistics]

### Implementation for User Story 2

- [X] T017 [P] [US2] Draft Methods section - Orthology mapping approach (Ensembl Compara) in `paper/source/sections/methods.tex` [kind:prose]
- [X] T018 [US2] Document end-to-end pipeline completion constraint (< 48h) in `paper/source/sections/methods.tex` [kind:prose]
- [X] T019 [US2] Verify tool versions in Methods match `paper/requirements.txt` [kind:reference-verification]
- [X] T020 [US2] Verify memory constraints (< 64GB per alignment job) documented in Methods [kind:prose]

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Claims Verification (Priority: P2)

**Goal**: A reviewer can locate every cited fact and verify each inferential claim about evolutionary pressure on alternative splicing against the supporting data.

**Independent Test**: Reviewer can trace each claim in the Results/Discussion to a specific figure and underlying data file.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US3] Traceability test for Claim 1 to Figure 4 in `tests/contract/test_claims.py` [kind:statistics]
- [X] T022 [P] [US3] Traceability test for Claim 2 to Figure 3/5 in `tests/contract/test_claims.py` [kind:statistics]

### Implementation for User Story 3

- [X] T023 [P] [US3] Draft Results section - Differential splicing analysis across species in `paper/source/sections/results.tex` [kind:prose]
- [X] T024 [P] [US3] Generate Figure 4 (Comparative splicing conservation heatmap) at `paper/source/figures/fig4.pdf` [kind:figure]
- [X] T025 [US3] Generate Figure 5 (Differential splicing events with statistical significance) at `paper/source/figures/fig5.pdf` [kind:figure]
- [X] T026 [US3] Verify Claim 1 (Conservation across orthologous genes) traces to Figure 4 data [kind:statistics]
- [X] T027 [US3] Verify Claim 2 (Event types evolutionary pressure) traces to Figure 3/5 data [kind:statistics]
- [X] T028 [US3] Verify statistical claims in Results computed on checksummed artifacts per Principle III [kind:statistics]
- [X] T029 [P] [US3] Verify citations for prior splicing studies in References section [kind:reference-verification]

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Comparative Analysis Clarity (Priority: P2)

**Goal**: A follow-up researcher can understand the comparative framework between species used to assess evolutionary pressure.

**Independent Test**: Researcher can identify which species were compared, what splicing event types were analyzed, and how orthology was established.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US4] Validation test for species pair identification in `tests/contract/test_species.py` [kind:prose]

### Implementation for User Story 4

- [X] T031 [P] [US4] Draft Results section - Species comparison framework in `paper/source/sections/results.tex` [kind:prose]
- [X] T032 [US4] Document rMATS event types included (exon skipping, mutually exclusive, etc.) in Methods [kind:prose]
- [X] T033 [US4] Draft Discussion section - Evolutionary pressure interpretation vs observed differences [kind:prose]
- [X] T034 [P] [US4] Perform lit-search for evolutionary pressure background in Introduction [kind:lit-search]
- [X] T035 [US4] Verify orthology mapping coverage percentage documented in Discussion [kind:statistics]

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: User Story 5 - Supplementary Materials Completeness (Priority: P3)

**Goal**: A student can access all supplementary tables and figures needed to understand the full scope of the analysis.

**Independent Test**: Student can locate and understand all supplementary materials referenced in the main text.

### Tests for User Story 5 (OPTIONAL - only if tests requested) ⚠️

- [X] T036 [P] [US5] Validation test for supplementary file references in `tests/contract/test_supplementary.py` [kind:prose]

### Implementation for User Story 5

- [X] T037 [P] [US5] Generate Supplementary Table of splicing events in `paper/source/supplementary/` [kind:statistics]
- [X] T038 [US5] Generate Supplementary Figures referenced in main text [kind:figure]
- [X] T039 [US5] Verify supplementary material data sources match `data/` directory checksums [kind:statistics]
- [X] T040 [US5] Verify tool version documentation in Supplementary Materials matches `requirements.txt` [kind:reference-verification]

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] [Polish] Proofread Abstract, Introduction, and Discussion for clarity and jargon discipline [kind:proofread]
- [X] T042 [P] [Polish] Run `pdflatex` build gate and verify no warnings in log [kind:latex-build]
- [X] T043 [Polish] Fix any LaTeX compilation errors encountered during build [kind:latex-fix]
- [X] T044 [P] [Polish] Verify all 5 required figures present with captions referencing `data/` files [kind:figure]
- [X] T045 [P] [Polish] Verify all 5 required claims traceable to evidence in paper [kind:prose]
- [X] T046 [P] [Polish] Run `check_figures.py` (checksum verification) [kind:statistics]

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (Data contracts before Figure scripts)
- Services before endpoints (Figure scripts before LaTeX inclusion)
- Core implementation before integration
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
Task: "Contract test for pipeline checksums in tests/contract/test_checksums.py"
Task: "Integration test for pipeline reproducibility in tests/integration/test_repro.py"

# Launch all models for User Story 1 together:
Task: "Draft Methods section - Pipeline description (STAR/rMATS) in paper/source/sections/methods.tex"
Task: "Document tool versions (STAR v2.7.10a, rMATS v4.1.2) in paper/source/sections/methods.tex"
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
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
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
- **CRITICAL**: Every task line MUST include a `[kind:<value>]` token for dispatcher routing.
