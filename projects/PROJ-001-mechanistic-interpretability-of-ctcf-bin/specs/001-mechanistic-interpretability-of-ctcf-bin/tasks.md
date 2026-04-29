# Tasks: Mechanistic Interpretability of CTCF Binding-Site Selection

**Input**: Design documents from `/specs/001-ctcf-binding-interpretability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Contract tests and integration tests included per spec requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/` at repository root
- Paths shown below reflect plan.md structure - `code/`, `tests/`, `data/`, `state/`

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are generated from spec.md and plan.md.
  
  Tasks are organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/`
- [ ] T002 Initialize Python 3.11 project with PyTorch 2.1, transformers 4.36, scikit-learn 1.3, pandas 2.1, numpy 1.24 in `code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, mypy) in `code/.flake8`, `code/pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create contract schemas in `specs/001-ctcf-binding-interpretability/contracts/`
- [ ] T005 [P] Implement SequenceContext entity schema in `specs/001-ctcf-binding-interpretability/contracts/sequence_context.schema.yaml`
- [ ] T006 [P] Implement LatentFeature entity schema in `specs/001-ctcf-binding-interpretability/contracts/latent_feature.schema.yaml`
- [ ] T007 [P] Implement BindingPrediction entity schema in `specs/001-ctcf-binding-interpretability/contracts/binding_prediction.schema.yaml`
- [ ] T008 Create data manifest structure in `code/data/manifest.json`
- [ ] T009 Setup environment configuration management in `code/.env.example` and `code/config.py`
- [ ] T010 Configure error handling and logging infrastructure in `code/utils/logging.py`
- [ ] T011 [P] Setup pytest configuration in `code/pytest.ini` and `tests/conftest.py`
- [ ] T012 Create base state tracking in `state/projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load and preprocess ENCODE ChIP-seq, ATAC-seq, and histone modification data for multiple cell types with standardized output

**Independent Test**: Can be fully tested by executing the data loader script against a static subset of ENCODE data and verifying the output tensor shapes and metadata consistency without running the neural network

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Contract test for SequenceContext schema in `code/tests/contract/test_sequence_context.py`
- [ ] T014 [P] [US1] Integration test for data ingestion pipeline in `code/tests/integration/test_data_ingestion.py`
- [ ] T015 [P] [US1] Unit test for data loader with static ENCODE subset in `code/tests/unit/test_loader.py`
- [ ] T016 [P] [US1] Unit test for preprocessing padding/truncation in `code/tests/unit/test_preprocess.py`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement ENCODE data loader in `code/data/loader.py` (FR-001)
- [ ] T018 [P] [US1] Implement data normalization and alignment in `code/data/preprocess.py` (FR-001)
- [ ] T019 [US1] Implement handling for missing cell type data with warning logging in `code/data/loader.py`
- [ ] T020 [US1] Implement sequence padding/truncation to 2048bp context window in `code/data/preprocess.py`
- [ ] T021 [US1] Add validation for 10+ cell type requirement in `code/data/loader.py`
- [ ] T022 [US1] Add logging for data ingestion operations in `code/utils/logging.py`
- [ ] T023 [US1] Implement checksum recording for processed data in `code/data/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Transformer Model Training and Execution (Priority: P2)

**Goal**: Train a transformer-based sequence-context model to predict CTCF binding probability with validation metrics

**Independent Test**: Can be fully tested by training on a small dummy dataset and verifying loss convergence and validation AUC scores without applying sparse autoencoders

### Tests for User Story 2

- [ ] T024 [P] [US2] Contract test for BindingPrediction schema in `code/tests/contract/test_binding_prediction.py`
- [ ] T025 [P] [US2] Integration test for training pipeline with dummy data in `code/tests/integration/test_training_pipeline.py`
- [ ] T026 [P] [US2] Unit test for transformer model architecture in `code/tests/unit/test_transformer.py`
- [ ] T027 [P] [US2] Unit test for inference speed (<10s per kilobase) in `code/tests/unit/test_inference.py`

### Implementation for User Story 2

- [ ] T028 [P] [US2] Create transformer architecture in `code/models/transformer.py` (FR-002)
- [ ] T029 [US2] Implement training loop with loss convergence tracking in `code/training/train.py` (FR-002)
- [ ] T030 [US2] Implement inference script for binding probability predictions in `code/training/inference.py` (FR-002)
- [ ] T031 [US2] Add AUC metric calculation for validation in `code/training/train.py`
- [ ] T032 [US2] Implement checkpoint saving/loading in `code/training/train.py`
- [ ] T033 [US2] Add cross-cell-type generalization validation in `code/training/train.py`
- [ ] T034 [US2] Add random seed pinning for reproducibility in `code/training/train.py`
- [ ] T035 [US2] Integrate with User Story 1 data loader in `code/training/train.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Mechanistic Interpretation and Validation (Priority: P3)

