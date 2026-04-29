# Data Security Policy

## Overview

This document defines the security requirements for handling IRB-protected research data
in the Mindfulness and Social Skills in Children with ASD study.

## Compliance Requirements

- **IRB Protocol**: All data access must comply with approved IRB protocol
- **HIPAA**: Protected health information (PHI) handling requirements
- **Institutional**: Follow Dartmouth/Human Research Protection Program guidelines

## Data Classification

| Level | Description | Examples | Access |
|-------|-------------|----------|--------|
| Public | Non-sensitive | Aggregated results | All team members |
| Internal | Research data | Processed datasets | Principal investigators only |
| Restricted | PHI/PII | Raw participant data | Authorized personnel only |

## Directory Structure & Permissions

```
data/
├── raw/           # 750 (owner: rwx, group: rx, others: none) - HIPAA raw data
├── processed/     # 750 - De-identified processed data
└── temp/          # 750 - Temporary files (auto-cleaned)
```

## Permission Enforcement

Run the following script after repository clone:

```bash
./scripts/set_data_permissions.sh
```

## Audit Requirements

- All data access must be logged
- Quarterly permission audits required
- Access requests must be documented in IRB portal

## Breach Response

1. Immediately revoke access
2. Document incident within 24 hours
3. Notify IRB within 72 hours
4. Complete corrective action plan

## Contact

- Data Security Officer: [REDACTED]
- IRB Administrator: [REDACTED]
