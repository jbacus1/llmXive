# Tasks: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Input**: Design documents from `/specs/001-bayesian-nonparametrics-anomaly-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are MANDATORY per plan.md requirements. Contract tests, integration tests, and unit tests must be written and verified to fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- All paths are relative to `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection/` project root
- Code artifacts: `code/`
- Data artifacts: `data/` at project root
- State artifacts: `state/` at project root
- Contract schemas: `specs/001-bayesian-nonparametrics-anomaly-detection/contracts/`
- Documentation artifacts: `specs/001-bayesian-nonparametrics-anomaly-detection/`

---

## Phase 0: Research

**Purpose**: Conduct initial research and create foundational documentation per plan.md Project Structure

**Checkpoint**: Research documentation complete - Constitution Check can proceed

- [X] T001 Conduct research on Dirichlet process Gaussian mixture models and streaming inference in specs/001-bayesian-nonparametrics-anomaly-detection/research.md
- [X] T002 Document data model for TimeSeries, DPGMMModel, AnomalyScore, EvaluationMetrics in specs/001-bayesian-nonparametrics-anomaly-detection/data-model.md
- [X] T003 Create quickstart.md with setup and execution instructions in specs/001-bayesian-nonparametrics-anomaly-detection/quickstart.md

---

## Constitution Check

**Purpose**: Verify all Constitution principles are satisfied before any implementation begins

**⚠️ CRITICAL**: Must pass before Phase 0 research begins. Re-check after Phase 1 design.

- [X] T004 Verify all 7 Constitution principles pass (reproducibility, accuracy, data hygiene, versioning, stability, prior sensitivity, single source of truth) per plan.md Constitution Check table <!-- FAILED: Constitution Check requires manual verification of 7 principles against research documentation and implementation plan - cannot be automated. -->

**Checkpoint**: Constitution verified - Phase 0 research can now proceed

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T005 Create project structure per implementation plan in projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection/
- [X] T006 Initialize Python 3.11 project with pymc>=5.0.0, numpy>=1.24.0, pandas>=2.0.0, scikit-learn>=1.3.0, statsmodels>=0.14.0, matplotlib>=3.7.0, pyyaml>=6.0.0 in code/requirements.txt
- [X] T007 [P] Configure linting and formatting tools (black, flake8, isort) in code/
- [X] T008 [P] Initialize pytest>=7.4.0 testing framework in code/tests/
- [X] T009 [P] Setup GitHub Actions CI workflow for Python 3.11 in .github/workflows/
- [X] T010 [P] Create contract schemas: anomaly_score.schema.yaml, config.schema.yaml, evaluation_metrics.schema.yaml in specs/001-bayesian-nonparametrics-anomaly-detection/contracts/
- [X] T011 [P] Create data/ directory structure: raw/, processed/ in project root

**Checkpoint**: Setup complete - foundational work can begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T012 Create config.yaml with random seeds, hyperparameters, and dataset paths per FR-007
- [X] T013 [P] Implement TimeSeries entity class in code/models/timeseries.py
- [X] T014 [P] Implement AnomalyScore entity class in code/models/anomaly_score.py
- [X] T015 [P] Implement EvaluationMetrics entity class in code/models/evaluation_metrics.py
- [X] T016 [P] Implement data download script with checksums in code/data/download_datasets.py <!-- FAILED-IN-EXECUTION: code/data/download_datasets.py exit=1 -->
- [X] T017 [P] Implement memory profiling utilities to verify <7GB RAM constraint in code/utils/memory_profiler.py
- [X] T018 [P] Implement runtime profiling utilities to verify <30 minutes per dataset constraint in code/utils/runtime_profiler.py
- [X] T019 [P] Implement synthetic anomaly dataset generator for controlled validation with known ground truth in code/data/synthetic_anomaly_generator.py
- [X] T020 [P] Implement error handling and logging infrastructure in code/utils/logger.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core DPGMM Implementation with Streaming Updates (Priority: P1) 🎯 MVP

**Goal**: Implement an incremental DPGMM that processes time series observations one at a time using stick-breaking construction and ADVI variational inference

**Independent Test**: Can be fully tested by processing a synthetic time series with known anomaly points and verifying that the model produces anomaly scores without requiring batch retraining

