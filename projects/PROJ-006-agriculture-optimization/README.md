# Climate-Smart Agricultural Practices for Food Security

**Version**: 1.0.0  
**Stage**: research_complete  
**Backend**: dartmouth (fallback: huggingface, then local)

---

## 🎯 Project Overview

This project provides a comprehensive framework for analyzing climate risks to agricultural productivity and generating climate-smart agricultural (CSA) practice recommendations for specific communities. It integrates agricultural, climate, and socioeconomic data from multiple open sources to support evidence-based decision-making for food security.

### Core Capabilities

1. **Data Collection & Ingestion** (US1) - Collect and validate agricultural, climate, and socioeconomic data
2. **Climate Risk Assessment** (US2) - Analyze climate data and assess risks to agricultural productivity
3. **CSA Recommendation Engine** (US3) - Generate climate-smart agricultural practice recommendations
4. **GIS Visualization & Reporting** (US4) - Generate visualizations and reports for stakeholders

---

## 📋 User Stories

| Story | Priority | Status | Description |
|-------|----------|--------|-------------|
| US1 | P1 | ✅ Complete | Data Collection & Ingestion |
| US2 | P2 | ✅ Complete | Climate Risk Assessment |
| US3 | P3 | ✅ Complete | CSA Recommendation Engine |
| US4 | P4 | ✅ Complete | GIS Visualization & Reporting |

---

## 🏗️ Project Structure

```
projects/<PROJ-ID>/
├── src/                          # Source code
│   ├── cli/                      # Command-line interface
│   │   └── validate.py           # Fail-fast validation
│   ├── config/                   # Configuration management
│   │   ├── constants.py          # Project constants
│   │   └── schemas.py            # Schema validation helpers
│   ├── data/                     # Data handling
│   │   ├── cache.py              # SQLite-based caching
│   │   ├── collectors/           # Data collectors
│   │   │   ├── survey_collector.py
│   │   │   ├── climate_collector.py
│   │   │   └── remote_sensing_collector.py
│   │   └── processors/           # Data processors
│   │       ├── survey_processor.py
│   │       └── climate_processor.py
│   ├── models/                   # ML/statistical models
│   │   ├── climate_risk.py       # Climate risk assessment
│   │   ├── adoption_rate.py      # Adoption rate modeling
│   │   ├── crop_yield.py         # Crop yield prediction
│   │   └── intervention_strategies.py
│   └── services/                 # Business logic
│       ├── api_client.py         # External API integration
│       ├── gis_mapper.py         # GIS-based risk mapping
│       ├── recommendation_engine.py
│       ├── visualization.py      # Visualization generation
│       └── report_generator.py   # Report generation
├── tests/                        # Test suite
│   ├── contract/                 # Schema contract tests
│   │   ├── test_dataset_schema.py
│   │   ├── test_risk_schema.py
│   │   ├── test_recommendation_schema.py
│   │   └── test_visualization_schema.py
│   ├── integration/              # Integration tests
│   │   ├── test_api_calls.py
│   │   ├── test_usgs_api.py
│   │   ├── test_climate_risk.py
│   │   ├── test_recommendations.py
│   │   └── test_gis_visualization.py
│   └── unit/                     # Unit tests
│       └── test_models.py
├── data/                         # Data storage
│   ├── raw/                      # Raw downloaded data
│   └── results/                  # Processed results
├── contracts/                    # Data contracts
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
├── docs/                         # Documentation
├── paper/                        # Research outputs
│   └── figures/
├── code/                         # Scripts for execution
│   └── scripts/
├── requirements.txt              # Python dependencies
├── quickstart.md                 # Quick start guide
├── research.md                   # Research citations
├── plan.md                       # Implementation plan
├── spec.md                       # User stories specification
├── tasks.md                      # Task tracking (this file)
└── README.md                     # This file
```

---

## 🚀 Installation

### Prerequisites

- Python 3.11+
- pip package manager
- API keys (see Configuration section)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd projects/<PROJ-ID>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure linting and formatting
pip install black flake8 isort pytest

# Run validation
python src/cli/validate.py
```

### Requirements

```
pandas>=2.0.0
geopandas>=0.13.0
rasterio>=1.3.0
scikit-learn>=1.3.0
matplotlib>=3.8.0
requests>=2.31.0
pytest>=7.4.0
```

---

## ⚙️ Configuration

### Environment Variables

Set the following environment variables before running:

```bash
# API Keys
export OPENWEATHERMAP_API_KEY="your_api_key"
export USGS_API_KEY="your_api_key"

# Paths
export PROJECT_ROOT="projects/<PROJ-ID>"
export DATA_DIR="data/raw"
```

### Validation

Run the validation script to verify configuration:

```bash
python src/cli/validate.py
```

This checks:
- API key availability
- Disk space requirements
- File existence
- Configuration compliance

---

## 📊 Usage

### Data Collection

```bash
# Collect survey data
python -m src.data.collectors.survey_collector

# Collect climate data
python -m src.data.collectors.climate_collector

# Collect remote sensing data
python -m src.data.collectors.remote_sensing_collector
```

### Climate Risk Assessment

```bash
# Run risk assessment
python -m src.models.climate_risk

# Generate risk maps
python -m src.services.gis_mapper
```

### Generate Recommendations

```bash
# Run recommendation engine
python -m src.services.recommendation_engine
```

### Visualizations & Reports

```bash
# Generate visualizations
python -m src.services.visualization

# Generate reports
python -m src.services.report_generator
```

---

## ✅ Testing

### Run All Tests

```bash
pytest tests/ -v --tb=short
```

### Run by User Story

```bash
# US1 tests
pytest tests/contract/test_dataset_schema.py tests/integration/test_api_calls.py tests/integration/test_usgs_api.py -v

# US2 tests
pytest tests/contract/test_risk_schema.py tests/integration/test_climate_risk.py -v

# US3 tests
pytest tests/contract/test_recommendation_schema.py tests/integration/test_recommendations.py -v

# US4 tests
pytest tests/contract/test_visualization_schema.py tests/integration/test_gis_visualization.py -v
```

### Contract Tests

Contract tests verify schema compliance for all data and output artifacts:

```bash
pytest tests/contract/ -v
```

---

## 🔧 Development

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Sort imports
isort src/ tests/
```

### Docker Support

```bash
# Build Docker image
docker-compose build

# Run in container
docker-compose up
```

---

## 📚 Research & Citations

See [research.md](research.md) for primary source citations and methodology documentation.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests before implementation
4. Run all tests before committing
5. Submit a pull request

### Task Tracking

Tasks are tracked in [tasks.md](tasks.md). Each task follows the format:
`[ID] [P?] [Story] Description`

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📞 Support

For issues and questions:
- Open an issue on the repository
- Check the [docs/](docs/) directory for documentation
- Review the [quickstart.md](quickstart.md) for troubleshooting

---

## 🏆 Achievement Status

| Component | Status |
|-----------|--------|
| Project Setup | ✅ Complete |
| Foundation Infrastructure | ✅ Complete |
| User Story 1 (Data) | ✅ Complete |
| User Story 2 (Risk) | ✅ Complete |
| User Story 3 (Recommendations) | ✅ Complete |
| User Story 4 (Visualization) | ✅ Complete |
| Tests | ✅ Complete |
| Documentation | ✅ Complete |
| Docker Support | ✅ Complete |

**Project Stage**: research_complete

---

*Last Updated: 2025*
