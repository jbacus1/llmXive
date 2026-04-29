# Data Documentation

## Data Sources

### Survey Data

**Source**: Community agricultural surveys
**Format**: CSV
**Schema**: `contracts/dataset.schema.yaml`

**Fields**:
- `community_id` - Unique community identifier
- `crop_type` - Primary crop grown
- `yield_per_hectare` - Historical yield
- `water_access` - Water availability score
- `soil_quality` - Soil quality rating

### Climate Data

**Source**: OpenWeatherMap API
**Format**: JSON
**Update Frequency**: Hourly

**Fields**:
- `timestamp` - Observation time
- `temperature` - Temperature in Celsius
- `precipitation` - Rainfall in mm
- `humidity` - Relative humidity %
- `wind_speed` - Wind speed in m/s

### Remote Sensing Data

**Source**: USGS EarthExplorer
**Format**: GeoTIFF
**Update Frequency**: Varies by satellite

**Fields**:
- `satellite` - Satellite source
- `acquisition_date` - Image capture date
- `resolution` - Spatial resolution
- `bands` - Spectral bands available

## Data Storage Structure

```
data/
├── raw/                    # Original downloaded data
│   ├── survey/
│   ├── climate/
│   └── remote_sensing/
├── processed/              # Cleaned and validated data
│   ├── survey/
│   ├── climate/
│   └── remote_sensing/
├── cache/                  # Cached API responses
│   └── sqlite.db
└── outputs/                # Generated reports and visualizations
```

## Data Validation

All data passes through schema validation:
- Input validation at collector level
- Contract tests for schema compliance
- Automated validation in preprocessing pipeline

## Data Privacy

- No personally identifiable information stored
- Community-level aggregation only
- Compliant with data protection regulations

## Data Quality

- Automated quality checks on ingestion
- Missing value handling documented
- Outlier detection and reporting
