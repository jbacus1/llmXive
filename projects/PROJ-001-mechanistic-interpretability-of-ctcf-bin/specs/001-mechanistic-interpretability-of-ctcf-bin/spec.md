# Feature Specification: Mechanistic Interpretability of CTCF Binding-Site Selection

**Feature Branch**: `001-ctcf-binding-interpretability`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Mechanistic Interpretability of CTCF Binding-Site Selection"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

As a researcher, I want to load and preprocess ENCODE ChIP-seq, ATAC-seq, and histone modification data for multiple cell types so that I have a standardized dataset ready for model training.

**Why this priority**: Without clean, standardized input data, no modeling or interpretation can occur. This is the foundational step for the entire pipeline.

**Independent Test**: Can be fully tested by executing the data loader script against a static subset of ENCODE data and verifying the output tensor shapes and metadata consistency without running the neural network.

**Acceptance Scenarios**:

1. **Given** valid ENCODE data paths for 10+ cell types, **When** the ingestion script runs, **Then** data is normalized and aligned to a common genomic coordinate system.
2. **Given** missing data for a specific cell type, **When** the ingestion script runs, **Then** the system logs a warning but continues processing available cell types.
3. **Given** mismatched sequence lengths, **When** preprocessing occurs, **Then** sequences are padded or truncated to a fixed context window size.

---

### User Story 2 - Transformer Model Training and Execution (Priority: P2)

As a researcher, I want to train a transformer-based sequence-context model to predict CTCF binding probability so that I have a predictive baseline to interpret.

**Why this priority**: The predictive model is the core asset that will be subjected to mechanistic interpretability analysis. It must be functional before interpretability tools can be applied.

**Independent Test**: Can be fully tested by training on a small dummy dataset and verifying loss convergence and validation AUC scores without applying sparse autoencoders.

**Acceptance Scenarios**:

1. **Given** preprocessed sequence and chromatin data, **When** the training job starts, **Then** the model converges to a loss below the defined threshold within 100 epochs.
2. **Given** a held-out test set from a new cell type, **When** the model predicts, **Then** it outputs binding probabilities with an AUC > 0.85.
3. **Given** a checkpoint file, **When** the inference script runs, **Then** it produces predictions for input sequences in under 10 seconds per kilobase.

---

### User Story 3 - Mechanistic Interpretation and Validation (Priority: P3)

As a researcher, I want to apply sparse autoencoders and feature attribution to identify latent features driving binding so that I can validate causal determinants via synthetic perturbations.

**Why this priority**: This delivers the specific research insight (interpretable features) promised in the project goal, validating the causal link between motifs and binding.

**Independent Test**: Can be fully tested by loading a pre-trained model and running the SAE decomposition on a fixed set of sequences to verify feature sparsity and motif correspondence.

**Acceptance Scenarios**:

1. **Given** a trained transformer model, **When** sparse autoencoders are applied to hidden layers, **Then** at least 3-5 interpretable latent features are extracted.
2. **Given** a synthetic sequence with a known motif, **When** the model predicts binding, **Then** the feature attribution highlights the motif region.
3. **Given** perturbed sequences (motif removed), **When** statistical testing is performed, **Then** predicted binding probability drops significantly (p < 0.05) compared to the original sequence.

---

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when **a specific cell type lacks matched ATAC-seq data** for the requested chromatin context?
- How does system handle **model convergence failure** where loss increases indefinitely during training?
- What happens when **sparse autoencoder features do not correspond to known biological motifs** (overfitting to noise)?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST ingest ChIP-seq and chromatin data from ENCODE for at least 10 distinct cell types.
- **FR-002**: System MUST train a transformer-based model using DNA sequence and chromatin features as input.
- **FR-003**: System MUST apply sparse autoencoders to decompose hidden layer activations into interpretable feature directions.
- **FR-004**: System MUST generate synthetic DNA sequences with systematic motif perturbations for validation.
- **FR-005**: System MUST output statistical significance metrics (permutation tests) for feature contributions.
- **FR-006**: System MUST allow configuration of _(Resolved by default; LLM clarifier could not pin a value: specific statistical significance threshold for permutation tests - p < 0.01 or p < 0.05?)_

### Key Entities *(include if feature involves data)*

- **SequenceContext**: Represents DNA sequence paired with local chromatin accessibility and histone modification profiles.
- **LatentFeature**: Represents an interpretable direction in the model's activation space corresponding to biological determinants.
- **BindingPrediction**: Represents the output probability of CTCF binding for a given genomic locus.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Model achieves >85% AUC on held-out cell types not used during training.
- **SC-002**: System identifies 3-5 distinct latent features that correspond to known CTCF-related sequence motifs or chromatin contexts.
- **SC-003**: Synthetic perturbation experiments show >90% correlation between predicted binding changes and actual model probability shifts.

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- ENCODE data is accessible via public API or direct download without authentication barriers.
- GPU resources are available to support transformer training within a reasonable timeframe (e.g., < 48 hours).
- Existing biological knowledge (e.g., known CTCF motifs) exists to validate the extracted latent features.
- _(Resolved by default; LLM clarifier could not pin a value: Specific hardware memory constraints for sparse autoencoder training are not defined)_.
- CRISPRi perturbation datasets are available for external validation if primary synthetic validation fails.
