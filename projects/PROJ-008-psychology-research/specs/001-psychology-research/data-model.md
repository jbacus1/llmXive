# Data Model: Mindfulness and Social Skills Study

## Overview

This document defines the data structures used throughout the study lifecycle, including participant information, assessment data, intervention records, and analysis outputs. All data structures are validated against schemas in the `contracts/` directory.

## Entity Relationships

```
┌─────────────────┐
│  Participant    │──┐
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌─────────────────┐
│  Assessment     │──┼────│  Intervention   │
└─────────────────┘  │    └─────────────────┘
                     │
┌─────────────────┐  │
│  AnalysisResult │──┘
└─────────────────┘
```

## Participant Entity

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `participant_id` | string | Yes | Unique anonymized identifier (format: `ASD-XXXX`) |
| `age` | integer | Yes | Age in years (8-12) |
| `sex` | string | Yes | Male/Female/Other |
| `diagnosis_date` | date | Yes | Date of ASD diagnosis |
| `diagnosis_facility` | string | Yes | Facility that provided diagnosis |
| `group_assignment` | string | Yes | `intervention` or `control` |
| `consent_date` | date | Yes | Parent consent signature date |
| `assent_date` | date | Yes | Child assent signature date |
| `enrollment_date` | date | Yes | Study enrollment date |
| `status` | string | Yes | `active`, `completed`, `withdrawn`, `lost_to_followup` |

### Constraints

- `participant_id` must be unique across all participants
- `age` must be between 8 and 12 (inclusive)
- `group_assignment` must be randomly assigned (documented in randomization log)
- All date fields must be in ISO 8601 format (YYYY-MM-DD)

## Assessment Entity

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assessment_id` | string | Yes | Unique identifier (format: `ASSESS-XXXX-TN`) |
| `participant_id` | string | Yes | Foreign key to Participant |
| `timepoint` | string | Yes | `baseline`, `post_intervention`, `followup` |
| `assessment_date` | date | Yes | Date assessment was administered |
| `assessor_id` | string | Yes | Blinded assessor identifier |
| `srs_total` | float | No | SRS-2 Total T-score |
| `srs_social_communication` | float | No | SRS Social Communication subscale |
| `srs_social_motivation` | float | No | SRS Social Motivation subscale |
| `ssis_total` | float | No | SSIS Total Standard Score |
| `erc_regulation` | float | No | ERC Regulation subscale |
| `erc_negativity` | float | No | ERC Negativity subscale |
| `wm_score` | float | No | Working Memory task accuracy (%) |
| `notes` | string | No | Administrator notes |

### Constraints

- Each participant can have at most one assessment per timepoint
- `timepoint` values must be from the controlled vocabulary
- Numeric scores must be within validated range for each instrument
- Missing data represented as `null` (not 0 or -99)

## Intervention Entity

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | Unique identifier (format: `SESS-XXXX-N`) |
| `participant_id` | string | Yes | Foreign key to Participant |
| `session_number` | integer | Yes | Session number (1-12) |
| `session_date` | date | Yes | Date session occurred |
| `facilitator_id` | string | Yes | Facilitator identifier |
| `duration_minutes` | integer | Yes | Actual session duration |
| `module_completed` | boolean | Yes | Whether module objectives were met |
| `attendance` | string | Yes | `present`, `absent`, `late`, `early_leave` |
| `homework_completed` | boolean | No | Whether homework was completed |
| `facilitator_notes` | string | No | Session notes |

### Constraints

- Sessions must be sequential (1-12)
- `duration_minutes` typically 30-35 minutes
- `module_completed` tracked for fidelity assessment

## Analysis Result Entity

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `analysis_id` | string | Yes | Unique identifier |
| `analysis_type` | string | Yes | `descriptive`, `anova`, `ttest`, `correlation` |
| `analysis_date` | date | Yes | Date analysis performed |
| `analyst_id` | string | Yes | Analyst identifier |
| `parameters` | object | Yes | Analysis parameters used |
| `results` | object | Yes | Primary results (statistics, p-values) |
| `effect_sizes` | object | No | Cohen's d, eta-squared, etc. |
| `confidence_intervals` | object | No | 95% CI for key estimates |
| `assumptions_checked` | object | Yes | Normality, homogeneity checks |
| `raw_output_path` | string | Yes | Path to raw analysis output |

## Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Raw Data    │───▶│  Validation  │───▶│  Clean Data  │
│  (collection)│    │  (schema)    │    │  (analysis)  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  data/raw/   │    │  data/       │    │  data/       │
│  *.csv       │    │  validated/  │    │  processed/  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## File Storage Standards

| Data Type | Format | Location | Version Control |
|-----------|--------|----------|-----------------|
| Raw assessments | CSV | `data/raw/` | ❌ No (protected) |
| Clean datasets | CSV/Parquet | `data/processed/` | ❌ No |
| Schemas | YAML | `contracts/` | ✅ Yes |
| Analysis scripts | Python | `src/` | ✅ Yes |
| Configuration | JSON/YAML | `config/` | ✅ Yes |

## Privacy & Security

- All participant identifiers stored separately from assessment data
- Linking table encrypted and access-restricted
- Data de-identified for analysis (participant_id only)
- Backup encryption required for all stored data
- Access logs maintained for all data operations