**Goal**: Apply sparse autoencoders and feature attribution to identify latent features driving binding, validate via synthetic perturbations

**Independent Test**: Can be fully tested by loading a pre-trained model and running the SAE decomposition on a fixed set of sequences to verify feature sparsity and motif correspondence

### Tests for User Story 3

- [ ] T036 [P] [US3] Contract test for LatentFeature schema in `code/tests/contract/test_latent_feature.py`
- [ ] T037 [P] [US3] Integration test for perturbation pipeline in `code/tests/integration/test_perturbation_pipeline.py`
- [ ] T038 [P] [US3] Unit test for sparse autoencoder decomposition in `code/tests/unit/test_sae.py`
- [ ] T039 [P] [US3] Unit test for statistical significance testing in `code/tests/unit/test_significance.py`

### Implementation for User Story 3

- [ ] T040 [P] [US3] Create sparse autoencoder model in `code/models/sae.py` (FR-003)
- [ ] T041 [US3] Implement feature attribution analysis in `code/interpretation/feature_attribution.py` (FR-003)
- [ ] T042 [US3] Implement synthetic sequence generation with motif perturbations in `code/interpretation/perturbation.py` (FR-004)
- [ ] T043 [US3] Implement statistical significance testing (permutation tests, p < 0.05) in `code/validation/significance.py` (FR-005)
- [ ] T044 [US3] Implement motif correspondence validation in `code/validation/motif_analysis.py` (FR-003)
- [ ] T045 [US3] Add 3-5 interpretable latent feature extraction requirement in `code/models/sae.py`
- [ ] T046 [US3] Integrate with User Story 2 model checkpoint in `code/interpretation/feature_attribution.py`
- [ ] T047 [US3] Add perturbation effect significance testing in `code/validation/significance.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `specs/001-ctcf-binding-interpretability/quickstart.md`
- [ ] T049 Code cleanup and refactoring across `code/`
- [ ] T050 Performance optimization for training (<48 hours) in `code/training/train.py`
- [ ] T051 [P] Additional unit tests in `code/tests/unit/`
- [ ] T052 Security hardening for data access in `code/data/loader.py`
- [ ] T053 Run quickstart.md validation
- [ ] T054 Verify reproducibility on fresh GitHub Actions runner

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
# Launch all tests for User Story 1 together:
Task: "Contract test for SequenceContext schema in code/tests/contract/test_sequence_context.py"
Task: "Integration test for data ingestion pipeline in code/tests/integration/test_data_ingestion.py"
Task: "Unit test for data loader with static ENCODE subset in code/tests/unit/test_loader.py"
Task: "Unit test for preprocessing padding/truncation in code/tests/unit/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement ENCODE data loader in code/data/loader.py"
Task: "Implement data normalization and alignment in code/data/preprocess.py"
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
   - Developer A: User Story 1 (data pipeline)
   - Developer B: User Story 2 (model training)
   - Developer C: User Story 3 (interpretability)
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
- All artifacts carry content hash per VI. Versioning Discipline
- FR-006 threshold (p < 0.05) set by default per spec resolution
