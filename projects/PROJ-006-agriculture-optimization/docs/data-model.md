# Data Model Documentation

**Project**: Climate-Smart Agricultural Practices for Food Security
**Version**: 1.0.0
**Last Updated**: 2025-07-04

## Overview

This document describes the data models used throughout the Climate-Smart Agricultural (CSA) system. The data model supports collection, processing, analysis, and visualization of agricultural, climate, and socioeconomic data from multiple sources.

## Data Sources

### External APIs
- **OpenWeatherMap**: Climate data (temperature, precipitation, humidity)
- **USGS EarthExplorer**: Remote sensing data (satellite imagery, elevation)
- **Survey Data**: Community-level agricultural practices and socioeconomic indicators

### Internal Storage
- **Raw Data**: `data/raw/` - Original downloaded data with metadata
- **Processed Data**: `data/processed/` - Cleaned and transformed data
- **Cache**: `data/cache/` - SQLite-based caching layer

## Core Entities

### Dataset

A collection of related data records with shared schema and metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique dataset identifier |
| name | string | Yes | Human-readable dataset name |
| source | string | Yes | Origin of the data (API name or collection method) |
| category | string | Yes | One of: climate, agricultural, socioeconomic, remote_sensing |
| created_at | datetime | Yes | Timestamp of dataset creation |
| updated_at | datetime | Yes | Last modification timestamp |
| version | string | Yes | Semantic version of dataset schema |
| record_count | integer | Yes | Number of records in dataset |
| checksum | string | Yes | SHA-256 hash for integrity verification |
| metadata | object | Yes | Additional source-specific metadata |

### Climate Record

Individual climate observation from weather stations or APIs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique record identifier |
| location_id | string | Yes | Geographic location reference |
| timestamp | datetime | Yes | Observation timestamp (UTC) |
| temperature_avg | float | No | Average temperature (°C) |
| temperature_max | float | No | Maximum temperature (°C) |
| temperature_min | float | No | Minimum temperature (°C) |
| precipitation | float | No | Total precipitation (mm) |
| humidity | float | No | Relative humidity (%) |
| wind_speed | float | No | Wind speed (m/s) |
| data_quality | string | No | Quality flag: verified, estimated, missing |

### Agricultural Record

Farm-level agricultural data including crops, yields, and practices.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique record identifier |
| farm_id | string | Yes | Farm identifier |
| location_id | string | Yes | Geographic location reference |
| crop_type | string | Yes | Primary crop classification |
| planting_date | date | No | Date of planting |
| harvest_date | date | No | Date of harvest |
| yield_kg_per_ha | float | No | Yield in kg per hectare |
| area_hectares | float | Yes | Farm area in hectares |
| irrigation_method | string | No | Irrigation type |
| fertilizer_used | boolean | No | Whether fertilizer was applied |
| practices | array | No | List of CSA practices implemented |

### Socioeconomic Record

Community-level socioeconomic indicators.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique record identifier |
| community_id | string | Yes | Community identifier |
| population | integer | No | Total population |
| poverty_rate | float | No | Percentage below poverty line |
| education_level | string | No | Average education level |
| income_per_capita | float | No | Annual income per capita (USD) |
| food_security_index | float | No | Composite food security score (0-100) |
| data_year | integer | Yes | Year of data collection |

### Remote Sensing Record

Satellite imagery and derived data products.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique record identifier |
| location_id | string | Yes | Geographic location reference |
| acquisition_date | date | Yes | Satellite image acquisition date |
| sensor_type | string | Yes | Sensor platform (e.g., Landsat, Sentinel) |
| cloud_coverage | float | No | Percentage of cloud coverage |
| ndvi_mean | float | No | Mean Normalized Difference Vegetation Index |
| ndvi_std | float | No | Standard deviation of NDVI |
| evi_mean | float | No | Mean Enhanced Vegetation Index |
| elevation_m | float | No | Mean elevation (meters) |
| data_path | string | Yes | File path to raster data |

### Risk Assessment Record

Climate risk assessment results for locations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique record identifier |
| location_id | string | Yes | Geographic location reference |
| assessment_date | datetime | Yes | Date of risk assessment |
| drought_risk | float | Yes | Drought risk score (0-1) |
| flood_risk | float | Yes | Flood risk score (0-1) |
| heat_stress_risk | float | Yes | Heat stress risk score (0-1) |
| overall_risk | float | Yes | Composite risk score (0-1) |
| risk_category | string | Yes | One of: low, moderate, high, critical |
| contributing_factors | array | No | List of factors influencing risk |
| confidence_level | float | No | Model confidence (0-1) |

### Recommendation Record

CSA practice recommendations for communities.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique record identifier |
| community_id | string | Yes | Target community |
| generated_date | datetime | Yes | Recommendation generation date |
| practice_name | string | Yes | Name of recommended practice |
| practice_category | string | Yes | Category (soil, water, crop, integrated) |
| priority | string | Yes | Priority level: high, medium, low |
| expected_yield_impact | float | No | Expected yield change (%) |
| adoption_feasibility | float | No | Feasibility score (0-1) |
| cost_estimate_usd | float | No | Estimated implementation cost |
| justification | string | Yes | Rationale for recommendation |
| references | array | No | Supporting citations |

## Relationships

```
Location ────┬─── Climate Record
             ├─── Agricultural Record
             ├─── Remote Sensing Record
             └─── Risk Assessment Record

Community ───┬─── Socioeconomic Record
             └─── Recommendation Record

Farm ───────── Agricultural Record
```

## Data Validation

All datasets must conform to the schema defined in `contracts/dataset.schema.yaml`. Validation is performed:
1. On data ingestion (raw data)
2. Before processing (transformed data)
3. On output generation (analysis results)

## Schema Evolution

Schema changes follow semantic versioning:
- **MAJOR**: Breaking changes (require data migration)
- **MINOR**: New optional fields (backward compatible)
- **PATCH**: Bug fixes and clarifications

## References

- Dataset Schema: `contracts/dataset.schema.yaml`
- Output Schema: `contracts/output.schema.yaml`
- API Contracts: `contracts/api/`
