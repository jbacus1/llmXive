---

description: "Task list template for feature implementation"
---

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

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-002-evolutionary-pressure-on-alternative-spl/`
- [ ] T002 Initialize Python 3.11 project with requirements.txt in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.ruff.toml` and `code/.black.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup environment configuration management in `code/src/utils/config.py`
- [ ] T005 [P] Implement checksum utilities for data hygiene in `code/src/utils/checksum.py`
- [ ] T006 [P] Setup logging infrastructure in `code/src/utils/logging.py`
- [ ] T007 Create base data models for RNA-seq Sample in `code/src/models/rna_sample.py`
- [ ] T008 Create base data models for Splice Junction in `code/src/models/splice_junction.py`
- [ ] T009 Create base data models for Differential Splicing Event in `code/src/models/differential_event.py`
- [ ] T010 Create base data models for Regulatory Region in `code/src/models/regulatory_region.py`
- [ ] T011 Setup SQLite metadata storage schema in `code/src/storage/metadata_db.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Acquire matched RNA-seq data from cortex tissue for human, chimpanzee, macaque, and marmoset from public repositories and align raw reads to respective reference genomes using STAR

**Independent Test**: Can be fully tested by successfully downloading and aligning RNA-seq reads from one species and producing aligned BAM files with acceptable mapping rates

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Contract test for SRA downloader in `code/tests/contract/test_sra_downloader.py`
- [ ] T013 [P] [US1] Integration test for alignment pipeline in `code/tests/integration/test_alignment_pipeline.py`
- [ ] T014 [P] [US1] Unit test for metadata parser in `code/tests/unit/test_metadata_parser.py`

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement SRA downloader in `code/src/acquisition/sra_downloader.py`
- [ ] T016 [P] [US1] Implement metadata parser for sample information in `code/src/acquisition/metadata_parser.py`
- [ ] T017 [US1] Implement STAR alignment runner in `code/src/alignment/star_runner.py`
- [ ] T018 [US1] Implement alignment quality control metrics in `code/src/alignment/quality_control.py`
- [ ] T019 [US1] Add validation for mapping rate thresholds (≥70% per SC-001) in `code/src/alignment/quality_control.py`
- [ ] T020 [US1] Add checksum verification for downloaded FASTQ files in `code/src/acquisition/sra_downloader.py`
- [ ] T021 [US1] Add logging for acquisition and alignment operations in `code/src/acquisition/sra_downloader.py` and `code/src/alignment/star_runner.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Splicing Quantification and Differential Analysis (Priority: P2)

**Goal**: Quantify splice junction usage and PSI values, then identify differentially spliced events between lineages using a fixed effect model

**Independent Test**: Can be fully tested by running splicing quantification on a subset of data and producing PSI values and differential splicing calls that can be validated against known benchmarks

### Tests for User Story 2

- [ ] T022 [P] [US2] Contract test for PSI calculator in `code/tests/contract/test_psi_calculator.py`
- [ ] T023 [P] [US2] Integration test for differential splicing analysis in `code/tests/integration/test_differential_splicing.py`
- [ ] T024 [P] [US2] Unit test for rMATS wrapper in `code/tests/unit/test_rmats_wrapper.py`

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement rMATS wrapper in `code/src/quantification/rmats_wrapper.py`
- [ ] T026 [P] [US2] Implement PSI value calculator in `code/src/quantification/psi_calculator.py`
- [ ] T027 [US2] Implement differential splicing analysis with fixed effect model in `code/src/analysis/differential_splicing.py`
- [ ] T028 [US2] Add Benjamini-Hochberg FDR correction for multiple hypothesis testing in `code/src/analysis/differential_splicing.py`
- [ ] T029 [US2] Add validation for ΔPSI threshold (≥0.1) in `code/src/analysis/differential_splicing.py`
- [ ] T030 [US2] Add validation for minimum read coverage (≥20 reads per junction) in `code/src/analysis/differential_splicing.py`
- [ ] T031 [US2] Add validation for FDR-corrected p-value threshold (<0.05) in `code/src/analysis/differential_splicing.py`
- [ ] T032 [US2] Integrate with User Story 1 alignment outputs in `code/src/quantification/rmats_wrapper.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evolutionary Selection Analysis and Validation (Priority: P3)

**Goal**: Extract flanking intronic sequences, calculate evolutionary conservation and selection metrics, perform enrichment analysis, and validate key findings using orthogonal datasets

**Independent Test**: Can be fully tested by running enrichment analysis on a subset of identified splicing events and producing selection metric calculations that can be compared to known positive selection regions

### Tests for User Story 3

- [ ] T033 [P] [US3] Contract test for phyloP extractor in `code/tests/contract/test_phylo_extractor.py`
- [ ] T034 [P] [US3] Integration test for enrichment analysis in `code/tests/integration/test_enrichment_analysis.py`
- [ ] T035 [P] [US3] Unit test for phyloP conservation score calculator in `code/tests/unit/test_phylo_p_calculator.py`

### Implementation for User Story 3

- [ ] T036 [P] [US3] Implement flanking intronic sequence extractor (±500bp) in `code/src/analysis/phylo_extractor.py`
- [ ] T037 [P] [US3] Implement phyloP conservation score calculator in `code/src/analysis/phylo_p_calculator.py`
- [ ] T038 [US3] Implement enrichment analysis with Benjamini-Hochberg FDR correction in `code/src/analysis/enrichment_test.py`
- [ ] T039 [US3] Add validation for FDR-corrected p-value threshold (<0.05 per SC-003) in `code/src/analysis/enrichment_test.py`
- [ ] T040 [US3] Implement orthology mapping via Ensembl Compara in `code/src/utils/orthology_mapper.py`
- [ ] T041 [US3] Add support for handling missing phyloP scores in `code/src/analysis/phylo_p_calculator.py`
- [ ] T042 [US3] Integrate with User Story 2 differential splicing outputs in `code/src/analysis/enrichment_test.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `code/src/README.md` and `docs/`
- [ ] T044 Code cleanup and refactoring across all modules
- [ ] T045 Performance optimization for alignment throughput (>10M reads/min per plan.md)
- [ ] T046 [P] Additional unit tests in `code/tests/unit/`
- [ ] T047 Security hardening for data access in `code/src/acquisition/`
- [ ] T048 Run quickstart.md validation in `specs/001-evolutionary-pressure-alternative-splicing/quickstart.md`
- [ ] T049 Verify reproducibility with random seed configuration in `code/src/utils/config.py`
- [ ] T050 Verify all data checksums are SHA-256 per Constitution Principle III

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

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
Task: "Integration test for alignment pipeline in code/tests/integration/test_alignment_pipeline.py"
Task: "Unit test for metadata parser in code/tests/unit/test_metadata_parser.py"

# Launch all models for User Story 1 together:
Task: "Create base data models for RNA-seq Sample in code/src/models/rna_sample.py"
Task: "Implement SRA downloader in code/src/acquisition/sra_downloader.py"
Task: "Implement metadata parser for sample information in code/src/acquisition/metadata_parser.py"
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
- Ensure all Constitution principles are satisfied (Reproducibility, Verified Accuracy, Data Hygiene, Single Source of Truth, Versioning, Cross-Species Data Harmonization, Phylogenetic Statistical Independence)
- Document all genome versions in `data/metadata.yaml` per Constitution Principle VI
- Apply phylogenetic correction in statistical models per Constitution Principle VII
