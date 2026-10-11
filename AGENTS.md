# Agent Instructions — Data Update Process

When asked to add new exam data or update the analysis with additional PDFs:

## Step 1: Locate the PDF

Find the new PDF file(s) in the `raw/` directory. If not there, move them into `raw/`.

## Step 2: Preview the PDF

Run a quick scan to see subjects and record count:

```python
python -c "
import fitz, re
doc = fitz.open(r'raw/FILENAME.pdf')
all_text = ''
for p in doc: all_text += p.get_text() + '\n'
subjects = {}
for m in re.findall(r'(SG\d+)\s+(\d+)\s+([-\d.]+)\s+(.+)', all_text):
    s = m[3].strip()
    subjects[s] = subjects.get(s, 0) + 1
for s, c in sorted(subjects.items(), key=lambda x: -x[1]):
    print(f'{s}: {c}')
print(f'Total: {sum(subjects.values())} records')
"
```

## Step 3: Add to `extract_all.py`

Locate the `pdfs` list (near top of the file) and append a new tuple:

```python
(r"raw/Your_File.pdf", "Day 3 (1 Jan 2026)", "1 Jan 2026"),
```

- First element: path relative to script (always `raw/...`)
- Second element: display label (format: `"Day N (date)"`)
- Third element: exam date string

If the PDF contains a subject that isn't in the `VACANCIES` dict, no vacancy info will show — that's fine unless the user provides vacancy data.

## Step 4: Regenerate

```bash
python extract_all.py
```

This regenerates all CSVs and HTMLs (combined + per-day) and the index page.

## Step 5: Verify

- Open `index.html` in browser — new position(s) should appear
- Click through to check charts, rankings, and candidate search work

## Step 6: Commit

```bash
git add -A
git commit -m "Add Day N exam data"
```

Never commit PDFs — they are gitignored under `raw/` (contains personal candidate data).

---

# Agent Instructions — Normalised-Score PDFs

Some posts have official "Raw Score and Normalised Score" PDFs (Roll | Raw | Normalised).
These are an **overlay, not a new exam day** — never add them to the `pdfs` list.

1. Map the PDF to the official subject name in `NORM_PDFS` (top of `extract_all.py`).
2. Run `python extract_all.py` — `load_normalized_scores()` parses them, and
   `process_and_export()` adds `Normalized_Score`, `Delta`, `Norm_Rank` columns
   plus a normalisation summary box, delta chart, and normalised cutoff to the
   affected combined + per-day pages and CSVs.
3. Verify roll counts match the combined CSV exactly and raw scores have zero mismatches.

# Agent Instructions — Final Selection Lists

Scanned official PDFs titled "List of issuing Appointment/Clarification letters"
(row per candidate: Sr, Roll No, Application Seq No, DOB, Gender, Applicant/Selection
Category, Selection Committee Recommendation, Remarks) have **no extractable text**
— they are images. There is no OCR tooling in this environment.

1. Render pages with `fitz` (`get_pixmap`) and read the table images directly.
2. Manually transcribe each list to `data/final_selection/<Safe>_final_selection.csv`
   with header `Sr_No,Roll_No,Application_Seq_No,DOB,Gender,Applicant_Category,Selection_Category,Recommendation,Remarks`.
   Map the PDF's post title to the site position name in `POSITION_NAMES` /
   `SOURCES` inside `gen_final_selection.py` (e.g. `CSSD Asstt.` → `CSSD Assistant`,
   `OT Assistant (Unfilled Backlog)` → `O.T. Assistant`).
3. Run `python gen_final_selection.py` — it joins rolls with
   `data/combined/<Safe>_analysis.csv`, cross-checks against
   `data/candidates_called/`, writes `analysis/final_selection/` pages and
   `data/final_selection/_manifest.json`. It **fails on any roll not found in
   raw data or any Registration No mismatch** — fix transcription errors until clean.
4. Run `python extract_all.py` — picks up the manifest, adds "View Final Selection"
   links to affected analysis pages, "Final: N appointed" pills to index cards,
   and the Final Selection section on the index page.
5. Verify (`node --check` on changed inline scripts if JS template code was touched)
   and commit. Never commit PDFs.
