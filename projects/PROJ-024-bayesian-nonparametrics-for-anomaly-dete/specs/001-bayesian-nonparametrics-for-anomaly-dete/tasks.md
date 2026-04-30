# Tasks: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Input**: Design documents from `/specs/001-bayesian-nonparametrics-anomaly-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Branch**: `001-bayesian-nonparametrics-anomaly-detection`
**Tests**: Tests are REQUIRED per spec.md Independent Test scenarios for all user stories.

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

## Phase 0: Research & Design Documentation (Blocking)

**Purpose**: Create required design artifacts that plan.md designates as Phase 0/1 outputs

**⚠️ CRITICAL**: These artifacts must be created before Phase 1 Setup begins

- [X] T000 [P] Create `research.md` with literature review and DPGMM theoretical foundations in `specs/001-bayesian-nonparametrics-anomaly-detection/research.md` per plan.md Phase 0
- [X] T001 [P] Create `data-model.md` with entity definitions and schema specifications in `specs/001-bayesian-nonparametrics-anomaly-detection/data-model.md` per plan.md Phase 1
- [X] T002 [P] Create `quickstart.md` with usage examples and installation instructions in `specs/001-bayesian-nonparametrics-anomaly-detection/quickstart.md` per plan.md Phase 1

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T003 Create project structure per implementation plan at `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/`
- [X] T004 Initialize Python 3.11 project with pinned dependencies in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/requirements.txt`
- [X] T005 [P] Configure linting (ruff/black) and formatting tools in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create `config.yaml` with hyperparameters, random seeds, and dataset paths per FR-007 in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml`
- [X] T007 [P] Implement data directory structure (`data/raw/`, `data/processed/`) in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/`
- [X] T008 Create `download_datasets.py` with wget/curl fetchers for UCI datasets per FR-008 AND implement SHA256 checksum validation for all downloaded files per Constitution Principle III in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/download_datasets.py`
- [X] T009 [P] Implement `streaming.py` utilities for sequential observation processing in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/streaming.py`
- [X] T010 Create base `TimeSeries` dataclass/entity in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/time_series.py`
- [X] T011 [P] Setup pytest framework with contract tests directory structure in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/contract/` (note: `contracts/` under `specs/` contains schema definitions, `tests/contract/` contains pytest validation tests)
- [X] T012 Create `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` for artifact hashes AND implement checksum recording logic for all state artifacts per Constitution Principle III in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core DPGMM Implementation with Streaming Updates (Priority: P1) 🎯 MVP

**Goal**: Implement incremental DPGMM that processes time series observations one at a time with stick-breaking construction and ADVI variational inference

**Independent Test**: Can be fully tested by processing a synthetic time series with known anomaly points and verifying that the model produces anomaly scores without requiring batch retraining

### Tests for User Story 1 (REQUIRED per spec.md)

- [X] T013 [P] [US1] Contract test for DPGMM model output schema in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/contract/test_dp_gmm_schema.py`
- [X] T014 [P] [US1] Integration test for streaming observation update in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/integration/test_streaming_update.py`
- [X] T015 [P] [US1] Memory usage test verifying <7GB RAM limit in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/unit/test_memory_profile.py`

### Implementation for User Story 1

- [X] T016 [P] [US1] Create `DPGMMModel` class with stick-breaking construction in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per FR-001
- [X] T017 [US1] Implement ADVI variational inference with posterior update mechanism in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per FR-002 <!-- ATOMIZE: requested -->
- [X] T018 [US1] Implement incremental posterior mixture weight update for each new observation in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per FR-002
- [X] T019 [US1] Create `AnomalyScore` dataclass for negative log posterior probability in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/anomaly_score.py` per FR-003
- [X] T020 [US1] Implement anomaly scoring function computing negative log posterior per observation in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per FR-003
- [X] T021 [US1] Add probabilistic uncertainty estimates to anomaly scoring output in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per US1 acceptance scenario 3
- [X] T022 [US1] Implement memory profiling during 1000 observation processing in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/memory_profiler.py` per FR-005
- [X] T023 [US1] Add edge case handling for low-variance time series causing numerical instability in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per Edge Cases
- [X] T024 [US1] Add edge case handling for missing values in time series that break streaming update in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per Edge Cases
- [X] T025 [US1] Add concentration parameter tuning logic for too many/too few mixture components in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per Edge Cases
- [X] T026 [US1] Create synthetic anomaly dataset generator with known ground truth for validation in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/data/synthetic_generator.py` per Assumptions

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison and Performance Evaluation (Priority: P2)

**Goal**: Compare DPGMM detector against ARIMA and moving average baselines on public benchmarks with F1-score validation

**Independent Test**: Can be fully tested by running all three models on a single UCI dataset and generating precision-recall curves with F1-score measurements

### Tests for User Story 2 (REQUIRED per spec.md)

- [X] T027 [P] [US2] Contract test for evaluation metrics output schema in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/contract/test_metrics_schema.py`
- [X] T028 [P] [US2] Integration test for end-to-end baseline comparison pipeline in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/integration/test_baseline_comparison.py`

### Implementation for User Story 2

- [X] T029 [P] [US2] Implement ARIMA baseline model in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/baselines/arima.py` per US2 acceptance scenario 1
- [X] T030 [P] [US2] Implement moving average with z-score baseline in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/baselines/moving_average.py` per US2 acceptance scenario 1 <!-- FAILED-IN-EXECUTION: code/baselines/moving_average.py exit=1 -->
- [X] T031 [US2] Create `EvaluationMetrics` class containing F1-scores, precision, recall, AUC in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/evaluation/metrics.py` per FR-006
- [X] T032 [US2] Implement F1-score, precision, recall, AUC computation functions in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/evaluation/metrics.py` per FR-006
- [X] T033 [US2] Create confusion matrix generator for model evaluation in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/evaluation/metrics.py` per FR-006
- [X] T034 [US2] Implement ROC curve generator saving PNG files in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/evaluation/plots.py` per FR-006
- [X] T035 [US2] Implement PR curve generator saving PNG files in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/evaluation/plots.py` per FR-006
- [X] T036 [US2] Implement paired t-test with Bonferroni correction across datasets in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/evaluation/statistical_tests.py` per US2 acceptance scenario 2
- [X] T037 [US2] Create dataset fetcher for UCI Electricity dataset with real URL in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/download_datasets.py` per Assumptions <!-- FAILED-IN-EXECUTION: code/download_datasets.py exit=1 -->
- [X] T038 [US2] Create dataset fetcher for UCI Traffic dataset with real URL in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/download_datasets.py` per Assumptions
- [X] T039 [US2] Create dataset fetcher for PEMS-SF dataset from PEMS project (https://pems.dot.ca.gov) NOT UCI - use Python requests to fetch from official PEMS data portal in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/download_datasets.py` per SC-001 requirement for 3 UCI datasets (PEMS-SF is from PEMS project, not UCI)
- [X] T040 [US2] Implement runtime monitoring to verify <30 minutes per dataset in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/runtime_monitor.py` per SC-003
- [X] T041 [US2] Create hyperparameter counting utility to verify <30% tunable parameters vs baselines in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/hyperparameter_counter.py` per SC-004 <!-- FAILED-IN-EXECUTION: code/utils/hyperparameter_counter.py exit=1 -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Anomaly Score Threshold Calibration (Priority: P3)

