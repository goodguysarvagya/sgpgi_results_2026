"""Generate Final Selection pages from transcribed Selection Committee PDFs.

Reads transcriptions from data/final_selection/<Safe>_final_selection.csv
(scanned official PDFs: "List of issuing Appointment/Clarification letters"),
joins each row with the raw-score data in data/combined/<Safe>_analysis.csv
(Roll_No -> Marks, Percentile, Rank), cross-checks against the earlier
called-for-DV lists in data/candidates_called/, and writes
analysis/final_selection/<Safe>_final_selection.html plus _manifest.json
(consumed by extract_all.py's index page).
"""
import csv
import json
import re
from pathlib import Path

out_dir = Path(r"C:\Users\Sarvagya\Desktop\sgpgi_data")
final_dir = out_dir / "data" / "final_selection"
combined_dir = out_dir / "data" / "combined"
called_dir = out_dir / "data" / "candidates_called"
html_dir = out_dir / "analysis" / "final_selection"
html_dir.mkdir(parents=True, exist_ok=True)

# file key -> official position name (must match extract_all.py VACANCIES keys)
POSITION_NAMES = {
    "CSSD_Assistant": "CSSD Assistant",
    "Draftsman": "Draftsman",
    "Junior_Accounts_Officer": "Junior Accounts Officer",
    "Medical_Social_Service_Officer_Gr-II": "Medical Social Service Officer Gr-II",
    "Nuclear_Medicine_Technologist": "Nuclear Medicine Technologist",
    "OT_Assistant": "O.T. Assistant",
    "Technical_Officer_CWS_Biomedical": "Technical Officer (CWS Biomedical)",
}

# file key -> (source PDF in raw/, advt no, exam date) for provenance labels
SOURCES = {
    "CSSD_Assistant": ("CSSD Asstt._0001.pdf", "I/08/9/Rectt/2025-26", "19.06.2026"),
    "Draftsman": ("Draftsman_0001.pdf", "I/08/10/Rectt/2025-26", "19.06.2026"),
    "Junior_Accounts_Officer": ("Junior Accounts Officer_0001.pdf", "I/08/2/Rectt/2025-26", "19.06.2026"),
    "Medical_Social_Service_Officer_Gr-II": ("Medical Social Service Officer Gr. II_0001.pdf", "I/08/6/Rectt/2025-26", "20.06.2026"),
    "Nuclear_Medicine_Technologist": ("Nuclear Medicine Technologist_0001.pdf", "I/08/4/Rectt/2025-26", "19.06.2026"),
    "OT_Assistant": ("OT Assistant (Unfilled Backlog)_0001.pdf", "I/08/12/Rectt/2025-26", "20.06.2026"),
    "Technical_Officer_CWS_Biomedical": ("Technical Officer (CWS Biomedical)_0001.pdf", "I/08/3/Rectt/2025-26", "19.06.2026"),
}

VACANCIES = {
    "Junior Accounts Officer": {"total": 6, "sc": 2, "st": 0, "obc": 1, "ews": 0, "ur": 3, "level": "Level-6", "group": "C", "advt": "I/08/2/Rectt/2025-26"},
    "Technical Officer (CWS Biomedical)": {"total": 1, "sc": 1, "st": 0, "obc": 0, "ews": 0, "ur": 0, "level": "Level-6", "group": "C", "advt": "I/08/3/Rectt/2025-26"},
    "Nuclear Medicine Technologist": {"total": 7, "sc": 2, "st": 0, "obc": 2, "ews": 0, "ur": 3, "level": "Level-5", "group": "C", "advt": "I/08/4/Rectt/2025-26"},
    "Medical Social Service Officer Gr-II": {"total": 2, "sc": 0, "st": 0, "obc": 0, "ews": 0, "ur": 2, "level": "Level-6", "group": "C", "advt": "I/08/6/Rectt/2025-26"},
    "CSSD Assistant": {"total": 20, "sc": 4, "st": 0, "obc": 6, "ews": 2, "ur": 8, "level": "Level-4", "group": "C", "advt": "I/08/9/Rectt/2025-26"},
    "Draftsman": {"total": 1, "sc": 0, "st": 0, "obc": 0, "ews": 0, "ur": 1, "level": "Level-4", "group": "C", "advt": "I/08/10/Rectt/2025-26"},
    "O.T. Assistant": {"total": 81, "sc": 21, "st": 2, "obc": 30, "ews": 0, "ur": 28, "level": "Level-5", "group": "C", "advt": "I/08/12/Rectt/2025-26"},
}