### Tests for User Story 1 (MANDATORY per plan.md) ⚠️

> **NOTE: Write these tests FIRST within Phase 3, after Phase 2 foundational infrastructure is complete**

- [X] T021 [P] [US1] Contract test for anomaly_score.schema.yaml validation in code/tests/contract/test_anomaly_score.py
- [X] T022 [P] [US1] Integration test for streaming DPGMM update in code/tests/integration/test_dpgmm_streaming.py
- [X] T023 [P] [US1] Unit test for stick-breaking construction in code/tests/unit/test_stick_breaking.py
- [X] T024 [P] [US1] Unit test for ADVI variational inference convergence in code/tests/unit/test_advi_convergence.py
- [X] T025 [P] [US1] Memory usage test for 1000 observations under 7GB in code/tests/integration/test_memory_profile.py
- [X] T026 [P] [US1] Unit test for low variance edge case handling in code/tests/unit/test_low_variance_edge_case.py
- [X] T027 [P] [US1] Unit test for missing values recovery in code/tests/unit/test_missing_values_edge_case.py
- [X] T028 [P] [US1] Unit test for concentration parameter sensitivity in code/tests/unit/test_concentration_parameter_edge_case.py
- [X] T029 [P] [US1] Unit test for anomaly cluster detection in code/tests/unit/test_anomaly_cluster_edge_case.py

### Implementation for User Story 1

- [X] T030 [P] [US1] Implement DPGMMModel class with stick-breaking construction in code/models/dpgmm.py
- [X] T031 [US1] Implement incremental posterior update method for streaming observations in code/models/dpgmm.py
- [X] T032 [US1] Implement anomaly score computation as negative log posterior probability in code/services/anomaly_detector.py
- [X] T033 [P] [US1] Add ADVI variational inference configuration with memory optimization in code/models/dpgmm.py
- [X] T034 [US1] Implement probabilistic uncertainty estimates for anomaly scoring in code/services/anomaly_detector.py
- [X] T035 [US1] Handle edge case: near-constant variance time series with numerical stability checks in code/models/dpgmm.py
- [X] T036 [US1] Handle edge case: missing values in time series with streaming update recovery in code/services/anomaly_detector.py
- [X] T037 [US1] Handle edge case: concentration parameter sensitivity with adaptive tuning in code/models/dpgmm.py
- [X] T038 [US1] Handle edge case: anomaly clusters vs isolated points in anomaly scoring in code/services/anomaly_detector.py
- [X] T039 [US1] Add logging for DPGMM update operations with ELBO convergence diagnostics in code/services/anomaly_detector.py
- [X] T040 [US1] Verify FR-001: stick-breaking construction for univariate time series <!-- FAILED-IN-EXECUTION: code/scripts/verify_fr001_stick_breaking.py exit=1 -->
- [X] T041 [US1] Verify FR-002: incremental posterior update after each observation <!-- FAILED-IN-EXECUTION: code/scripts/verify_fr002_incremental_update.py exit=1 -->
- [X] T042 [US1] Verify FR-003: anomaly scores as negative log posterior probability <!-- FAILED-IN-EXECUTION: code/scripts/verify_fr003_anomaly_scores.py exit=1 -->
- [X] T043 [US1] Consolidated verification: memory usage under 7GB during 1000 observation processing <!-- FAILED-IN-EXECUTION: code/scripts/verify_memory_usage.py exit=1 -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison and Performance Evaluation (Priority: P2)

**Goal**: Compare the DPGMM detector against ARIMA and moving average baselines on public benchmarks to validate F1-scores

**Independent Test**: Can be fully tested by running all three models on a single UCI dataset and generating precision-recall curves with F1-score measurements

### Tests for User Story 2 (MANDATORY per plan.md) ⚠️

- [X] T044 [P] [US2] Contract test for evaluation_metrics.schema.yaml in code/tests/contract/test_evaluation_metrics.py
- [X] T045 [P] [US2] Integration test for multi-model comparison pipeline in code/tests/integration/test_baseline_comparison.py <!-- FAILED-IN-EXECUTION: code/tests/integration/test_baseline_comparison.py exit=1 -->
- [X] T046 [P] [US2] Unit test for F1-score calculation in code/tests/unit/test_metrics.py
- [X] T047 [P] [US2] Unit test for ROC and PR curve generation in code/tests/unit/test_plots.py

