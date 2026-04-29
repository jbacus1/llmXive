# Quickstart: Mechanistic Interpretability of CTCF Binding-Site Selection

## Prerequisites

- Python 3.11+
- CUDA-capable GPU (16GB+ VRAM recommended)
- 100GB+ available disk space
- ENCODE account (for data access)

## Installation

### Step 1: Clone and Setup Environment

```bash
cd projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/code/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Verify Dependencies

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
```

## Data Preparation

### Step 3: Download ENCODE Data

1. Register at https://www.encodeproject.org/
2. Navigate to the project's `data/manifest.json`
3. Download all listed datasets using ENCODE accession numbers
4. Place raw files in `data/raw/<cell_type>/`

### Step 4: Verify Data Integrity

```bash
python code/data/loader.py --verify-only
```

Expected output: All checksums match manifest.json

### Step 5: Run Preprocessing

```bash
python code/data/preprocess.py \
  --input-dir data/raw/ \
  --output-dir data/processed/ \
  --context-window 2048 \
  --genome-build hg38
```

## Model Training

### Step 6: Configure Training

Edit `code/models/configs/training_config.yaml`:

```yaml
model:
  hidden_dim: 768
  num_layers: 12
  context_window: 2048

training:
  batch_size: 32
  epochs: 100
  learning_rate: 0.0001
  seed: 42

validation:
  test_cell_types:
    - GM12878
    - K562
```

### Step 7: Start Training

```bash
python code/training/train.py \
  --config code/models/configs/training_config.yaml \
  --data-dir data/processed/ \
  --output-dir code/models/checkpoints/
```

Training should complete within 48 hours on a single GPU.

### Step 8: Verify Training Convergence

```bash
python code/training/train.py --check-convergence \
  --loss-threshold 0.3 \
  --checkpoint code/models/checkpoints/
```

Expected: Loss < 0.3 after 100 epochs

## Inference and Interpretation

### Step 9: Run Inference

```bash
python code/training/inference.py \
  --checkpoint code/models/checkpoints/transformer_epoch_100.pt \
  --input-dir data/processed/ \
  --output data/outputs/predictions.parquet
```

Expected: <10 seconds per kilobase

### Step 10: Apply Sparse Autoencoder

```bash
python code/models/sae.py \
  --model code/models/checkpoints/transformer_epoch_100.pt \
  --layer-index 3 \
  --output data/outputs/latent_features.parquet
```

Expected: 3-5 interpretable latent features extracted

### Step 11: Generate Perturbations

```bash
python code/interpretation/perturbation.py \
  --input data/outputs/predictions.parquet \
  --motif-file code/data/known_ctcf_motifs.fasta \
  --output data/outputs/perturbation_results.parquet
```

### Step 12: Statistical Validation

```bash
python code/validation/significance.py \
  --predictions data/outputs/predictions.parquet \
  --perturbations data/outputs/perturbation_results.parquet \
  --threshold p < 0.05 \
  --output data/outputs/statistical_tests.json
```

## Contract Testing

### Step 13: Run Contract Tests

```bash
pytest tests/contract/ -v
```

Expected: All contract tests pass against schema definitions

### Step 14: Run Integration Tests

```bash
pytest tests/integration/test_pipeline.py -v
```

Expected: Full pipeline executes without errors

## Troubleshooting

### Issue: Data checksum mismatch

**Solution**: Re-download affected dataset from ENCODE; update manifest.json

### Issue: Model convergence failure

**Solution**: Adjust learning_rate in training_config.yaml; check for data leakage

### Issue: SAE features lack motif correspondence

**Solution**: Increase sparsity threshold; verify known_motifs.fasta is current

### Issue: GPU memory exhaustion

**Solution**: Reduce batch_size in training_config.yaml; enable gradient checkpointing

## Next Steps

1. Review `research.md` for methodology details
2. Examine `data-model.md` for entity specifications
3. Run `tests/unit/` for module-level validation
4. Generate figures from `data/outputs/` for paper
