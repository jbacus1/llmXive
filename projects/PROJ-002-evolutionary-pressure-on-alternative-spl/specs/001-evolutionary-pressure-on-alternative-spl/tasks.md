# Tasks: Evolutionary Pressure on Alternative Splicing in Primates

**Input**: Design documents from `/specs/001-evolutionary-pressure-alternative-splicing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-002-evolutionary-pressure-on-alternative-spl/`
- [ ] T002 Initialize Python 3.11 project with dependencies in `code/requirements.txt` and `code/setup.py`
- [ ] T003 [P] Configure linting (black, flake8) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create base configuration management in `code/src/utils/config.py`
- [ ] T005 [P] Setup checksum utility for data integrity in `code/src/utils/checksum.py`
- [ ] T006 [P] Create metadata schema and YAML parser in `code/src/acquisition/metadata_parser.py`
- [ ] T007 Setup environment configuration management with random seed pinning
- [ ] T008 Configure logging infrastructure for pipeline operations
- [ ] T009 Create data directory structure (`data/raw/`, `data/processed/`, `data/metadata.yaml`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Acquire matched RNA-seq data from cortex tissue for human, chimpanzee, macaque, and marmoset from public repositories and align raw reads to respective reference genomes using STAR

**Independent Test**: Can be fully tested by successfully downloading and aligning RNA-seq reads from one species and producing aligned BAM files with acceptable mapping rates

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for SRA downloader in `code/tests/contract/test_sra_downloader.py`
- [ ] T011 [P] [US1] Integration test for STAR alignment pipeline in `code/tests/integration/test_star_alignment.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement SRA Toolkit downloader in `code/src/acquisition/sra_downloader.py`
- [ ] T013 [P] [US1] Create RNA-seq sample entity model in `code/src/acquisition/sample.py`
- [ ] T014 [US1] Implement STAR alignment runner in `code/src/alignment/star_runner.py`
- [ ] T015 [US1] Implement quality control metrics for alignment in `code/src/alignment/quality_control.py`
- [ ] T016 [US1] Add validation for species-specific reference genomes (GRCh38, PanTro6, Mmul10, CalJac1)
- [ ] T017 [US1] Add logging for data acquisition and alignment operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Splicing Quantification and Differential Analysis (Priority: P2)

**Goal**: Quantify splice junction usage and PSI values, then identify differentially spliced events between lineages using a fixed effect model

**Independent Test**: Can be fully tested by running splicing quantification on a subset of data and producing PSI values and differential splicing calls that can be validated against known benchmarks

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for PSI calculator in `code/tests/contract/test_psi_calculator.py`
- [ ] T019 [P] [US2] Integration test for differential splicing analysis in `code/tests/integration/test_differential_splicing.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create SpliceJunction entity model in `code/src/quantification/splice_junction.py`
- [ ] T021 [P] [US2] Create DifferentialSplicingEvent entity model in `code/src/analysis/differential_splicing_event.py`
- [ ] T022 [US2] Implement rMATS wrapper in `code/src/quantification/rmats_wrapper.py`
- [ ] T023 [US2] Implement SUPPA2 wrapper as alternative in `code/src/quantification/suppa2_wrapper.py`
- [ ] T024 [US2] Implement PSI value calculator in `code/src/quantification/psi_calculator.py`
- [ ] T025 [US2] Implement fixed effect model for differential splicing in `code/src/analysis/differential_splicing.py`
- [ ] T026 [US2] Apply Benjamini-Hochberg FDR correction for multiple hypothesis testing
- [ ] T027 [US2] Enforce statistical thresholds (ΔPSI ≥ 0.1, read coverage ≥ 20, FDR < 0.05)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evolutionary Selection Analysis and Validation (Priority: P3)

**Goal**: Extract flanking intronic sequences, calculate evolutionary conservation and selection metrics, perform enrichment analysis, and validate key findings using orthogonal datasets

**Independent Test**: Can be fully tested by running enrichment analysis on a subset of identified splicing events and producing selection metric calculations that can be compared to known positive selection regions

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for phyloP extractor in `code/tests/contract/test_phylo_extractor.py`
- [ ] T029 [P] [US3] Integration test for enrichment analysis in `code/tests/integration/test_enrichment_analysis.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Create RegulatoryRegion entity model in `code/src/analysis/regulatory_region.py`
- [ ] T031 [US3] Implement flanking intronic sequence extractor (±500bp) in `code/src/analysis/phylo_extractor.py`
- [ ] T032 [US3] Implement phyloP conservation score calculator in `code/src/analysis/conservation_score.py`
- [ ] T033 [US3] Implement selection metric calculation for regulatory regions
- [ ] T034 [US3] Implement enrichment analysis with Benjamini-Hochberg correction in `code/src/analysis/enrichment_test.py`
- [ ] T035 [US3] Add validation against orthogonal datasets or independent samples
- [ ] T036 [US3] Handle edge cases: missing phyloP scores, incomplete annotations, sequence divergence issues

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `specs/001-evolutionary-pressure-alternative-splicing/`
- [ ] T038 Code cleanup and refactoring across all modules
- [ ] T039 Performance optimization for alignment throughput (> 10M reads/min target)
- [ ] T040 [P] Additional unit tests in `code/tests/unit/`
- [ ] T041 Security hardening for data access and PII scanning
- [ ] T042 Run quickstart.md validation
- [ ] T043 Verify reproducibility with fixed random seeds across all statistical models
- [ ] T044 Validate orthology mapping via Ensembl Compara for cross-species aggregation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 alignment outputs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 differential splicing outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
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
Task: "Contract test for SRA downloader in code/tests/contract/test_sra_downloader.py"
Task: "Integration test for STAR alignment pipeline in code/tests/integration/test_star_alignment.py"

# Launch all models for User Story 1 together:
Task: "Create RNA-seq sample entity model in code/src/acquisition/sample.py"
Task: "Implement SRA Toolkit downloader in code/src/acquisition/sra_downloader.py"
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
   - Developer A: User Story 1 (Data Acquisition & Alignment)
   - Developer B: User Story 2 (Splicing Quantification & Differential Analysis)
   - Developer C: User Story 3 (Evolutionary Selection Analysis)
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
- Memory constraint: < 64GB per alignment job
- Reproducibility: All statistical models must use fixed random seeds
- Data hygiene: All files under `data/` must be checksummed (SHA-256)
- External tools: STAR (v2.7.10a), rMATS (v4.1.2), SAMtools (v1.17), Bedtools (v2.31.0), SRA Toolkit (v3.0.0)