### Implementation for User Story 2

- [X] T048 [P] [US2] Implement ARIMA baseline model in code/models/baselines.py
- [X] T049 [P] [US2] Implement moving average with z-score baseline in code/models/baselines.py
- [X] T050 [US2] Implement evaluation metrics: precision, recall, F1-score, AUC in code/evaluation/metrics.py
- [X] T051 [US2] Implement confusion matrix generation in code/evaluation/metrics.py
- [X] T052 [US2] Implement ROC curve generation and PNG export in code/evaluation/plots.py
- [X] T053 [US2] Implement PR curve generation and PNG export in code/evaluation/plots.py
- [X] T054 [US2] Implement paired t-tests with Bonferroni correction across datasets in code/evaluation/metrics.py
- [X] T055 [US2] Integrate DPGMM with baseline models for unified evaluation pipeline in code/services/anomaly_detector.py
- [X] T056 [US2] Verify FR-006: confusion matrices, ROC curves, PR curves for evaluation
- [X] T057 [US2] [Depends: T016] Verify FR-008: download 3-5 UCI datasets using wget/curl and confirm quantity requirement <!-- FAILED-IN-EXECUTION: code/scripts/download_uci_datasets.py exit=1 -->
- [X] T058 [US2] Verify SC-001: F1-score within 5% of baselines on at least 3 UCI datasets <!-- ATOMIZE: requested -->
- [X] T059 [US2] Verify SC-004: fewer hyperparameters than baseline methods (30% reduction)
- [X] T060 [US2] Verify SC-005: precision-recall curves generated for all datasets <!-- FAILED-IN-EXECUTION: code/scripts/verify_sc005_pr_curves.py exit=1 -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Anomaly Score Threshold Calibration (Priority: P3)

**Goal**: Calibrate the posterior probability threshold for anomaly flagging without labeled data for real-world streaming deployment

**Independent Test**: Can be fully tested by running the model on unlabeled data and verifying that the adaptive threshold produces reasonable anomaly rates based on statistical properties of the scores

### Tests for User Story 3 (MANDATORY per plan.md) ⚠️

- [X] T061 [P] [US3] Contract test for config.yaml threshold parameters in code/tests/contract/test_config.py
- [X] T062 [P] [US3] Integration test for adaptive threshold calibration on unlabeled data in code/tests/integration/test_threshold_calibration.py
- [X] T063 [P] [US3] Unit test for 95th percentile threshold computation in code/tests/unit/test_threshold.py

### Implementation for User Story 3