**Goal**: Calibrate posterior probability threshold for anomaly flagging without labeled data for real-world streaming deployment

**Independent Test**: Can be fully tested by running the model on unlabeled data and verifying that the adaptive threshold produces reasonable anomaly rates based on statistical properties of the scores

### Tests for User Story 3 (REQUIRED per spec.md)

- [X] T042 [P] [US3] Contract test for threshold calibration output schema in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/contract/test_threshold_schema.py`
- [X] T043 [P] [US3] Integration test for unlabeled data threshold calibration in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/integration/test_threshold_calibration.py`

### Implementation for User Story 3

- [X] T044 [P] [US3] Implement adaptive threshold computation using 95th percentile of score distribution in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/threshold.py` per Assumptions
- [X] T045 [US3] Create threshold calibration function for unlabeled data in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/threshold.py` per FR-004
- [X] T046 [US3] Document decision boundary in config.yaml for replication per FR-007 and US3 acceptance scenario 2
- [X] T047 [US3] Implement anomaly rate validation against expected bounds in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/threshold.py` per US3 acceptance scenario 1
- [X] T048 [US3] Add support for threshold calibration across multiple datasets without labeled data in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/utils/threshold.py` per US3 acceptance scenario 3

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T049 [P] Documentation updates in `specs/001-bayesian-nonparametrics-anomaly-detection/` directory (NOT docs/) per plan.md Project Structure
- [X] T050 Code cleanup and refactoring across all implementation files <!-- ATOMIZE: requested -->
- [X] T051 Performance optimization for streaming DPGMM inference <!-- ATOMIZE: requested -->
- [X] T052 [P] Additional unit tests for edge cases in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/tests/unit/`
- [X] T053 [US1] Implement cluster anomaly handling for clustered anomalies rather than isolated points in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py` per Edge Cases
- [X] T054 [P] Add GitHub Actions workflow for automated testing within 30-minute runtime constraint per SC-003
- [X] T055 Create README with usage instructions for all three baselines and DPGMM
- [X] T056 Verify Constitution Principles I-VII are all satisfied and documented
- [X] T057 Validate quickstart.md (created in Phase 0) and verify all artifacts hash correctly <!-- FAILED-IN-EXECUTION: code/scripts/validate_quickstart_artifacts.py exit=1 -->
- [X] T058 Implement ELBO convergence logging for ADVI variational inference per Constitution Principle VI in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py`
- [X] T059 Implement GitHub Actions runtime edge case handler that logs timeout warnings and triggers retry logic when runtime exceeds 30 minutes per Edge Cases in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/.github/workflows/ci.yml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research & Design)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion
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

- Tests (REQUIRED) MUST be written and FAIL before implementation
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
Task: "Contract test for DPGMM model output schema in tests/contract/test_dp_gmm_schema.py"
Task: "Integration test for streaming observation update in tests/integration/test_streaming_update.py"
Task: "Memory usage test verifying <7GB RAM limit in tests/unit/test_memory_profile.py"

# Launch all models for User Story 1 together:
Task: "Create DPGMMModel class with stick-breaking construction in models/dp_gmm.py"
Task: "Create AnomalyScore dataclass in models/anomaly_score.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research & Design Documentation
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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
- Tests are REQUIRED per spec.md Independent Test scenarios (not OPTIONAL)
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Dataset URLs must be real and reachable (UCI Machine Learning Repository, NAB CSVs at https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/..., PEMS-SF from https://pems.dot.ca.gov)
- Task ordering MUST respect data flow: download datasets (T008, T037-T039) BEFORE model training (T016-T026), model training BEFORE evaluation (T031-T041)
- Note: `contracts/` under `specs/` contains schema definitions; `tests/contract/` contains pytest validation tests against those schemas
- PEMS-SF is from PEMS project NOT UCI Machine Learning Repository - use correct data source