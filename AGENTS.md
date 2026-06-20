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
