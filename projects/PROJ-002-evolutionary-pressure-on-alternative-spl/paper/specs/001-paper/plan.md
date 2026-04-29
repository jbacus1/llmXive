# Implementation Plan: Evolutionary Pressure on Alternative Splicing in Comparative Genomics

**Branch**: `paper-evolutionary-pressure-alternative-splicing` | **Date**: 2024-01-15 | **Spec**: `/specs/paper-evolutionary-pressure-alternative-splicing/spec.md`
**Input**: Feature specification from `spec.md`, Paper Constitution `PROJ-002-evolutionary-pressure-on-alternative-spl`

## Summary

Reproduce splicing quantification pipeline (STAR v2.7.10a, rMATS v4.1.2) on SRA-derived RNA-seq data across primate species to analyze evolutionary pressure. Document methods for reproducibility, generate 5 required figures from real data, and produce a LaTeX manuscript compliant with the Paper Constitution.

## Technical Context

**Language/Version**: LaTeX (TeX Live 2023)  
**Primary Dependencies**: `arxiv-style` (LaTeX class), `biblatex`, `graphicx`, `matplotlib==3.7.0`, `seaborn==0.12.2`  
**Storage**: `data/` (CSV/JSON artifacts, STAR logs), `paper/source/` (LaTeX)  
**Testing**: `pdflatex` build gate, `check_figures.py` (checksum verification)  
**Target Platform**: PDF (arXiv/Nature style)  
**Project Type**: Scientific Manuscript  
**Performance Goals**: Compile time < 2 mins on standard runner; Figure generation < 10 mins  
**Constraints**: < 64GB memory per alignment job; Reproducibility within 0.1% variance  
**Scale/Scope**: 5 Figures, 6 Sections, 1 Primary Pipeline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
|-----------|--------|-----------------|
| I. Writing Quality | PASS | Proofreader-Agent to flag violations; Plan includes structure to avoid repetition. |
| II. Figure Quality | PASS | All 5 figures bound to `data/` sources; Scripts in `scripts/figures/`. |
| III. Citation Verification | PASS | Bibliography schema enforces `verification_status=verified` from research stage. |
| IV. Statistical Interpretation | PASS | Results section template requires test, statistic, p-value per claim. |
| V. Reproducibility | PASS | `pdflatex` build gate enforced; Tool versions pinned in Methods. |
| VI. Jargon Discipline | PASS | Acronyms expanded on first use; Gene symbols follow HGNC. |
| VII. Genomic Coordinate Consistency | PASS | All coordinates pinned to GRCh38/hg38 per Constitution Principle VII. |
| VIII. Bioinformatics Pipeline Transparency | PASS | STAR/rMATS versions and seeds documented in Methods. |

## Project Structure

### Documentation (this feature)

```text
paper/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── figure-data.schema.yaml
│   └── bibliography.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
paper/
├── source/
│   ├── main.tex         # Main manuscript
│   ├── sections/        # Abstract, Intro, Methods, Results, Discussion
│   ├── figures/         # Generated figures (PNG/PDF)
│   └── refs.bib         # Bibliography (verified)
├── data/
│   ├── alignment_stats.csv
│   ├── splicing_events.csv
│   └── orthology_map.json
├── scripts/
│   ├── figures/         # Python scripts for Figure 1-5
│   └── pipeline/        # Pipeline wrappers (STAR/rMATS)
└── requirements.txt     # Python & LaTeX dependencies
```

**Structure Decision**: Standard scientific manuscript structure (`source/`, `data/`, `scripts/`) to separate content generation from data processing. Aligns with Constitution Principle V (LaTeX Build Gate).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |
