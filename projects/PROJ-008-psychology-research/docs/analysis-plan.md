# Analysis Plan: Mindfulness and Social Skills in Children with ASD

## Document Information
- **Version**: 1.0.0
- **Date**: 2025-01-15
- **Study Type**: Randomized Controlled Trial (RCT)
- **Participants**: N=60 children with ASD (30 intervention, 30 control)

## 1. Statistical Analysis Framework

### 1.1 Primary Analysis Approach
- **Software**: Python 3.11 with scipy, pingouin, pandas
- **Significance Level**: α = 0.05 (two-tailed)
- **Effect Size Metrics**: Cohen's d, partial η²

### 1.2 Data Preparation
```python
# Pseudocode for data loading and validation
from src.models.data_models import Participant, Assessment
from src.lib.validators import validate_assessment

# Load processed data
data = load_from_csv('data/processed/assessments.csv')
validated = [validate_assessment(row) for row in data]
```

### 2. Primary Outcome Measures

### 2.1 Social Skills Assessment (SSA)
| Timepoint | Description | Analysis Method |
|-----------|-------------|-----------------|
| T0 (Baseline) | Pre-intervention | - |
| T1 (Post-intervention) | After 8-12 sessions | Paired t-test vs T0 |
| T2 (Follow-up) | 3 months post | ANOVA (T0, T1, T2) |

### 2.2 Statistical Tests
- **Within-group changes**: Paired t-tests (T0 vs T1, T1 vs T2)
- **Between-group differences**: Independent t-tests at each timepoint
- **Time × Group interaction**: Repeated measures ANOVA
- **Effect size calculation**: Cohen's d for t-tests, partial η² for ANOVA

## 3. Secondary Outcome Measures

### 3.1 Mindfulness Questionnaires
- Child Mindfulness Scale (CMS)
- Parent-Report Mindfulness Index (PRMI)
- Analysis: Same as primary outcomes

### 3.2 Adherence Metrics
- Session attendance rate (%)
- Intervention fidelity scores
- Analysis: Descriptive statistics + correlation with outcomes

## 4. Missing Data Handling

- **Threshold**: <20% missing data per participant
- **Method**: Multiple imputation (MICE) if needed
- **Reporting**: Document missing data patterns in final report

## 5. Report Generation Specifications

### 5.1 Output Formats
- **Markdown**: For version control and web display
- **PDF**: For IRB submission and publication

### 5.2 Report Structure
```
1. Executive Summary
2. Participant Demographics
3. Primary Outcome Results
4. Secondary Outcome Results
5. Adherence Analysis
6. Limitations
7. Conclusions
```

### 5.3 Code Implementation
```python
# src/services/analysis.py (report generation)
def generate_report(results: dict, output_path: str, format: str = 'markdown'):
    """
    Generate analysis report from statistical results.
    
    Args:
        results: Dict containing t-test, ANOVA, and effect size results
        output_path: Where to save the report
        format: 'markdown' or 'pdf'
    """
    # Implementation in src/services/analysis.py
    pass
```

## 6. Quality Assurance

- **Validation**: All statistical outputs validated against synthetic test data
- **Reproducibility**: Random seeds set for all stochastic operations
- **Audit Trail**: All analysis steps logged with timestamps

## 7. Compliance Notes

- All participant identifiers removed from analysis datasets
- IRB approval number referenced in all final reports
- Data retention policy: 7 years post-study completion

---
*This analysis plan aligns with the intervention protocol defined in docs/protocol.md*
*Last updated: 2025-01-15*