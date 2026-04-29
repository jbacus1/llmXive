# Tasks: Climate-Smart Agricultural Practices for Food Security

**Input**: Design documents from `/specs/agriculture-20250704-001/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are INCLUDED - the constitution requires verified accuracy and robustness.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (src/, tests/, data/, docs/, contracts/)
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, geopandas, rasterio, scikit-learn, matplotlib, requests, pytest)
- [X] T003 [P] Configure linting and formatting tools (black, flake8, isort)
- [X] T004 [P] Setup pytest configuration with test discovery patterns

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement fail-fast validation in src/cli/validate.py (API keys, disk space, file existence)
- [X] T006 [P] Setup configuration management in src/config/constants.py (Principle I compliance)
- [X] T007 [P] Create schema validation helpers in src/config/schemas.py
- [X] T008 [P] Implement caching layer in src/data/cache.py (SQLite-based)
- [X] T009 [P] Setup error handling and logging infrastructure
- [X] T010 Create data-model.md and contracts/dataset.schema.yaml
- [X] T011 Create contracts/output.schema.yaml for pipeline outputs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection & Ingestion (Priority: P1) 🎯 MVP

**Goal**: Collect and ingest agricultural, climate, and socioeconomic data from multiple sources

**Independent Test**: Verify data files are downloaded, validated, and stored in data/raw/ with proper metadata

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Contract test for schema validation in tests/contract/test_dataset_schema.py
- [X] T013 [P] [US1] Integration test for OpenWeatherMap API in tests/integration/test_api_calls.py
- [X] T014 [P] [US1] Integration test for USGS EarthExplorer in tests/integration/test_usgs_api.py

### Implementation for User Story 1

- [X] T015 [P] [US1] Create survey data collector in src/data/collectors/survey_collector.py
- [X] T016 [P] [US1] Create climate data collector in src/data/collectors/climate_collector.py
- [X] T017 [US1] Implement remote sensing collector in src/data/collectors/remote_sensing_collector.py (uses rasterio)
- [X] T018 [US1] Implement API client in src/services/api_client.py (OpenWeatherMap, USGS)
- [X] T019 [US1] Add validation and error handling for all data collectors
- [X] T020 [US1] Add logging for data collection operations
- [X] T021 [US1] Implement data preprocessing in src/data/processors/survey_processor.py
- [X] T022 [US1] Implement data preprocessing in src/data/processors/climate_processor.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Climate Risk Assessment (Priority: P2)

**Goal**: Analyze climate data and assess risks to agricultural productivity

**Independent Test**: Verify risk scores are calculated and stored with proper schema validation

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Contract test for risk assessment output in tests/contract/test_risk_schema.py
- [X] T024 [P] [US2] Integration test for climate risk model in tests/integration/test_climate_risk.py

### Implementation for User Story 2

- [ ] T025 [P] [US2] Create climate_risk model in src/models/climate_risk.py
- [ ] T026 [US2] Implement statistical analysis using pandas and scikit-learn
- [ ] T027 [US2] Implement time series analysis for historical climate patterns
- [ ] T028 [US2] Implement regression analysis for yield prediction
- [ ] T029 [US2] Add GIS-based risk mapping in src/services/gis_mapper.py
- [ ] T030 [US2] Add validation and error handling for risk calculations
- [ ] T031 [US2] Add logging for climate risk assessment operations

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - CSA Recommendation Engine (Priority: P3)

**Goal**: Generate climate-smart agricultural practice recommendations for specific communities

**Independent Test**: Verify recommendations are generated with proper justification and schema validation

### Tests for User Story 3 ⚠️

- [ ] T032 [P] [US3] Contract test for recommendation output in tests/contract/test_recommendation_schema.py
- [ ] T033 [P] [US3] Integration test for recommendation pipeline in tests/integration/test_recommendations.py

### Implementation for User Story 3

- [ ] T034 [P] [US3] Create adoption_rate model in src/models/adoption_rate.py
- [ ] T035 [P] [US3] Create crop_yield model in src/models/crop_yield.py
- [ ] T036 [US3] Implement recommendation logic in src/services/recommendation_engine.py
- [ ] T037 [US3] Integrate sustainability, ecosystem service, and social equity principles
- [ ] T038 [US3] Add validation for recommendation outputs
- [ ] T039 [US3] Add logging for recommendation generation operations
- [ ] T040 [US3] Implement intervention strategy module in src/models/intervention_strategies.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - GIS Visualization & Reporting (Priority: P4)

**Goal**: Generate visualizations and reports for stakeholders

**Independent Test**: Verify visualizations are generated in <30 seconds and reports match schema

### Tests for User Story 4 ⚠️

- [ ] T041 [P] [US4] Contract test for visualization output in tests/contract/test_visualization_schema.py
- [ ] T042 [P] [US4] Integration test for GIS visualization in tests/integration/test_gis_visualization.py

### Implementation for User Story 4

- [ ] T043 [P] [US4] Create GIS mapper service in src/services/gis_mapper.py (uses geopandas, rasterio)
- [ ] T044 [US4] Implement visualization generation in src/services/visualization.py (matplotlib)
- [ ] T045 [US4] Implement report generation in src/services/report_generator.py
- [ ] T046 [US4] Add validation for visualization outputs
- [ ] T047 [US4] Add logging for visualization operations
- [ ] T048 [US4] Implement quickstart.md validation script

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049 [P] Documentation updates in docs/
- [ ] T050 Code cleanup and refactoring
- [ ] T051 Performance optimization across all stories (process 10,000+ records in <5 minutes)
- [ ] T052 [P] Additional unit tests in tests/unit/test_models.py
- [ ] T053 Security hardening (API key management, input sanitization)
- [ ] T054 Run quickstart.md validation
- [ ] T055 Docker setup for reproducibility (Dockerfile, docker-compose.yml)
- [ ] T056 Create README.md with project overview
- [ ] T057 Create research.md with primary source citations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - May integrate with US1/US2/US3 but should be independently testable

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
Task: "Contract test for schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for OpenWeatherMap API in tests/integration/test_api_calls.py"
Task: "Integration test for USGS EarthExplorer in tests/integration/test_usgs_api.py"

# Launch all collectors for User Story 1 together:
Task: "Create survey data collector in src/data/collectors/survey_collector.py"
Task: "Create climate data collector in src/data/collectors/climate_collector.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Collection)
   - Developer B: User Story 2 (Climate Risk)
   - Developer C: User Story 3 (Recommendations)
   - Developer D: User Story 4 (Visualization)
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
- All data sources must be free/open (Principle IV)
- All API calls must fail-fast validation (Principle V)
- All claims verified against primary sources (Principle II)
