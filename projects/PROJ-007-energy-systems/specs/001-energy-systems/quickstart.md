# Quickstart: Energy Inequity Analysis Toolkit

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (for version control)
- Minimum 500MB free disk space
- Internet access (for initial setup and data downloads)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/llmXive/energy-20250704-001.git
cd energy-20250704-001
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Core Dependencies** (pinned per Constitution Principle I):
- `pandas==2.1.0`
- `numpy==1.26.0`
- `scikit-learn==1.3.0`
- `requests==2.31.0`
- `pydantic==2.5.0`
- `pyyaml==6.0.1`
- `pytest==7.4.0`

### 4. Verify Installation

```bash
python -c "import energy_toolkit; print(energy_toolkit.__version__)"
```

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# API Keys (if using external services)
# NOTE: Add .env to .gitignore per Constitution Principle II (Secrets)

# Optional: LLM provider for analysis assistance
LLM_PROVIDER=dartmouth  # Options: dartmouth, huggingface, local
LLM_API_KEY=your_key_here  # Only if required by provider

# Data Paths
DATA_DIR=./data
OUTPUT_DIR=./output
```

### Validate Configuration

```bash
python src/cli/main.py --validate-config
```

This performs **fail-fast checks** per Constitution Principle V:
- Required environment variables present
- Data directory exists and is writable
- Python version meets minimum requirement
- All dependencies installed

## Running Your First Analysis

### 1. Download Sample Data

```bash
python src/cli/main.py data download --sample
```

This fetches anonymized sample household data from the project's public repository.

### 2. Run Energy Burden Analysis

```bash
python src/cli/main.py analysis burden --input data/sample/households.csv --output output/burden_report.json
```

### 3. Generate Feasibility Report

```bash
python src/cli/main.py analysis feasibility --input output/burden_report.json --output output/feasibility.json
```

### 4. Validate Output Against Schema

```bash
python src/cli/main.py validate --input output/feasibility.json --schema contracts/energy_analysis.schema.yaml
```

## Testing

### Run Full Test Suite

```bash
pytest tests/ -v --tb=short
```

**Note**: Per Constitution Principle III, tests include real API calls where applicable. Mock tests are secondary only.

### Run Contract Tests

```bash
pytest tests/contract/ -v
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

## Project Structure Reference

```
energy-20250704-001/
├── src/
│   ├── models/          # Data models (Pydantic)
│   ├── services/        # Business logic
│   ├── cli/             # Command-line interface
│   └── lib/             # Shared utilities
├── tests/
│   ├── contract/        # Schema validation tests
│   ├── integration/     # End-to-end tests
│   └── unit/            # Unit tests
├── data/
│   ├── raw/             # Downloaded datasets
│   └── processed/       # Cleaned analysis data
├── contracts/           # Schema definitions
├── docs/                # Documentation
├── requirements.txt     # Dependency manifest
└── README.md            # Project overview
```

## Common Issues

### Issue: `ModuleNotFoundError`

**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: `PermissionError` on data write

**Solution**: Check directory permissions:
```bash
chmod 755 data/ output/
```

### Issue: Schema validation fails

**Solution**: Verify data matches contract schema:
```bash
python src/cli/main.py validate --help
```

## Next Steps

1. Review `research.md` for methodology details
2. Examine `data-model.md` for schema specifications
3. Read `plan.md` for implementation roadmap
4. Begin Phase 1 tasks (see `tasks.md` when available)
