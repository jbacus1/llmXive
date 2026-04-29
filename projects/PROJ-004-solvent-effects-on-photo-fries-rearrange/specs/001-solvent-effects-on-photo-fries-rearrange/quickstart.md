# Quickstart: Solvent Effects on Photo-Fries Rearrangement Kinetics

## Prerequisites

- Python 3.11 or later
- Access to laser flash photolysis instrumentation (or simulated data for development)
- Access to DFT compute cluster (Gaussian or ORCA) or local compute resources
- Git for version control

## Repository Setup

```bash
# Clone the project repository
git clone <repository-url>
cd projects/PROJ-004-solvent-effects-on-photo-fries-rearrange

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Project Structure Overview

```
projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/
├── code/                    # Analysis scripts and instrumentation interfaces
│   ├── solvent_config.py    # Solvent series configuration
│   ├── kinetic_analysis.py  # Global kinetic analysis and lifetime extraction
│   ├── dft_solvation.py     # DFT solvation energy computation interface
│   └── correlation_analysis.py  # Statistical correlation and regression
├── data/                    # Experimental and computational data
│   ├── raw/                 # Unmodified instrument and compute output
│   ├── compute/             # DFT input files
│   ├── chemicals/           # Reagent and solvent provenance records
│   └── processed/           # Derived metrics and analysis results
├── docs/                    # Project documentation
│   ├── deviation_analysis.md  # Computational-experimental deviation analysis
│   └── chemical_provenance.md # Chemical provenance and purity records
└── state/                   # Project state and artifact hashes
```

## Running the Analysis Pipeline

### Step 1: Configure Solvent Series

```bash
# Create solvent configuration file
python code/solvent_config.py --config specs/001-solvent-effects/solvents.yaml

# Expected output: solvent_registry.yaml in data/chemicals/
```

### Step 2: Execute Experimental Protocol

```bash
# For each solvent in the series:
python code/kinetic_analysis.py --solvent cyclohexane --replicates 3

# Expected output: decay traces in data/raw/laser_flash_photolysis/
#                  lifetime metrics in data/processed/lifetimes.csv
```

### Step 3: Compute Solvation Energies

```bash
# Submit DFT jobs for each solvent
python code/dft_solvation.py --solvents data/chemicals/solvent_registry.yaml

# Expected output: solvation energies in data/processed/solvation_energies.csv
```

### Step 4: Correlation Analysis

```bash
# Generate regression plot and statistical test
python code/correlation_analysis.py --lifetimes data/processed/lifetimes.csv \
                                     --solvation data/processed/solvation_energies.csv \
                                     --output docs/correlation_results.pdf
```

## Testing

```bash
# Run all tests
pytest code/tests/ -v

# Run contract validation tests
pytest code/tests/contract/ -v
```

## Data Validation

```bash
# Validate data against contract schemas
python code/validate_data.py --schema specs/001-solvent-effects/contracts/solvent.schema.yaml \
                              --data data/processed/lifetimes.csv
```

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| DFT computation fails | Check convergence criteria; try alternative solvent model (PCM instead of SMD) |
| Kinetic fit R² < 0.95 | Verify instrument calibration; check laser pulse intensity settings |
| Statistical significance p > 0.01 | Increase replicate count (n ≥ 3 required); verify data quality |
| Checksum mismatch | Re-download raw data from canonical source; verify file integrity |

## References

See `research.md` for full literature references. All citations will be verified by the Reference-Validator Agent before contributing review points.
