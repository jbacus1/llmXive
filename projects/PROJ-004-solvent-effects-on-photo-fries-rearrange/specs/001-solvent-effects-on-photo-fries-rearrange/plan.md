# Implementation Plan: Solvent Effects on Photo-Fries Rearrangement Kinetics

**Branch**: `001-solvent-effects` | **Date**: 2024-05-21 | **Spec**: `specs/001-solvent-effects/spec.md`
**Input**: Feature specification from `specs/001-solvent-effects/spec.md`

## Summary

This feature enables systematic investigation of solvent effects on Photo-Fries rearrangement kinetics by configuring solvent series, capturing transient-absorption spectroscopy data, extracting radical-pair lifetimes via global kinetic analysis, and correlating experimental lifetimes with computed solvation free energies. The technical approach combines laser flash photolysis instrumentation control with DFT-based computational chemistry (B3LYP/6-31G*, SMD/PCM implicit solvent models).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: numpy, scipy, pandas, scikit-learn, pymatgen, ase, openbabel, pyyaml, pytest  
**Storage**: SQLite (experimental metadata), local filesystem (raw instrument data, computational input/output files)  
**Testing**: pytest with contract validation via YAML schemas  
**Target Platform**: Linux server (laser flash photolysis instrument interface + DFT compute cluster)  
**Project Type**: computational-experimental research pipeline  
**Performance Goals**: Global kinetic analysis completes within 5 minutes per solvent condition; DFT solvation energy computation within 24 hours per solvent  
**Constraints**: Temperature control maintained at 25 ± 0.5°C; solvent dielectric constant range ε ≈ 2 to ε ≈ 33; n ≥ 3 replicates per condition for statistical significance  
**Scale/Scope**: 5+ solvent conditions, each with n ≥ 3 replicates, generating kinetic traces and lifetime metrics for correlation analysis

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | PASS | All code in `code/`, data in `data/`; random seeds pinned; external datasets fetched from canonical sources |
| **II. Verified Accuracy** | PASS | All citations from spec.md (arxiv URLs) will be verified by Reference-Validator; title-token-overlap ≥ 0.7 required |
| **III. Data Hygiene** | PASS | All files under `data/` checksummed in `state/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange.yaml`; no in-place modifications |
| **IV. Single Source of Truth** | PASS | All figures/statistics trace to `data/` rows and `code/` blocks; no hand-typed numbers in paper |
| **V. Versioning Discipline** | PASS | Content hashes for all artifacts; `state/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange.yaml` updated on changes |
| **VI. Computational-Experimental Consistency** | PASS | DFT solvation energies (kcal/mol) and laser flash photolysis kinetics (ns) use standardized units; deviations documented in `docs/deviation_analysis.md` |
| **VII. Chemical Provenance & Purity** | PASS | All reagents/solvents logged in `data/chemicals/` with manufacturer, lot number, purity certificate; substitutions require verification |

## Project Structure

### Documentation (this feature)

```text
specs/001-solvent-effects/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── solvent_config.py
│   ├── kinetic_analysis.py
│   ├── dft_solvation.py
│   ├── correlation_analysis.py
│   └── tests/
│       ├── __init__.py
│       ├── test_solvent_config.py
│       ├── test_kinetic_analysis.py
│       ├── test_dft_solvation.py
│       └── test_correlation_analysis.py
├── data/
│   ├── raw/
│   │   └── laser_flash_photolysis/
│   │       └── [solvent_name]/
│   │           └── [run_id].csv
│   ├── compute/
│   │   └── dft_inputs/
│   │       └── [solvent_name].com
│   ├── chemicals/
│   │   └── solvent_registry.yaml
│   └── processed/
│       ├── lifetimes.csv
│       └── solvation_energies.csv
├── docs/
│   ├── deviation_analysis.md
│   └── chemical_provenance.md
└── state/
    └── projects/PROJ-004-solvent-effects-on-photo-fries-rearrange.yaml
```

**Structure Decision**: Single project structure (Option 1) selected. This is a computational-experimental research pipeline where code, data, and documentation coexist in a unified repository structure. The `code/` directory contains analysis scripts and instrumentation interfaces; `data/` is hierarchically organized by data type (raw, compute, chemicals, processed); `docs/` contains deviation analysis and chemical provenance records; `state/` maintains project metadata and artifact hashes.

## Complexity Tracking

> No violations detected in Constitution Check; Complexity Tracking section not required.
