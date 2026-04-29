# Quickstart: Compiling the Paper

**Date**: 2024-01-15  
**Context**: Instructions for local compilation and figure regeneration.

## Prerequisites

1. **LaTeX Distribution**: TeX Live 2023 or equivalent (MiKTeX, MacTeX).
2. **Python Environment**: Python 3.10+ with `requirements.txt` installed.
3. **Data Access**: `data/` directory populated with checksummed artifacts from Research Stage.

## Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd projects/PROJ-002-evolutionary-pressure-on-alternative-spl/paper

# 2. Install Python dependencies for figures
pip install -r requirements.txt

# 3. Verify LaTeX installation
pdflatex --version
```

## Compilation Steps

1. **Generate Figures** (if not already present):
   ```bash
   python scripts/figures/generate_all.py --data-dir data/ --output-dir paper/source/figures/
   ```
   *Note: This script reads `data-model.md` bindings to ensure figures match source data.*

2. **Compile LaTeX**:
   ```bash
   cd paper/source
   pdflatex main.tex
   bibtex main
   pdflatex main.tex
   pdflatex main.tex
   ```

3. **Verify Build**:
   - Check `main.pdf` exists.
   - Check for no `! LaTeX Error` in console output.
   - Verify Figure captions reference `data/` files correctly.

## Troubleshooting

- **Missing Fonts**: Ensure TeX Live 2023 is fully installed.
- **Figure Errors**: Run `scripts/figures/generate_all.py` again to regenerate from `data/`.
- **Citation Warnings**: Check `state/citations/` for `verification_status=verified`.
