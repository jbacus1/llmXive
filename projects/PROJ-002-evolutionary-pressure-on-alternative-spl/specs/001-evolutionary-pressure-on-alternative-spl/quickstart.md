# Quickstart: Evolutionary Pressure on Alternative Splicing in Primates

## Prerequisites

- **OS**: Linux (Ubuntu 20.04+ or RHEL 8+)
- **Python**: 3.11+
- **Disk Space**: Minimum 500GB (for raw data and intermediate files)
- **Memory**: Minimum 64GB RAM (for STAR alignment)
- **Dependencies**: STAR, SAMtools, Bedtools, SRA Toolkit installed system-wide or via conda.

## Environment Setup

1. **Clone Repository**
   ```bash
   git clone <repo_url>
   cd projects/PROJ-002-evolutionary-pressure-on-alternative-spl
   ```

2. **Create Virtual Environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python Dependencies**
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Verify External Tools**
   ```bash
   star --version
   samtools --version
   sra-toolkit --version
   ```

## Data Acquisition

1. **Update Metadata**
   Edit `data/metadata.yaml` to include target SRA accessions for Human, Chimp, Macaque, and Marmoset cortex samples.

2. **Download Data**
   Run the acquisition script:
   ```bash
   python code/src/acquisition/sra_downloader.py --config data/metadata.yaml --output data/raw/
   ```
   *Note: Ensure checksums are recorded automatically in `state/`.*

## Pipeline Execution

1. **Alignment**
   ```bash
   python code/src/alignment/star_runner.py --genome GRCh38 --input data/raw/sample_*.fq --output data/processed/alignments/
   ```

2. **Quantification**
   ```bash
   python code/src/quantification/rmats_wrapper.py --bam data/processed/alignments/*.bam --gtf data/annotations.gtf --output data/processed/psi_matrix.csv
   ```

3. **Analysis**
   ```bash
   python code/src/analysis/differential_splicing.py --input data/processed/psi_matrix.csv --output data/processed/differential_events.json
   ```

4. **Enrichment**
   ```bash
   python code/src/analysis/enrichment_test.py --events data/processed/differential_events.json --phylo data/annotations/phylop.bed --output data/processed/enrichment_results.json
   ```

## Verification

1. **Run Contract Tests**
   ```bash
   pytest tests/contract/
   ```

2. **Check Reproducibility**
   Re-run the pipeline and verify `state/projects/PROJ-002-evolutionary-pressure-on-alternative-spl.yaml` checksums match.

3. **Validate Outputs**
   Ensure `data/processed/differential_events.json` matches the schema in `contracts/differential_splicing_event.schema.yaml`.

## Troubleshooting

- **Memory Error**: Reduce `--limitBAMsortRAM` in STAR config or process samples in batches.
- **Mapping Rate Low**: Check genome version compatibility with GTF annotation.
- **Missing phyloP**: Verify `data/annotations/phylop.bed` covers all target chromosomes.