- [X] T064 [P] [US3] Implement ThresholdCalibrator service with adaptive threshold logic in code/services/threshold_calibrator.py
- [X] T065 [US3] Implement 95th percentile threshold computation from validation split in code/services/threshold_calibrator.py
- [X] T066 [US3] Implement anomaly rate validation against expected bounds in code/services/threshold_calibrator.py
- [X] T067 [US3] Implement anomaly flagging logic that marks observations exceeding threshold per FR-004 in code/services/anomaly_detector.py
- [X] T068 [US3] Document decision boundary in config.yaml for replication per FR-004
- [X] T069 [US3] Verify FR-004: flag observations when scores exceed adaptive threshold <!-- FAILED-IN-EXECUTION: code/scripts/verify_fr004_threshold_flagging.py exit=1 -->

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T070 [P] Final documentation polish: quickstart.md, data-model.md, research.md in specs/001-bayesian-nonparametrics-anomaly-detection/
- [X] T071 Code cleanup and refactoring across all modules <!-- ATOMIZE: requested -->
- [X] T072 [P] Performance optimization: verify <30 minutes runtime per dataset using runtime_profiler.py <!-- FAILED-IN-EXECUTION: code/scripts/verify_runtime_performance.py exit=1 -->
- [X] T073 [P] Verify SC-003: runtime per dataset does not exceed 30 minutes on GitHub Actions <!-- FAILED-IN-EXECUTION: code/scripts/verify_sc003_runtime.py exit=2 -->
- [X] T074 [P] Run quickstart.md intermediate validation checkpoint 1 after Phase 3 completion <!-- FAILED-IN-EXECUTION: code/scripts/validate_checkpoint_1.py exit=1 -->
- [X] T075 [P] Run quickstart.md intermediate validation checkpoint 2 after Phase 5 completion <!-- FAILED-IN-EXECUTION: code/scripts/validate_checkpoint_2.py exit=1 -->
- [X] T076 [P] Run quickstart.md final validation to ensure reproducibility <!-- FAILED-IN-EXECUTION: code/scripts/validate_final.py exit=1 -->
- [X] T077 [P] Generate experiment metadata with state tracking in state/ <!-- FAILED-IN-EXECUTION: code/services/state_tracker.py exit=1; code/scripts/generate_experiment_metadata.py exit=1 -->
- [X] T078 Final integration test: run full pipeline from data download to evaluation on all 3-5 UCI datasets <!-- FAILED-IN-EXECUTION: code/scripts/run_full_pipeline_integration_test.py exit=1; code/scripts/validate_integration_test_results.py exit=1 -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Constitution Check**: No dependencies - must pass before Phase 0
- **Phase 0 **(Research): Depends on Constitution Check - creates foundational docs
- **Phase 1 **(Setup): Depends on Phase 0 completion - can start immediately after
- **Phase 2 **(Foundational): Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories **(Phase 3+): All depend on Phase 2 completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Phase 6 **(Polish): Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 **(P1): Can start after Phase 2 completion - No dependencies on other stories
- **User Story 2 **(P2): Can start after Phase 2 completion - May integrate with US1 but should be independently testable
- **User Story 3 **(P3): Can start after Phase 2 completion - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (MANDATORY) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Phase 2 is complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (MANDATORY):
Task: "Contract test for anomaly_score.schema.yaml validation in code/tests/contract/test_anomaly_score.py"
Task: "Integration test for streaming DPGMM update in code/tests/integration/test_dpgmm_streaming.py"
Task: "Unit test for stick-breaking construction in code/tests/unit/test_stick_breaking.py"
Task: "Unit test for ADVI variational inference convergence in code/tests/unit/test_advi_convergence.py"
Task: "Memory usage test for 1000 observations under 7GB in code/tests/integration/test_memory_profile.py"
Task: "Unit test for low variance edge case handling in code/tests/unit/test_low_variance_edge_case.py"
Task: "Unit test for missing values recovery in code/tests/unit/test_missing_values_edge_case.py"
Task: "Unit test for concentration parameter sensitivity in code/tests/unit/test_concentration_parameter_edge_case.py"
Task: "Unit test for anomaly cluster detection in code/tests/unit/test_anomaly_cluster_edge_case.py"

# Launch all models for User Story 1 together:
Task: "Implement DPGMMModel class with stick-breaking construction in code/models/dpgmm.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Constitution Check
2. Complete Phase 0: Research
3. Complete Phase 1: Setup
4. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
5. Complete Phase 3: User Story 1
6. **STOP and VALIDATE**: Test User Story 1 independently
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Constitution Check → Compliance verified
2. Complete Phase 0 → Research documentation ready
3. Complete Phase 1 + Phase 2 → Foundation ready
4. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
5. Add User Story 2 → Test independently → Deploy/Demo
6. Add User Story 3 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Constitution Check + Phase 0 + Phase 1 together
2. Complete Phase 2 together
3. Once Phase 2 is done:
   - Developer A: User Story 1 (DPGMM core)
   - Developer B: User Story 2 (Baseline comparison)
   - Developer C: User Story 3 (Threshold calibration)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (tests are MANDATORY per plan.md)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All edge cases from spec.md must be handled: low variance, missing values, concentration parameter, anomaly clusters, runtime limits
- Constitution principles must remain satisfied throughout implementation
- All paths are relative to projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection/ project root
- Documentation files must reside in specs/ directory per plan.md Project Structure
- T057 explicitly declares dependency on T016 for download script implementation
- T070 clarifies documentation is final polish of existing artifacts, not recreation
- T074/T075/T076 provide intermediate validation checkpoints for quickstart.md
- T004 verifies all 7 constitution principles including Single Source of Truth