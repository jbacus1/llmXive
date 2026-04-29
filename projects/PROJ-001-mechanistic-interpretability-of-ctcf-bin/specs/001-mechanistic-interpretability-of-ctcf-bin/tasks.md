# Tasks: Mechanistic Interpretability of CTCF Binding-Site Selection

**Input**: Design documents from `/specs/001-ctcf-binding-interpretability/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/`)
- [ ] T002 Initialize Python 3.11 project with PyTorch 2.1, transformers 4.36, scikit-learn 1.3, pandas 2.1, numpy 1.24 dependencies
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort)
- [ ] T004 [P] Setup pytest 7.4 testing framework in tests/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Setup environment configuration management (state/projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin.yaml)
- [ ] T006 [P] Create data manifest.json schema for ENCODE accession tracking and checksums
- [ ] T007 [P] Create contract test schemas in contracts/ (sequence_context.schema.yaml, latent_feature.schema.yaml, binding_prediction.schema.yaml)
- [ ] T008 [P] Setup data/processed/ directory structure with checksum verification
- [ ] T009 Create base SequenceContext entity model in code/models/sequence_context.py
- [ ] T010 [P] Create base LatentFeature entity model in code/models/latent_feature.py
- [ ] T011 [P] Create base BindingPrediction entity model in code/models/binding_prediction.py
- [ ] T012 Configure random seed pinning for reproducibility (Constitution Principle I)
- [ ] T013 Setup logging infrastructure with ENCODE accessions tracking
- [ ] T014 Implement error handling for missing cell type data (US1 edge case)
- [ ] T015 Implement sequence padding/truncation to 2048bp context window

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load and preprocess ENCODE ChIP-seq, ATAC-seq, and histone modification data for multiple cell types into standardized datasets ready for model training

**Independent Test**: Can be fully tested by executing the data loader script against a static subset of ENCODE data and verifying the output tensor shapes and metadata consistency without running the neural network

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Contract test for SequenceContext schema in tests/contract/test_sequence_context.py
- [ ] T017 [P] [US1] Unit test for ENCODE data loader in tests/unit/test_loader.py
- [ ] T018 [P] [US1] Unit test for preprocessing normalization in tests/unit/test_preprocess.py
- [ ] T019 [P] [US1] Integration test for full data pipeline in tests/integration/test_data_pipeline.py

### Implementation for User Story 1

- [ ] T020 [P] [US1] Implement ENCODE data ingestion in code/data/loader.py (FR-001)
- [ ] T021 [P] [US1] Implement data normalization and alignment in code/data/preprocess.py (FR-001)
- [ ] T022 [US1] Implement multi-cell-type support for 10+ cell types (FR-001)
- [ ] T023 [US1] Implement warning logging for missing cell type data (edge case handling)
- [ ] T024 [US1] Implement sequence alignment to common genomic coordinate system
- [ ] T025 [US1] Add validation for 1M+ sequence contexts loading
- [ ] T026 [US1] Add metadata consistency checks for tensor outputs
- [ ] T027 [US1] Document data preprocessing pipeline in quickstart.md

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Transformer Model Training and Execution (Priority: P2)

**Goal**: Train a transformer-based sequence-context model to predict CTCF binding probability

**Independent Test**: Can be fully tested by training on a small dummy dataset and verifying loss convergence and validation AUC scores without applying sparse autoencoders

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US2] Contract test for BindingPrediction schema in tests/contract/test_binding_prediction.py
- [ ] T029 [P] [US2] Unit test for transformer model in tests/unit/test_transformer.py
- [ ] T030 [P] [US2] Unit test for training loop in tests/unit/test_training.py
- [ ] T031 [P] [US2] Integration test for model training and inference in tests/integration/test_training_pipeline.py

### Implementation for User Story 2

