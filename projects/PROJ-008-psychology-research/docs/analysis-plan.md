# Analysis Plan: Mindfulness and Social Skills in Children with ASD

## 1. Study Overview

### 1.1 Research Question
Does a mindfulness-based intervention improve social skills in children with Autism Spectrum Disorder (ASD) compared to standard care?

### 1.2 Study Design
- **Type**: Randomized Controlled Trial (RCT)
- **Arms**: Intervention (mindfulness-based) vs. Control (standard care)
- **Sample Size**: 60 participants (30 per arm)
- **Timepoints**: Pre-intervention (T0), Post-intervention (T1), Follow-up (T2)

### 1.3 Intervention Protocol
- **Duration**: 8 sessions (per T004 resolution)
- **Frequency**: Weekly
- **Setting**: Individual or small group sessions
- **Adherence Tracking**: Session logs per `contracts/intervention.schema.yaml`

## 2. Primary Outcomes

### 2.1 Social Skills Assessment
- **Measure**: Social Skills Improvement System (SSIS) Rating Scale
- **Timepoints**: T0, T1, T2
- **Scoring**: Standardized T-scores (mean=50, SD=10)

### 2.2 Mindfulness Engagement
- **Measure**: Child Mindfulness Scale (CMS)
- **Timepoints**: T0, T1, T2

## 3. Secondary Outcomes

- Anxiety levels (SCARED scale)
- Parent-reported behavioral changes (CBCL)
- Session adherence metrics
- Quality of life measures (PedsQL)

## 4. Statistical Analysis

### 4.1 Primary Analysis
- **Method**: Mixed-effects ANOVA (repeated measures)
- **Factors**: Time (3 levels), Group (2 levels), Time × Group interaction
- **Software**: Python (scipy, pingouin, statsmodels)
- **Significance Level**: α = 0.05 (two-tailed)

### 4.2 Secondary Analysis
- **Between-group comparisons**: Independent samples t-tests at T1 and T2
- **Within-group changes**: Paired t-tests (T0→T1, T0→T2)
- **Effect Sizes**: Cohen's d, partial eta-squared (η²)
- **Confidence Intervals**: 95% CI for all effect estimates

### 4.3 Missing Data Handling
- **Approach**: Multiple Imputation by Chained Equations (MICE)
- **Threshold**: Participants with >50% missing data excluded from primary analysis
- **Sensitivity**: Complete-case analysis as sensitivity check

### 4.4 Assumption Checks
- **Normality**: Shapiro-Wilk test on residuals
- **Homogeneity**: Levene's test for equality of variances
- **Sphericity**: Mauchly's test (with Greenhouse-Geisser correction if violated)

## 5. Data Processing Pipeline

```
Raw Data (data/raw/) → Validation (src/lib/validators.py) → 
Processed Data (data/processed/) → Analysis (src/services/analysis.py)
```

### 5.1 Data Validation
- Schema compliance per `contracts/*.schema.yaml`
- Range checks for all numeric variables
- Missing value identification and logging

### 5.2 Data Preparation
- Participant anonymization (HIPAA-compliant)
- Timepoint alignment (T0, T1, T2)
- Outlier detection (IQR method, ±3 SD)

## 6. Power Analysis

### 6.1 Sample Size Justification
- **Effect Size**: Medium (d = 0.5) based on prior mindfulness studies in ASD
- **Power**: 80% (1-β = 0.80)
- **α Level**: 0.05
- **Attrition Rate**: 20% (60 recruited → 48 analyzable)
- **Software**: G*Power 3.1 (for initial calculation)

## 7. Subgroup Analyses

- Age groups (5-8 vs. 9-12 years)
- Baseline severity (mild vs. moderate ASD)
- Gender differences (if N permits)
- **Note**: All subgroup analyses exploratory; no adjustment for multiple comparisons

## 8. Reporting Standards

### 8.1 Documentation
- **CONSORT Flow Diagram**: Participant recruitment and retention
- **Baseline Table**: Demographics and baseline characteristics
- **Results Table**: Primary and secondary outcomes with effect sizes
- **Adverse Events**: Any unintended consequences documented

### 8.2 Output Format
- **Primary**: Markdown report (docs/analysis-plan.md)
- **Supplementary**: Statistical code repository (src/services/analysis.py)
- **Data**: Processed datasets (data/processed/) with schema validation

## 9. Quality Assurance

- **Code Review**: All analysis scripts peer-reviewed
- **Reproducibility**: Random seeds set for all stochastic processes
- **Version Control**: Git-tracked analysis pipeline
- **Validation**: Unit tests per `tests/unit/test_analysis.py`

## 10. Timeline

| Phase | Activity | Duration |
|-------|----------|----------|
| Data Collection | Participant enrollment & assessments | Weeks 1-24 |
| Data Cleaning | Validation & processing | Weeks 25-26 |
| Primary Analysis | Mixed-effects ANOVA | Week 27 |
| Secondary Analysis | Subgroup & sensitivity analyses | Weeks 28-29 |
| Reporting | Drafting & validation | Weeks 30-32 |

## 11. Approval & Sign-off

This analysis plan requires approval from:
- [ ] Principal Investigator
- [ ] IRB Committee
- [ ] Statistical Consultant

**Last Updated**: 2025-01-XX
**Version**: 1.0