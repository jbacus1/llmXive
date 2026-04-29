# Quick Start Guide

Get up and running with the Climate-Smart Agricultural Practices system in 5 minutes.

## Step 1: Clone and Install

```bash
git clone <repository-url>
cd climate-smart-agriculture
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Set required API keys
export OPENWEATHERMAP_API_KEY=your_api_key_here
export USGS_API_KEY=your_api_key_here

# Validate configuration
python -m src.cli.validate
```

## Step 3: Run Data Collection

```bash
# Collect climate data
python -m src.data.collectors.climate_collector

# Collect survey data
python -m src.data.collectors.survey_collector

# Collect remote sensing data
python -m src.data.collectors.remote_sensing_collector
```

## Step 4: Run Risk Assessment

```bash
python -m src.models.climate_risk
```

## Step 5: Generate Recommendations

```bash
python -m src.services.recommendation_engine
```

## Step 6: Create Visualizations

```bash
python -m src.services.visualization
python -m src.services.report_generator
```

## Verify Installation

```bash
# Run all tests
pytest tests/ -v

# Run validation script
python -m src.cli.validate
```

## Next Steps

- Read the [User Guide](user_guide.md) for detailed usage
- Review the [Developer Guide](developer_guide.md) for contributing
- Check the [Architecture](architecture.md) for system design

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API key errors | Verify environment variables |
| Import errors | Reinstall requirements.txt |
| Disk space errors | Free up space in data directory |
| Test failures | Check Python version is 3.11+ |

## Support

For issues, open a GitHub issue with:
- Python version
- Error message
- Steps to reproduce