# Data Model: Climate-Smart Agricultural Practices

**Project**: agriculture-20250704-001  
**Date**: 2026-04-28  
**Version**: 1.0.0

## Overview

This document defines the data models for the climate-smart agriculture analysis pipeline. All data structures are validated against schemas in `contracts/` directory.

## Entity Relationship Diagram

```
┌─────────────────────┐       ┌─────────────────────┐
│   Site            │ 1───n │   Observation      │
│   (Location)      │       │   (Field Measurement)│
└─────────┬─────────┘       └─────────┬───────────┘
          │                           │
          │                           │
          ▼                           ▼
┌─────────────────────┐       ┌─────────────────────┐
│   ClimateRecord   │       │   PracticeRecord    │
│   (Weather Data)  │       │   (CSA Practice)    │
└─────────────────────┘       └─────────────────────┘
          │                           │
          └───────────┬───────────────┘
                      │
                      ▼
              ┌─────────────────────┐
              │   YieldRecord      │
              │   (Crop Output)    │
              └─────────────────────┘
```

## Core Entities

### Site

Represents a geographic location where agricultural data is collected.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| site_id | string | Yes | Unique identifier (UUID) |
| name | string | Yes | Human-readable name |
| latitude | float | Yes | WGS84 latitude (-90 to 90) |
| longitude | float | Yes | WGS84 longitude (-180 to 180) |
| elevation | float | No | Elevation in meters above sea level |
| country | string | Yes | ISO 3166-1 alpha-3 country code |
| region | string | No | Administrative region |
| land_use | string | Yes | Primary land use classification |
| created_at | datetime | Yes | Record creation timestamp |

### Observation

Field measurements collected at a site.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| observation_id | string | Yes | Unique identifier (UUID) |
| site_id | string | Yes | Foreign key to Site |
| observation_date | date | Yes | Date of observation |
| soil_ph | float | No | Soil pH value (0-14) |
| soil_organic_carbon | float | No | SOC percentage |
| moisture_content | float | No | Soil moisture percentage |
| temperature | float | No | Air temperature (°C) |
| precipitation | float | No | Precipitation (mm) |
| notes | string | No | Free-text observations |

### ClimateRecord

Aggregated climate data from remote sources.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| record_id | string | Yes | Unique identifier (UUID) |
| site_id | string | Yes | Foreign key to Site |
| period_start | date | Yes | Start of climate period |
| period_end | date | Yes | End of climate period |
| avg_temperature | float | Yes | Average temperature (°C) |
| max_temperature | float | Yes | Maximum temperature (°C) |
| min_temperature | float | Yes | Minimum temperature (°C) |
| total_precipitation | float | Yes | Total precipitation (mm) |
| extreme_event_count | integer | Yes | Count of extreme weather events |
| source | string | Yes | Data source (e.g., "WorldClim", "CHIRPS") |

### PracticeRecord

Climate-smart agricultural practice implementation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| practice_id | string | Yes | Unique identifier (UUID) |
| site_id | string | Yes | Foreign key to Site |
| practice_type | string | Yes | Type of practice (see below) |
| implementation_date | date | Yes | Date practice was implemented |
| area_hectares | float | Yes | Area under practice (ha) |
| cost_usd | float | No | Implementation cost |
| expected_yield_change | float | No | Expected yield change percentage |
| actual_yield_change | float | No | Actual yield change percentage |
| status | string | Yes | Status (planned, active, completed) |

**Practice Type Values**:
- `conservation_tillage`
- `cover_cropping`
- `crop_rotation`
- `agroforestry`
- `improved_varieties`
- `irrigation_efficiency`
- `integrated_pest_management`

### YieldRecord

Crop yield measurements.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| yield_id | string | Yes | Unique identifier (UUID) |
| site_id | string | Yes | Foreign key to Site |
| crop_type | string | Yes | Crop type (see below) |
| harvest_date | date | Yes | Date of harvest |
| area_harvested | float | Yes | Area harvested (ha) |
| total_yield_kg | float | Yes | Total yield (kg) |
| yield_per_ha | float | Yes | Yield per hectare (kg/ha) |
| quality_grade | string | No | Quality classification |

**Crop Type Values**:
- `maize`
- `wheat`
- `rice`
- `sorghum`
- `millet`
- `cassava`
- `sweet_potato`
- `beans`
- `groundnut`
- `other`

## Derived Models

### VulnerabilityIndex

Calculated climate vulnerability for a site.

| Field | Type | Description |
|-------|------|-------------|
| site_id | string | Foreign key to Site |
| exposure_score | float | Climate hazard exposure (0-1) |
| sensitivity_score | float | System sensitivity (0-1) |
| adaptive_capacity | float | Adaptive capacity (0-1) |
| vulnerability_score | float | Overall vulnerability (0-1) |
| calculation_date | datetime | When index was calculated |

### AdoptionRecommendation

Recommended CSA practices for a site.

| Field | Type | Description |
|-------|------|-------------|
| recommendation_id | string | Unique identifier |
| site_id | string | Foreign key to Site |
| practice_type | string | Recommended practice |
| priority_rank | integer | Priority order (1=highest) |
| expected_benefit | float | Expected benefit score |
| implementation_cost | float | Estimated cost (USD) |
| complexity_level | string | Low, Medium, High |
| confidence_score | float | Recommendation confidence (0-1) |

## Data Flow

```
Raw Data Sources
    │
    ├── Remote Sensing (GeoTIFF)
    ├── Survey Data (CSV)
    └── Climate APIs (JSON)
    │
    ▼
Validation Layer (contracts/*.schema.yaml)
    │
    ▼
Cleaned Data (data/processed/)
    │
    ▼
Analysis Models (src/models/)
    │
    ▼
Output Reports (docs/reports/)
```

## Validation Rules

1. **Geographic Bounds**: Latitude must be -90 to 90; longitude must be -180 to 180
2. **Date Consistency**: period_end must be >= period_start
3. **Numeric Ranges**: Soil pH 0-14; temperature values must be physically plausible
4. **Foreign Key Integrity**: All site_id references must exist in Site table
5. **Enum Values**: Practice types and crop types must match defined lists
