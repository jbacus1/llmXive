# Reproducibility Audit Trail

This directory contains reproducibility audit trails for the Evolutionary Pressure on Alternative Splicing in Primates project.

## Purpose

The audit trail ensures that all research outputs can be:
- Reproduced using the same code and data
- Validated against known benchmarks
- Tracked for version control and compliance

## Contents

- `audit_*.json`: Individual audit entries for each pipeline execution
- `audit_template.json`: Template structure for new audit entries
- `dependencies_snapshot.txt`: Frozen Python dependencies at time of execution
- `README.md`: This documentation file

## Audit Entry Structure

Each audit entry contains:
1. **Git Information**: Commit hash, branch, dirty status
2. **Environment**: Python version, platform, dependencies
3. **Pipeline Execution**: Task ID, user story, timestamps, status
4. **Random Seeds**: All random seeds used for reproducibility
5. **Data Checksums**: SHA256 hashes of input/output data
6. **Config Snapshot**: Path to configuration snapshot
7. **Notes**: Optional contextual information

## Usage

Audit entries are automatically created by the pipeline when running:
- Data acquisition (US1)
- Splicing quantification (US2)
- Selection analysis (US3)

Each execution generates a timestamped audit file for traceability.

## Compliance

This audit trail supports compliance with:
- FAIR data principles (Findable, Accessible, Interoperable, Reusable)
- Scientific reproducibility standards
- Institutional review requirements for computational research