- [ ] T032 [P] [US2] Implement transformer architecture in code/models/transformer.py (FR-002)
- [ ] T033 [US2] Implement model training loop in code/training/train.py (FR-002)
- [ ] T034 [US2] Implement inference script in code/training/inference.py (FR-002)
- [ ] T035 [US2] Implement loss convergence monitoring (threshold < defined value within 100 epochs)
- [ ] T036 [US2] Implement AUC > 0.85 validation on held-out cell types (SC-001)
- [ ] T037 [US2] Implement checkpoint saving and loading
- [ ] T038 [US2] Implement performance monitoring (inference < 10 seconds per kilobase)
- [ ] T039 [US2] Handle model convergence failure edge case (loss increases indefinitely)
- [ ] T040 [US2] Add GPU memory optimization for < 200GB constraint
- [ ] T041 [US2] Document model training pipeline in quickstart.md

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Mechanistic Interpretation and Validation (Priority: P3)

**Goal**: Apply sparse autoencoders and feature attribution to identify latent features driving binding, validate via synthetic perturbations

**Independent Test**: Can be fully tested by loading a pre-trained model and running the SAE decomposition on a fixed set of sequences to verify feature sparsity and motif correspondence

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T042 [P] [US3] Contract test for LatentFeature schema in tests/contract/test_latent_feature.py
- [ ] T043 [P] [US3] Unit test for sparse autoencoder in tests/unit/test_sae.py
- [ ] T044 [P] [US3] Unit test for feature attribution in tests/unit/test_feature_attribution.py
- [ ] T045 [P] [US3] Unit test for statistical significance testing in tests/unit/test_significance.py
- [ ] T046 [P] [US3] Integration test for perturbation experiments in tests/integration/test_perturbation_pipeline.py

### Implementation for User Story 3

- [ ] T047 [P] [US3] Implement sparse autoencoder in code/models/sae.py (FR-003)
- [ ] T048 [US3] Implement feature attribution analysis in code/interpretation/feature_attribution.py (FR-003)
- [ ] T049 [US3] Implement synthetic perturbation generation in code/interpretation/perturbation.py (FR-004)
- [ ] T050 [US3] Implement statistical significance testing in code/validation/significance.py (FR-005)
- [ ] T051 [US3] Implement motif correspondence analysis in code/validation/motif_analysis.py (FR-003)
- [ ] T052 [US3] Extract 3-5 interpretable latent features (SC-002)
- [ ] T053 [US3] Implement permutation tests for feature contributions
- [ ] T054 [US3] Implement p-value threshold configuration (FR-006 - default p < 0.05)
- [ ] T055 [US3] Validate synthetic perturbation correlation > 90% (SC-003)
- [ ] T056 [US3] Handle SAE features not corresponding to known motifs edge case
- [ ] T057 [US3] Integrate with CRISPRi perturbation datasets for external validation
- [ ] T058 [US3] Document interpretability pipeline in quickstart.md

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T059 [P] Documentation updates in docs/
- [ ] T060 Code cleanup and refactoring across all modules
- [ ] T061 Performance optimization across all stories
- [ ] T062 [P] Additional unit tests in tests/unit/
- [ ] T063 Security hardening for data access
- [ ] T064 Run quickstart.md validation
- [ ] T065 Verify Constitution Principles compliance (all 6 principles)
- [ ] T066 Update state/ artifact_hashes on all changes
- [ ] T067 Validate reproducibility on fresh GitHub Actions runner
- [ ] T068 Cross-validate figures/statistics trace to data rows (Principle IV)

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for SequenceContext schema in tests/contract/test_sequence_context.py"
Task: "Unit test for ENCODE data loader in tests/unit/test_loader.py"
Task: "Unit test for preprocessing normalization in tests/unit/test_preprocess.py"
Task: "Integration test for full data pipeline in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement ENCODE data ingestion in code/data/loader.py (FR-001)"
Task: "Implement data normalization and alignment in code/data/preprocess.py (FR-001)"
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
- All data files under data/ must be checksummed per Constitution Principle III
- All artifacts carry content hash per Constitution Principle V
