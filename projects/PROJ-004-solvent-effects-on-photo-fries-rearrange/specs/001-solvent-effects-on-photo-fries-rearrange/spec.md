# Feature Specification: Solvent Effects on Photo-Fries Rearrangement Kinetics

**Feature Branch**: `001-solvent-effects`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Solvent Effects on Photo-Fries Rearrangement Kinetics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure and Execute Solvent Series (Priority: P1)

The researcher MUST be able to define a series of solvents ranging from non-polar to polar and initiate the experimental protocol for each condition.

**Why this priority**: This is the foundational step. Without a controlled solvent series, no kinetic data can be collected, and the research question cannot be addressed. It delivers the primary dataset.

**Independent Test**: Can be fully tested by configuring a solvent list (e.g., cyclohexane, methanol) and verifying the system logs the dielectric constant and temperature settings for each run.

**Acceptance Scenarios**:

1. **Given** a list of 5+ solvents with known dielectric constants, **When** the researcher configures the experiment, **Then** the system records each solvent's properties and prepares the instrument parameters.
2. **Given** a configured solvent series, **When** the researcher initiates the laser flash photolysis, **Then** the system captures transient-absorption data for the defined time range (1 ns–10 μs).

---

### User Story 2 - Extract Radical-Pair Lifetime (Priority: P2)

The system MUST process the raw spectroscopic data to extract the singlet-radical-pair intermediate lifetime via global kinetic analysis.

**Why this priority**: This transforms raw data into the primary metric (lifetime) required to answer the research question. It is a distinct analytical step from data collection.

**Independent Test**: Can be fully tested by uploading a set of decay traces and verifying the system outputs a lifetime value derived from exponential fitting.

**Acceptance Scenarios**:

1. **Given** raw decay traces from transient-absorption detection, **When** the system performs global kinetic analysis, **Then** it outputs a lifetime value with a confidence interval.
2. **Given** multiple replicates (n ≥ 3) for a single solvent, **When** the analysis completes, **Then** the system calculates the mean and standard deviation of the lifetime.

---

### User Story 3 - Correlate Solvation Energy with Product Distribution (Priority: P3)

The researcher MUST be able to correlate computed solvation free energies with the experimentally determined lifetimes and product distributions.

**Why this priority**: This synthesizes the computational and experimental data to validate the hypothesis (monotonic decrease in lifetime with polarity). It represents the final insight generation.

**Independent Test**: Can be fully tested by inputting solvation energy values and lifetime data, verifying the system generates a regression plot and statistical significance test.

**Acceptance Scenarios**:

1. **Given** lifetime data for ≥5 solvent conditions and corresponding solvation free energies, **When** the correlation analysis is run, **Then** the system outputs a regression coefficient (R²).
2. **Given** product distribution data from HPLC, **When** the statistical analysis is performed, **Then** the system confirms if trends meet statistical significance (p < 0.01).

---

### Edge Cases

- What happens when a solvent evaporates significantly during the measurement window, altering the dielectric constant?
- How does system handle photodegradation of the substrate if the laser pulse intensity is too high?
- What happens when DFT computation fails for a specific solvent model?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow configuration of at least 5 distinct solvent conditions spanning a dielectric constant range of ε ≈ 2 to ε ≈ 33.
- **FR-002**: System MUST capture transient-absorption spectroscopy data in the 200–800 nm wavelength range with 1 ns–10 μs time resolution.
- **FR-003**: System MUST perform global kinetic analysis on decay traces using exponential fitting to extract intermediate lifetimes.
- **FR-004**: System MUST integrate or accept computed solvation free energies from implicit solvent models (SMD/PCM) at DFT level.
- **FR-005**: System MUST perform statistical significance testing (ANOVA) across solvent conditions with support for n ≥ 3 replicates.

*Example of marking unclear requirements:*

- **FR-006**: System MUST validate product isomers via HPLC using _(Resolved by default; LLM clarifier could not pin a value: Specific column type and gradient method not specified in idea)_.
- **FR-007**: System MUST compute DFT energies using _(Resolved by default; LLM clarifier could not pin a value: Computational resource allocation and queue management not specified)_.

### Key Entities *(include if feature involves data)*

- **Solvent Condition**: Represents a specific solvent environment (Dielectric Constant, Temperature, Volume).
- **Kinetic Trace**: Represents the raw transient-absorption data for a specific solvent and time window.
- **Reaction Metric**: Represents the derived lifetime and product distribution values for a condition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Correlation between lifetime and solvation energy achieves R² > 0.8.
- **SC-002**: Consistent trends observed across ≥5 solvent conditions.
- **SC-003**: Statistical significance testing yields p < 0.01 for observed trends.

## Assumptions

- Substrate (e.g., phenyl benzoate) purity will be >99% as per standard esterification protocols.
- Temperature control will be maintained at 25 ± 0.5°C throughout all measurements.
- Access to laser flash photolysis equipment with nanosecond resolution is available.
- Computational resources for B3LYP/6-31G* calculations are accessible.

## References

- [Learning Continuous Solvent Effects from Transient Flow Data: A Graph Neural Network Benchmark on Catechol Rearrangement (2025)](http://arxiv.org/abs/2512.19530v1)
- [Fluctuations and correlations in chemical reaction kinetics and population dynamics (2018)](http://arxiv.org/abs/1807.01248v1)
- [Erratum to the article: Charge transfer to solvent identified using dark channel fluorescence-yield L-edge spectroscopy, NATURE CHEMISTRY 2 (2010) 853 (2017)](http://arxiv.org/abs/1705.03941v2)
- [Enhancing Swelling Kinetics of pNIPAM Lyogels: The Role of Crosslinking, Copolymerization, and Solvent (2025)](http://arxiv.org/abs/2503.14134v2)
- [Guest Editorial: Special Topic on Data-enabled Theoretical Chemistry (2018)](http://arxiv.org/abs/1806.02690v2)
