# Data Model: Mechanistic Interpretability of CTCF Binding-Site Selection

## Key Entities

### SequenceContext

Represents DNA sequence paired with local chromatin accessibility and histone modification profiles.

**Purpose**: Input to the transformer model for binding prediction

**Attributes**:
- `sequence_id`: Unique identifier for the genomic locus
- `genome_build`: Genome assembly (e.g., GRCh38/hg38)
- `chromosome`: Chromosome name (e.g., chr1)
- `start_position`: Start coordinate (0-based)
- `end_position`: End coordinate (0-based)
- `cell_type`: Cell type identifier (e.g., GM12878)
- `dna_sequence`: DNA sequence string (A,C,G,T,N)
- `chromatin_accessibility`: ATAC-seq signal array
- `histone_modifications`: Dict of histone mark signals (e.g., H3K27ac, H3K4me3)
- `ctcf_chipseq`: CTCF ChIP-seq signal (ground truth)
- `context_window`: Fixed size in base pairs (2048bp)

**Constraints**:
- Sequence length must match context_window
- Chromatin signals must be aligned to sequence coordinates
- Missing modalities allowed but logged

### LatentFeature

Represents an interpretable direction in the model's activation space corresponding to biological determinants.

**Purpose**: Output of sparse autoencoder decomposition for interpretability analysis

**Attributes**:
- `feature_id`: Unique identifier for the latent feature
- `layer_index`: Transformer layer where feature was extracted
- `feature_vector`: Weight vector in activation space
- `sparsity_score`: L1/L2 ratio indicating feature sparsity
- `motif_correspondence`: Dict mapping to known motifs (e.g., JASPAR ID)
- `cell_types_active`: List of cell types where feature is active
- `activation_threshold`: Activation threshold for feature detection
- `biological_annotation`: Text description of biological function

**Constraints**:
- Must have sparsity_score > threshold (configurable)
- Motif correspondence validated against external databases
- Requires perturbation evidence for causal claims

### BindingPrediction

Represents the output probability of CTCF binding for a given genomic locus.

**Purpose**: Model output for binding site prediction

**Attributes**:
- `prediction_id`: Unique identifier for the prediction
- `sequence_id`: Reference to SequenceContext
- `binding_probability`: Probability score (0-1)
- `confidence_interval`: 95% confidence interval
- `feature_contributions`: Dict of latent feature contributions
- `attribution_method`: Method used (e.g., integrated gradients)
- `timestamp`: Prediction timestamp
- `model_version`: Model checkpoint identifier

**Constraints**:
- Probability must be in [0, 1]
- Confidence intervals computed via bootstrap or Bayesian methods
- Feature contributions must sum to total prediction

## Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ENCODE Data   │────▶│  Data Ingestion │────▶│  SequenceContext│
│   (ChIP-seq,    │     │  & Preprocessing│     │  (Preprocessed) │
│    ATAC-seq,    │     │                 │     │                 │
│    Histone)     │     └─────────────────┘     └────────┬────────┘
└─────────────────┘                                      │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Synthetic       │◀────│  Model          │◀────│  Transformer    │
│ Perturbations   │     │  Training       │     │  Model          │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Statistical     │◀────│  Interpretation │◀────│  Binding        │
│ Validation      │     │  (SAE,          │     │  Prediction     │
│ (p-values,      │     │   Perturbation) │     │                 │
│  Correlation)   │     └─────────────────┘     └─────────────────┘
└─────────────────┘
```

## File Organization

### Input Data (data/raw/)
```
data/
├── manifest.json              # Accession numbers, checksums, genome builds
└── raw/
    ├── GM12878/
    │   ├── CTCF_chipseq.bed.gz
    │   ├── ATAC_seq.bed.gz
    │   └── H3K27ac_chipseq.bed.gz
    ├── K562/
    │   └── ...
    └── ... (10+ cell types)
```

### Processed Data (data/processed/)
```
data/
└── processed/
    ├── sequence_contexts.parquet
    ├── train_split.parquet
    ├── validation_split.parquet
    └── test_split.parquet
```

### Model Artifacts (code/models/)
```
code/
└── models/
    ├── checkpoints/
    │   ├── transformer_epoch_100.pt
    │   └── sae_layer_3.pt
    └── configs/
        ├── training_config.yaml
        └── sae_config.yaml
```

### Output Data (data/outputs/)
```
data/
└── outputs/
    ├── predictions.parquet
    ├── latent_features.parquet
    ├── perturbation_results.parquet
    └── statistical_tests.json
```

## Data Validation Rules

| Entity | Validation Rule | Error Handling |
|--------|----------------|----------------|
| SequenceContext | DNA sequence contains only A,C,G,T,N | Reject invalid sequences |
| SequenceContext | Coordinates within chromosome bounds | Log warning, skip locus |
| SequenceContext | Context window = 2048bp | Pad/truncate as needed |
| LatentFeature | Sparsity score > 0.1 | Filter below threshold |
| LatentFeature | Motif correspondence verified | Flag uncorresponded features |
| BindingPrediction | Probability in [0, 1] | Clip to bounds |

## Schema References

This data model is formally specified in the following schema files:
- `contracts/sequence_context.schema.yaml` - SequenceContext entity validation
- `contracts/latent_feature.schema.yaml` - LatentFeature entity validation
- `contracts/binding_prediction.schema.yaml` - BindingPrediction entity validation