def safe(n):
    return re.sub(r'[^\w\s-]', '', n).strip().replace(' ', '_').replace('.', '')


def status_of(recommendation):
    r = recommendation.strip().lower()
    if "not eligible" in r or "not  eligible" in r:
        return "rejected"
    if "clarification" in r:
        return "clarification"
    if "eligible" in r and "selected" in r:
        return "selected"
    return "other"


def read_combined(safe_name):
    path = combined_dir / f"{safe_name}_analysis.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing combined raw data: {path}")
    rows = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            rows[row["Roll_No"]] = row
    return rows


def read_called(safe_name):
    path = called_dir / f"{safe_name}_PDF_vs_CSV_Ranks.csv"
    if not path.exists():
        return {}
    out = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            out[row["Roll_No_CSV"]] = row
    return out


def gen_position_html(pos_name, safe_name, rows, source_pdf, exam_date, vac, called_map):
    total = len(rows)
    n_sel = sum(1 for r in rows if r["status"] == "selected")
    n_clar = sum(1 for r in rows if r["status"] == "clarification")
    n_rej = sum(1 for r in rows if r["status"] == "rejected")

    rows_json = json.dumps([{
        "sr": r["Sr_No"],
        "roll": r["Roll_No"],
        "reg": r["Application_Seq_No"],
        "dob": r["DOB"],
        "gender": r["Gender"],
        "appcat": r["Applicant_Category"],
        "selcat": r["Selection_Category"],
        "reco": r["Recommendation"],
        "remarks": r["Remarks"],
        "status": r["status"],
        "marks": r.get("Marks"),
        "pctl": r.get("Percentile"),
        "rank": r.get("Rank"),
        "called_rank": r.get("Called_Rank"),
        "reg_match": r.get("Reg_Match"),
    } for r in rows])

    vac_json = json.dumps(vac) if vac else "{}"
    advt = vac.get("advt", "") if vac else ""
    level = vac.get("level", "") if vac else ""
    group = vac.get("group", "") if vac else ""
    vac_total = vac.get("total", 0) if vac else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{pos_name} - Final Selection</title>
