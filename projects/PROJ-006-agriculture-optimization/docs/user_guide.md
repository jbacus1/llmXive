# User Guide

This guide explains how to use the Climate-Smart Agricultural Practices system.

## Prerequisites

- Python 3.11+
- Required API keys (OpenWeatherMap, USGS EarthExplorer)
- Sufficient disk space for data storage

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API keys in environment variables:
```bash
export OPENWEATHERMAP_API_KEY=your_key
export USGS_API_KEY=your_key
```

3. Run validation:
```bash
python -m src.cli.validate
```

## Data Collection (US1)

The system collects data from multiple sources:

- **Survey Data**: Community agricultural surveys
- **Climate Data**: Weather and climate information from OpenWeatherMap
- **Remote Sensing**: Satellite imagery from USGS EarthExplorer

Run collectors:
```bash
python -m src.data.collectors.survey_collector
python -m src.data.collectors.climate_collector
python -m src.data.collectors.remote_sensing_collector
```

## Climate Risk Assessment (US2)

After data collection, run risk assessment:
```bash
python -m src.models.climate_risk
```

Output includes:
- Risk scores by region
- Historical climate pattern analysis
- Yield prediction models

## CSA Recommendations (US3)

Generate recommendations for communities:
```bash
python -m src.services.recommendation_engine
```

## Visualization & Reporting (US4)

Generate visualizations and reports:
```bash
python -m src.services.visualization
python -m src.services.report_generator
```

## Data Storage

All data is stored in the `data/` directory:
- `data/raw/` - Original downloaded data
- `data/processed/` - Cleaned and validated data
- `data/cache/` - Cached API responses

## Troubleshooting

- **API Key Errors**: Verify environment variables are set correctly
- **Disk Space**: Check available space in data directory
- **Schema Validation**: Ensure input data matches expected schemas
