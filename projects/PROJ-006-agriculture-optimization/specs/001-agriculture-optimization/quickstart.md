# Quickstart: Climate-Smart Agricultural Practices Pipeline

**Project**: agriculture-20250704-001  
**Date**: 2026-04-28  
**Version**: 1.0.0

## Prerequisites

Before running this project, ensure you have:

- **Python 3.11+** installed
- **Git** for version control
- **5GB free disk space** for data and cache
- **Internet connection** for API calls (Principle V validation)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/llmXive/agriculture-20250704-001.git
cd agriculture-20250704-001
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Core Dependencies**:
- pandas==2.2.0
- geopandas==0.14.0
- rasterio==1.3.9
- scikit-learn==1.4.0
- matplotlib==3.8.0
- requests==2.31.0
- pytest==8.0.0

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys (required for data collection)
OPENWEATHERMAP_API_KEY=your_api_key_here
USGS_USERNAME=your_usgs_username
USGS_PASSWORD=your_usgs_password

# Optional: For paid tier access (Principle IV: free-first)
# NASA_EARTHDATA_USERNAME=your_username
# NASA_EARTHDATA_PASSWORD=your_password
```

### Step 5: Run Pre-flight Validation

```bash
python src/cli/validate.py
```

This checks:
- All required environment variables are set
- Disk space is sufficient (>5GB)
- Network connectivity to data sources
- Python version compatibility
- All required files exist

## Running the Pipeline

### Basic Execution

```bash
python src/cli/run_pipeline.py --config configs/default.yaml
```

### With Custom Parameters

```bash
python src/cli/run_pipeline.py \
  --config configs/custom.yaml \
  --regions sub-saharan-africa,south-asia \
  --practices conservation-tillage,agroforestry,improved-varieties \
  --output-dir outputs/2026-04-
```

### Running Tests

```bash
# Contract tests (schema validation)
pytest tests/contract/ -v

# Integration tests (real API calls - Principle III)
pytest tests/integration/ -v --real-calls

# Full test suite
pytest -v
```

## Data Directory Structure

```
data/
├── raw/                    # Downloaded raw data
│   ├── remote-sensing/     # GeoTIFF files
│   ├── surveys/            # CSV survey data
│   └── climate/            # Climate API responses
├── processed/              # Cleaned/transformed data
│   ├── harmonized/         # Spatially/temporally aligned
│   └── features/           # Feature-engineered datasets
└── cache.db                # SQLite cache for API responses
```

## Output Files

After running the pipeline, check:

- `outputs/reports/vulnerability_assessment.csv` - Site vulnerability scores
- `outputs/reports/adoption_recommendations.csv` - Recommended practices
- `outputs/visualizations/climate_risk_map.png` - GIS visualization
- `outputs/visualizations/yield_comparison.png` - Yield impact charts

## Troubleshooting

### API Rate Limiting

If you encounter rate limit errors:

```bash
# Enable caching (reduces API calls)
python src/cli/run_pipeline.py --enable-cache

# Add delay between requests
export API_REQUEST_DELAY=2  # seconds
```

### Missing Data

For missing climate data:

```bash
# Use imputation
python src/cli/run_pipeline.py --impute-missing

# Check which sites have gaps
python src/cli/validate.py --check-data-completeness
```

### Schema Validation Errors

If schema validation fails:

```bash
# Check which records failed
pytest tests/contract/ -v --tb=short

# View validation report
cat outputs/validation_report.json
```

## Next Steps

1. **Customize Configuration**: Edit `configs/default.yaml` for your regions
2. **Add Your Data**: Place survey data in `data/raw/surveys/`
3. **Run Analysis**: Execute the pipeline with your parameters
4. **Review Results**: Check outputs and adjust models as needed
5. **Document Findings**: Update `docs/research_findings.md` with results

## Support

- **Issues**: https://github.com/llmXive/agriculture-20250704-001/issues
- **Documentation**: See `docs/` directory
- **Constitution**: See `projects/agriculture-20250704-001/.specify/memory/constitution.md`
