# SGPGIMS Exam Results Analysis

Exam results analysis for SGPGIMS recruitment (Advt I/08/1-12/Rectt/2025-26). Extracts raw scores from PDFs, ranks candidates, computes percentiles, and generates interactive HTML visualizations.

## Directory Structure

```
├── index.html                  Landing page with all positions
├── extract_all.py              Script to parse PDFs and generate output
├── analysis/
│   ├── combined/               HTML pages — all exam days merged per position
│   └── per_day/                HTML pages — individual exam days per position
├── data/
│   ├── combined/               CSVs — all exam days merged per position
│   └── per_day/                CSVs — individual exam days per position
└── raw/                        PDFs (gitignored — contains personal data)
```

## Usage

Open **`index.html`** in a browser to view the landing page. Click any position card to see its analysis (charts, rankings, candidate search).

## Adding New Exam Data

1. Drop the PDF into `raw/`
2. Add an entry to the `pdfs` list in `extract_all.py`:
   ```python
   (r"raw/Your_New_File.pdf", "Day 3 (1 Jan 2026)", "1 Jan 2026"),
   ```
3. Run `python extract_all.py`
4. Commit the generated files