<style>
:root {{ --bg: #e8eaf0; --surface: #fff; --text: #222; --text2: #555; --accent: #1a237e; --accent2: #283593; --border: #d0d4dc; --hover-bg: #f0f2f8; --input-bg: #fff; --pill-bg: #eef0f6; --pill-text: #1a237e; }}
body.dark {{ --bg: #121212; --surface: #1e1e1e; --text: #e0e0e0; --text2: #aaa; --accent: #7c8cdb; --accent2: #5c6bc0; --border: #333; --hover-bg: #2a2a35; --input-bg: #2a2a2a; --pill-bg: #2a2a3a; --pill-text: #7c8cdb; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); padding: 20px; transition: background 0.2s, color 0.2s; }}
.container {{ max-width: 1400px; margin: 0 auto; }}
.header-row {{ display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }}
.header-row h1 {{ font-size: 26px; color: var(--accent); }}
.subtitle {{ color: var(--text2); margin-bottom: 16px; font-size: 13px; }}
.back-link {{ color: var(--accent); text-decoration: none; font-size: 13px; font-weight: 600; display: inline-block; margin-bottom: 8px; }}
.back-link:hover {{ text-decoration: underline; }}
.toggle {{ display: inline-flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer; color: var(--text2); user-select: none; }}
.toggle input {{ display: none; }}
.toggle .slider {{ width: 38px; height: 20px; background: var(--border); position: relative; cursor: pointer; transition: 0.2s; }}
.toggle .slider::after {{ content: ''; position: absolute; width: 14px; height: 14px; background: var(--surface); top: 3px; left: 3px; transition: 0.2s; }}
.toggle input:checked + .slider {{ background: var(--accent); }}
.toggle input:checked + .slider::after {{ left: 21px; }}
.info-box {{ background: var(--surface); padding: 14px 16px; border: 1px solid var(--border); margin-bottom: 14px; display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: center; font-size: 13px; }}
.info-pill {{ background: var(--pill-bg); color: var(--pill-text); padding: 3px 10px; font-weight: 600; font-size: 11px; }}
.final-badge {{ padding: 4px 12px; font-weight: 700; font-size: 12px; color: #fff; background: #2e7d32; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 16px; }}
.stat-card {{ background: var(--surface); padding: 14px; text-align: center; border: 1px solid var(--border); }}
.stat-card .label {{ font-size: 10px; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; }}
.stat-card .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; color: var(--accent); }}
.stat-card .value.green {{ color: #2e7d32; }}
.stat-card .value.orange {{ color: #e65100; }}
.stat-card .value.red {{ color: #c62828; }}
body.dark .stat-card .value.green {{ color: #66bb6a; }}
body.dark .stat-card .value.orange {{ color: #ffb74d; }}
body.dark .stat-card .value.red {{ color: #ef5350; }}
.status-filter {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }}
.status-filter button {{ padding: 6px 16px; border: 1px solid var(--border); background: var(--surface); color: var(--text); cursor: pointer; font-size: 12px; font-weight: 600; }}
.status-filter button.active {{ background: var(--accent); color: var(--surface); border-color: var(--accent); }}
.search-section {{ background: var(--surface); padding: 14px 16px; border: 1px solid var(--border); margin-bottom: 14px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
.search-section input {{ flex: 1; min-width: 180px; padding: 8px 12px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 13px; outline: none; }}
.search-section input:focus {{ border-color: var(--accent); }}
.search-section button {{ padding: 8px 20px; background: var(--accent); color: var(--surface); border: none; cursor: pointer; font-size: 13px; font-weight: 600; }}
.search-section button:hover {{ background: var(--accent2); }}
.table-wrap {{ background: var(--surface); padding: 14px; border: 1px solid var(--border); overflow-x: auto; margin-bottom: 14px; }}
.table-wrap h3 {{ font-size: 13px; margin-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th {{ background: var(--accent); color: var(--surface); padding: 7px 8px; text-align: left; font-weight: 600; white-space: nowrap; }}
th.sortable {{ cursor: pointer; user-select: none; position: relative; padding-right: 18px; }}
th.sortable:hover {{ background: var(--accent2); }}
.sort-arrow {{ position: absolute; right: 4px; top: 50%; transform: translateY(-50%); font-size: 10px; opacity: 0.5; }}
th.sorted-asc .sort-arrow, th.sorted-desc .sort-arrow {{ opacity: 1; }}
td {{ padding: 5px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }}
tr:hover td {{ background: var(--hover-bg); }}
.rank-badge {{ background: var(--accent); color: var(--surface); padding: 1px 6px; font-size: 11px; font-weight: 600; }}
.st {{ padding: 2px 8px; font-size: 11px; font-weight: 700; white-space: nowrap; }}
.st-selected {{ background: #2e7d32; color: #fff; }}
.st-clarification {{ background: #e65100; color: #fff; }}
.st-rejected {{ background: #c62828; color: #fff; }}
.st-other {{ background: var(--pill-bg); color: var(--pill-text); }}
.remark-cell {{ max-width: 280px; font-size: 11px; color: var(--text2); }}
.reg-diff {{ color: #c62828; font-weight: 700; }}
.note-box {{ background: var(--surface); padding: 12px 16px; border: 1px solid var(--border); margin-bottom: 14px; font-size: 12px; color: var(--text2); line-height: 1.7; }}
.note-box strong {{ color: var(--accent); }}
.filter-input {{ padding: 7px 12px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 12px; width: 240px; outline: none; }}
.filter-input:focus {{ border-color: var(--accent); }}
.disclaimer {{ margin-top: 28px; padding: 14px 18px; background: var(--surface); border: 1px solid var(--border); font-size: 12px; color: var(--text2); line-height: 1.7; }}
.disclaimer strong {{ color: var(--accent); }}
.footer {{ margin-top: 18px; text-align: center; font-size: 11px; color: var(--text2); padding: 12px 0 4px; border-top: 1px solid var(--border); }}
.footer a {{ color: var(--accent); text-decoration: none; }}
@media (max-width: 720px) {{ body {{ padding: 16px; }} h1 {{ font-size: 22px; }} }}
</style>
</head>
<body>
<div class="container">
<div class="header-row">
<div><a class="back-link" href="../../index.html">&larr; Back to All Positions</a><h1>{pos_name}</h1><div style="margin-top:4px;display:flex;gap:8px;flex-wrap:wrap;"><a class="back-link" href="../combined/{safe_name}_analysis.html">&larr; Full Score Analysis</a><a class="back-link" href="../called_candidates/{safe_name}_called_candidates.html" style="color:#e65100;">View Called Candidates &rarr;</a></div></div>
<label class="toggle"><span>Dark</span><input type="checkbox" id="darkToggle"><span class="slider"></span></label>
</div>
<p class="subtitle">Final Selection &mdash; Selection Committee Recommendation (Exam Date: {exam_date})</p>

<div class="info-box" id="infoBox"></div>

<div class="stats-grid" id="statsGrid"></div>

<div class="note-box" id="xcheckBox" style="display:none"></div>

<div class="status-filter" id="statusFilter">
<button class="active" onclick="setStatus('all')">All ({total})</button>
<button onclick="setStatus('selected')">Appointment Issued ({n_sel})</button>
<button onclick="setStatus('clarification')">Clarification ({n_clar})</button>
<button onclick="setStatus('rejected')">Not Eligible ({n_rej})</button>
</div>

<div class="search-section">
<input id="candidateSearchInput" type="text" placeholder="Enter Registration No or Roll No..." onkeydown="if(event.key==='Enter') searchCandidate()">
<button onclick="searchCandidate()">Search</button>
</div>

<div class="table-wrap">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
<h3 style="margin:0" id="tableTitle">All Candidates in Final List</h3>
<input id="searchInput" type="text" placeholder="Filter by Reg No, Roll No or name..." class="filter-input" oninput="filterTable()">
</div>
<table><thead><tr><th>Sr</th><th>Status</th><th class="sortable" onclick="sortBy('roll')">Roll No<span class="sort-arrow" id="sort-roll"></span></th><th class="sortable" onclick="sortBy('reg')">Registration No<span class="sort-arrow" id="sort-reg"></span></th><th>DOB</th><th>Gender</th><th>Applicant Cat</th><th>Selection Cat</th><th>Recommendation</th><th>Remarks</th><th class="sortable" onclick="sortBy('marks')">Raw Marks<span class="sort-arrow" id="sort-marks"></span></th><th class="sortable" onclick="sortBy('rank')">Raw Rank<span class="sort-arrow" id="sort-rank"></span></th></tr></thead>
<tbody id="allBody"></tbody></table>
</div>
</div>

<script>
let allData = {rows_json};
let statusFilter = 'all';
let sortKey = null;
let sortDir = 1;
const vac = {vac_json};

function statusBadge(s) {{
    if (s === 'selected') return '<span class="st st-selected">Appointment Issued</span>';
    if (s === 'clarification') return '<span class="st st-clarification">Clarification</span>';
    if (s === 'rejected') return '<span class="st st-rejected">Not Eligible</span>';
    return '<span class="st st-other">' + s + '</span>';
}}

function setStatus(s) {{
    statusFilter = s;
    document.querySelectorAll('#statusFilter button').forEach(b => b.classList.remove('active'));
    const btns = document.querySelectorAll('#statusFilter button');
    const idx = s === 'all' ? 0 : s === 'selected' ? 1 : s === 'clarification' ? 2 : 3;
    if (btns[idx]) btns[idx].classList.add('active');
    document.getElementById('searchInput').value = '';
    renderTable();
}}

function sortBy(key) {{
    if (sortKey === key) {{ sortDir *= -1; }} else {{ sortKey = key; sortDir = 1; }}
    document.querySelectorAll('th.sortable').forEach(th => th.classList.remove('sorted-asc', 'sorted-desc'));
    document.querySelectorAll('.sort-arrow').forEach(s => s.textContent = '');
    const arrow = document.getElementById('sort-' + key);
    if (arrow) arrow.textContent = sortDir === 1 ? '▲' : '▼';
    const th = document.querySelector(`th[onclick*="${{key}}"]`);
    if (th) th.classList.add(sortDir === 1 ? 'sorted-asc' : 'sorted-desc');
    allData.sort((a, b) => {{
        let va = a[key], vb = b[key];
        if (va === null || va === undefined) return 1 * sortDir;
        if (vb === null || vb === undefined) return -1 * sortDir;
        if (typeof va === 'string') return va.localeCompare(vb) * sortDir;
        return (va - vb) * sortDir;
    }});
    renderTable();
}}

function filteredData() {{
    const q = document.getElementById('searchInput').value.toLowerCase();
    let rows = statusFilter === 'all' ? allData : allData.filter(d => d.status === statusFilter);
    if (q) rows = rows.filter(d => d.reg.toLowerCase().includes(q) || d.roll.includes(q) || (d.remarks || '').toLowerCase().includes(q));
    return rows;
}}

function loadData() {{
    renderInfo(); renderStats(); renderXcheck(); renderTable();
}}

function renderInfo() {{
    let html = `<span class="final-badge">FINAL SELECTION</span>`;
    html += `<span class="info-pill">{level} / Group {group}</span>`;
    html += `<span class="info-pill">Advt: {advt}</span>`;
    html += `<span class="info-pill">Exam: {exam_date}</span>`;
    html += `<span class="info-pill">Total Vacancies: {vac_total}</span>`;
    html += `<span class="info-pill">In final list: {total}</span>`;
    document.getElementById('infoBox').innerHTML = html;
}}

function renderStats() {{
    const sel = allData.filter(d => d.status === 'selected').length;
    const clar = allData.filter(d => d.status === 'clarification').length;
    const rej = allData.filter(d => d.status === 'rejected').length;
    const marks = allData.map(d => d.marks).filter(v => v !== null && v !== undefined);
    const avg = marks.length ? (marks.reduce((a,b) => a+b, 0) / marks.length).toFixed(2) : '-';
    document.getElementById('statsGrid').innerHTML = `
        <div class="stat-card"><div class="label">In Final List</div><div class="value">${{allData.length}}</div></div>
        <div class="stat-card"><div class="label">Appointment Issued</div><div class="value green">${{sel}}</div></div>
        <div class="stat-card"><div class="label">Clarification Needed</div><div class="value orange">${{clar}}</div></div>
        <div class="stat-card"><div class="label">Not Eligible</div><div class="value red">${{rej}}</div></div>
        <div class="stat-card"><div class="label">Avg Raw Marks (listed)</div><div class="value">${{avg}}</div></div>
    `;
}}

function renderXcheck() {{
    const box = document.getElementById('xcheckBox');
    const notCalled = allData.filter(d => d.called_rank === null || d.called_rank === undefined);
    const missed = (window.__calledMissing || []);
    if (!notCalled.length && !missed.length) {{ box.style.display = 'none'; return; }}
    let html = '<strong>Cross-check vs called-for-DV list:</strong><br>';
    if (notCalled.length) html += `In final list but NOT in called list: <strong>${{notCalled.map(d => d.roll).join(', ')}}</strong><br>`;
    if (missed.length) html += `Called for DV but NOT in final list: <strong>${{missed.join(', ')}}</strong>`;
    box.innerHTML = html;
    box.style.display = 'block';
}}

function renderTable() {{
    const rows = filteredData();
    const titles = {{ all: 'All Candidates in Final List', selected: 'Appointment Issued', clarification: 'Clarification Needed', rejected: 'Not Eligible' }};
    document.getElementById('tableTitle').textContent = titles[statusFilter] + ` (${{rows.length}})`;
    const tbody = document.getElementById('allBody');
    tbody.innerHTML = rows.map(d => {{
        const regCell = d.reg_match === false ? `<span class="reg-diff">${{d.reg}} ⚠</span>` : d.reg;
        const marksCell = (d.marks === null || d.marks === undefined) ? '-' : `<strong>${{d.marks.toFixed(2)}}</strong>`;
        const rankCell = (d.rank === null || d.rank === undefined) ? '-' : `<span class="rank-badge">#${{d.rank}}</span>`;
        return `<tr><td>${{d.sr}}</td><td>${{statusBadge(d.status)}}</td><td>${{d.roll}}</td><td>${{regCell}}</td><td>${{d.dob}}</td><td>${{d.gender}}</td><td>${{d.appcat}}</td><td>${{d.selcat}}</td><td>${{d.reco}}</td><td class="remark-cell">${{d.remarks}}</td><td>${{marksCell}}</td><td>${{rankCell}}</td></tr>`;
    }}).join('');
}}

function filterTable() {{
    renderTable();
}}

function searchCandidate() {{
    const q = document.getElementById('candidateSearchInput').value.trim().toLowerCase();
    if (!q) return;
    document.getElementById('searchInput').value = q;
    renderTable();
    const el = document.querySelector('.table-wrap');
    if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
}}

loadData();
const t = document.getElementById('darkToggle');
const m = window.matchMedia('(prefers-color-scheme:dark)');
t.checked = localStorage.getItem('dark') === '1' || (!localStorage.getItem('dark') && m.matches);
t.onchange = () => {{ document.body.classList.toggle('dark', t.checked); localStorage.setItem('dark', t.checked ? '1' : '0'); }};
if (t.checked) document.body.classList.add('dark');
</script>
<div class="disclaimer">
<strong>Disclaimer:</strong> This page transcribes the official SGPGIMS Selection Committee list (source PDF: {source_pdf}; list is explicitly <strong>not in order of rank or category</strong>). Raw marks/ranks shown are joined from this site's raw-score data for reference — the official merit is the Selection Committee's recommendation. Appointment letters are issued only to candidates marked Eligible &amp; Selected.
</div>
<div class="footer">Made for public use — <a href="https://www.gnu.org/licenses/agpl-3.0.html">GNU AGPL v3</a> | Source: <a href="https://github.com/goodguysarvagya/sgpgi_results_2026">github.com/goodguysarvagya/sgpgi_results_2026</a></div>
</body>
</html>"""
    return html


def main():
    manifest = {}
    errors = []
    for file_key, pos_name in sorted(POSITION_NAMES.items(), key=lambda kv: kv[1]):
        safe_name = safe(pos_name)
        csv_path = final_dir / f"{file_key}_final_selection.csv"
        if not csv_path.exists():
            print(f"  SKIP (no transcription CSV): {csv_path.name}")
            continue
        source_pdf, advt_no, exam_date = SOURCES[file_key]
        with open(csv_path, newline='', encoding='utf-8') as f:
            trans = list(csv.DictReader(f))
        print(f"\n{pos_name}: {len(trans)} transcribed rows (source: {source_pdf})")

        try:
            combined = read_combined(safe_name)
        except FileNotFoundError as e:
            errors.append(str(e))
            print(f"  ERROR: {e}")
            continue
        called_map = read_called(safe_name)
        print(f"  combined raw rows: {len(combined)} | called-list rows: {len(called_map)}")

        rows = []
        for t in trans:
            roll = t["Roll_No"].strip()
            reg = t["Application_Seq_No"].strip()
            rec = {
                "Sr_No": int(t["Sr_No"]),
                "Roll_No": roll,
                "Application_Seq_No": reg,
                "DOB": t["DOB"].strip(),
                "Gender": t["Gender"].strip(),
                "Applicant_Category": t["Applicant_Category"].strip(),
                "Selection_Category": t["Selection_Category"].strip(),
                "Recommendation": t["Recommendation"].strip(),
                "Remarks": t["Remarks"].strip(),
            }
            rec["status"] = status_of(rec["Recommendation"])
            c = combined.get(roll)
            if c is None:
                errors.append(f"{pos_name}: roll {roll} NOT FOUND in combined raw data")
                print(f"  ERROR: roll {roll} NOT FOUND in combined raw data")
                rec["Marks"] = None
                rec["Percentile"] = None
                rec["Rank"] = None
                rec["Reg_Match"] = False
            else:
                rec["Marks"] = float(c["Marks"])
                rec["Percentile"] = float(c["Percentile"])
                rec["Rank"] = int(c["Rank"])
                rec["Reg_Match"] = (c["Registration_No"].strip() == reg)
                if not rec["Reg_Match"]:
                    errors.append(f"{pos_name}: roll {roll} reg mismatch PDF={reg} CSV={c['Registration_No']}")
                    print(f"  ERROR: roll {roll} reg mismatch PDF={reg} CSV={c['Registration_No']}")
            cm = called_map.get(roll)
            rec["Called_Rank"] = int(cm["Rank_in_PDF"]) if cm else None
            rows.append(rec)

        # cross-checks vs called list
        final_rolls = {r["Roll_No"] for r in rows}
        called_rolls = set(called_map.keys())
        not_in_called = sorted(final_rolls - called_rolls)
        missing_from_final = sorted(called_rolls - final_rolls)
        if not_in_called:
            print(f"  NOTE: in final list but NOT in called list: {not_in_called}")
        if missing_from_final:
            print(f"  NOTE: called for DV but NOT in final list: {missing_from_final}")

        vac = VACANCIES.get(pos_name, {})
        html = gen_position_html(pos_name, safe_name, rows, source_pdf, exam_date, vac, called_map)
        # define called-missing list for the xcheck box (before loadData runs)
        html = html.replace("loadData();", f"window.__calledMissing = {json.dumps(missing_from_final)};\nloadData();", 1)
        html_path = html_dir / f"{safe_name}_final_selection.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        n_sel = sum(1 for r in rows if r["status"] == "selected")
        n_clar = sum(1 for r in rows if r["status"] == "clarification")
        n_rej = sum(1 for r in rows if r["status"] == "rejected")
        manifest[pos_name] = {
            "safe": safe_name,
            "total": len(rows),
            "selected": n_sel,
            "clarification": n_clar,
            "rejected": n_rej,
            "html": f"analysis/final_selection/{safe_name}_final_selection.html",
            "source_pdf": source_pdf,
            "exam_date": exam_date,
        }
        print(f"  Generated: {html_path.name} (selected={n_sel} clarification={n_clar} rejected={n_rej})")

    with open(final_dir / "_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest: {len(manifest)} positions -> data/final_selection/_manifest.json")
    if errors:
        print(f"\n*** {len(errors)} VERIFICATION ERRORS ***")
        for e in errors:
            print("  - " + e)
        raise SystemExit(1)
    print("\nAll rolls verified against raw data. Done!")


if __name__ == "__main__":
    main()
