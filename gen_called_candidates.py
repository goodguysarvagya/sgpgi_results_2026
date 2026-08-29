import csv, json
from pathlib import Path

out_dir = Path(r"C:\Users\Sarvagya\Desktop\sgpgi_data")
called_dir = out_dir / "data" / "candidates_called"
html_dir = out_dir / "analysis" / "called_candidates"
html_dir.mkdir(parents=True, exist_ok=True)

# Position name -> call type
CALL_TYPES = {
    "Senior Administrative Assistant": "Skill Test",
    "Stenographer": "Skill Test",
}

POSITION_NAMES = {
    "CSSD_Assistant": "CSSD Assistant",
    "Draftsman": "Draftsman",
    "Junior_Accounts_Officer": "Junior Accounts Officer",
    "Medical_Social_Service_Officer_Gr-II": "Medical Social Service Officer Gr-II",
    "Nuclear_Medicine_Technologist": "Nuclear Medicine Technologist",
    "OT_Assistant": "O.T. Assistant",
    "Senior_Administrative_Assistant": "Senior Administrative Assistant",
    "Stenographer": "Stenographer",
    "Store_Keeper": "Store Keeper",
    "Technical_Officer_CWS_Biomedical": "Technical Officer (CWS Biomedical)",
}

VACANCIES = {
    "Nursing Officer": {"total": 1200, "sc": 253, "st": 24, "obc": 324, "ews": 119, "ur": 480, "level": "Level-7", "group": "B", "advt": "I/08/1/Rectt/2025-26"},
    "Junior Accounts Officer": {"total": 6, "sc": 2, "st": 0, "obc": 1, "ews": 0, "ur": 3, "level": "Level-6", "group": "C", "advt": "I/08/2/Rectt/2025-26"},
    "Technical Officer (CWS Biomedical)": {"total": 1, "sc": 1, "st": 0, "obc": 0, "ews": 0, "ur": 0, "level": "Level-6", "group": "C", "advt": "I/08/3/Rectt/2025-26"},
    "Nuclear Medicine Technologist": {"total": 7, "sc": 2, "st": 0, "obc": 2, "ews": 0, "ur": 3, "level": "Level-5", "group": "C", "advt": "I/08/4/Rectt/2025-26"},
    "Store Keeper": {"total": 22, "sc": 5, "st": 0, "obc": 6, "ews": 2, "ur": 9, "level": "Level-6", "group": "C", "advt": "I/08/5/Rectt/2025-26"},
    "Medical Social Service Officer Gr-II": {"total": 2, "sc": 0, "st": 0, "obc": 0, "ews": 0, "ur": 2, "level": "Level-6", "group": "C", "advt": "I/08/6/Rectt/2025-26"},
    "Senior Administrative Assistant": {"total": 32, "sc": 7, "st": 1, "obc": 8, "ews": 3, "ur": 13, "level": "Level-4", "group": "C", "advt": "I/08/7/Rectt/2025-26"},
    "Stenographer": {"total": 64, "sc": 13, "st": 1, "obc": 18, "ews": 6, "ur": 26, "level": "Level-4", "group": "C", "advt": "I/08/8/Rectt/2025-26"},
    "CSSD Assistant": {"total": 20, "sc": 4, "st": 0, "obc": 6, "ews": 2, "ur": 8, "level": "Level-4", "group": "C", "advt": "I/08/9/Rectt/2025-26"},
    "Draftsman": {"total": 1, "sc": 0, "st": 0, "obc": 0, "ews": 0, "ur": 1, "level": "Level-4", "group": "C", "advt": "I/08/10/Rectt/2025-26"},
    "Hospital Attendant Gr-II": {"total": 43, "sc": 9, "st": 0, "obc": 13, "ews": 4, "ur": 17, "level": "Level-1", "group": "D", "advt": "I/08/11/Rectt/2025-26"},
    "O.T. Assistant": {"total": 81, "sc": 21, "st": 2, "obc": 30, "ews": 0, "ur": 28, "level": "Level-5", "group": "C", "advt": "I/08/12/Rectt/2025-26"},
}


def safe(n):
    import re
    return re.sub(r'[^\w\s-]', '', n).strip().replace(' ', '_').replace('.', '')


def read_csv(filepath):
    rows = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["Marks"] = float(row["Marks"])
            row["Percentile"] = float(row["Percentile"])
            row["Rank_in_CSV"] = int(row["Rank_in_CSV"])
            row["Rank_in_PDF"] = int(row["Rank_in_PDF"])
            rows.append(row)
    return rows


def gen_position_html(pos_name, safe_name, rows, call_type):
    vac = VACANCIES.get(pos_name, {})
    total_called = len(rows)
    total_vac = vac.get("total", 0)

    rows_json = json.dumps([{
        "reg": r["Registration_No"],
        "roll_csv": r["Roll_No_CSV"],
        "roll_pdf": r["Roll_No_PDF"],
        "marks": r["Marks"],
        "pctl": r["Percentile"],
        "rank_csv": r["Rank_in_CSV"],
        "rank_pdf": r["Rank_in_PDF"],
        "rank_change": r["Rank_in_CSV"] - r["Rank_in_PDF"],
    } for r in rows])

    vac_json = json.dumps(vac) if vac else "{}"

    call_type_badge_color = "#e65100" if call_type == "Skill Test" else "#1a237e"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{pos_name} - Called Candidates</title>
<style>
:root {{ --bg: #e8eaf0; --surface: #fff; --text: #222; --text2: #555; --accent: #1a237e; --accent2: #283593; --border: #d0d4dc; --hover-bg: #f0f2f8; --input-bg: #fff; --pill-bg: #eef0f6; --pill-text: #1a237e; }}
body.dark {{ --bg: #121212; --surface: #1e1e1e; --text: #e0e0e0; --text2: #aaa; --accent: #7c8cdb; --accent2: #5c6bc0; --border: #333; --hover-bg: #2a2a35; --input-bg: #2a2a2a; --pill-bg: #2a2a3a; --pill-text: #7c8cdb; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); padding: 20px; transition: background 0.2s, color 0.2s; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
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
.call-type-badge {{ padding: 4px 12px; font-weight: 700; font-size: 12px; color: #fff; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 16px; }}
.stat-card {{ background: var(--surface); padding: 14px; text-align: center; border: 1px solid var(--border); }}
.stat-card .label {{ font-size: 10px; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; }}
.stat-card .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; color: var(--accent); }}
.stat-card .value.green {{ color: #2e7d32; }}
body.dark .stat-card .value.green {{ color: #66bb6a; }}
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
td {{ padding: 5px 8px; border-bottom: 1px solid var(--border); }}
tr:hover td {{ background: var(--hover-bg); }}
.rank-badge {{ background: var(--accent); color: var(--surface); padding: 1px 6px; font-size: 11px; font-weight: 600; }}
.roll-match {{ color: #2e7d32; font-weight: 600; }}
.roll-diff {{ color: #c62828; font-weight: 600; }}
.rank-up {{ color: #2e7d32; font-weight: 700; }}
.rank-down {{ color: #c62828; font-weight: 700; }}
.rank-same {{ color: var(--text2); }}
body.dark .rank-up {{ color: #66bb6a; }}
body.dark .rank-down {{ color: #ef5350; }}
.pagination {{ display: flex; justify-content: center; gap: 4px; margin-top: 10px; flex-wrap: wrap; }}
.pagination button {{ padding: 4px 10px; border: 1px solid var(--border); background: var(--surface); color: var(--text); cursor: pointer; font-size: 12px; }}
.pagination button.active {{ background: var(--accent); color: var(--surface); border-color: var(--accent); }}
.pagination button:hover:not(.active) {{ background: var(--hover-bg); }}
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
<div><a class="back-link" href="../../index.html">&larr; Back to All Positions</a><h1>{pos_name}</h1></div>
<label class="toggle"><span>Dark</span><input type="checkbox" id="darkToggle"><span class="slider"></span></label>
</div>
<p class="subtitle">Called Candidates &mdash; Shortlisted for {call_type}</p>

<div class="info-box" id="infoBox"></div>

<div class="stats-grid" id="statsGrid"></div>

<div class="search-section">
<input id="candidateSearchInput" type="text" placeholder="Enter Registration No or Roll No..." onkeydown="if(event.key==='Enter') searchCandidate()">
<button onclick="searchCandidate()">Search</button>
</div>

<div class="table-wrap">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
<h3 style="margin:0">All Called Candidates</h3>
<input id="searchInput" type="text" placeholder="Filter by Reg No or Roll No..." class="filter-input" oninput="filterTable()">
</div>
<table><thead><tr><th class="sortable" onclick="sortBy('num')">#<span class="sort-arrow" id="sort-num"></span></th><th class="sortable" onclick="sortBy('reg')">Registration No<span class="sort-arrow" id="sort-reg"></span></th><th class="sortable" onclick="sortBy('roll')">Roll No<span class="sort-arrow" id="sort-roll"></span></th><th class="sortable" onclick="sortBy('marks')">Marks<span class="sort-arrow" id="sort-marks"></span></th><th class="sortable" onclick="sortBy('pctl')">Percentile<span class="sort-arrow" id="sort-pctl"></span></th><th class="sortable" onclick="sortBy('rank_csv')">Raw Score Rank<span class="sort-arrow" id="sort-rank_csv"></span></th><th class="sortable" onclick="sortBy('rank_pdf')">Merit List Rank<span class="sort-arrow" id="sort-rank_pdf"></span></th><th class="sortable" onclick="sortBy('rank_change')">Change<span class="sort-arrow" id="sort-rank_change"></span></th></tr></thead>
<tbody id="allBody"></tbody></table>
<div class="pagination" id="pagination"></div>
</div>
</div>

<script>
const PAGE_SIZE = 50;
let allData = {rows_json};
let currentPage = 1;
const vac = {vac_json};
const callType = "{call_type}";
let sortKey = null;
let sortDir = 1;

function sortBy(key) {{
    if (sortKey === key) {{ sortDir *= -1; }} else {{ sortKey = key; sortDir = key === 'rank_change' ? -1 : 1; }}
    document.querySelectorAll('th.sortable').forEach(th => th.classList.remove('sorted-asc', 'sorted-desc'));
    const th = document.querySelector(`th[onclick*="${{key}}"]`);
    if (th) th.classList.add(sortDir === 1 ? 'sorted-asc' : 'sorted-desc');
    document.querySelectorAll('.sort-arrow').forEach(s => s.textContent = '');
    const arrow = document.getElementById('sort-' + key);
    if (arrow) arrow.textContent = sortDir === 1 ? '▲' : '▼';
    allData.sort((a, b) => {{
        let va, vb;
        if (key === 'reg') {{ va = a.reg; vb = b.reg; }}
        else if (key === 'roll') {{ va = a.roll_csv; vb = b.roll_csv; }}
        else if (key === 'marks') {{ va = a.marks; vb = b.marks; }}
        else if (key === 'pctl') {{ va = a.pctl; vb = b.pctl; }}
        else if (key === 'rank_csv') {{ va = a.rank_csv; vb = b.rank_csv; }}
        else if (key === 'rank_pdf') {{ va = a.rank_pdf; vb = b.rank_pdf; }}
        else if (key === 'rank_change') {{ va = a.rank_change; vb = b.rank_change; }}
        else {{ return 0; }}
        if (typeof va === 'string') return va.localeCompare(vb) * sortDir;
        return (va - vb) * sortDir;
    }});
    renderTable(1);
}}

function loadData() {{
    renderInfo(); renderStats(); renderTable(1);
}}

function renderInfo() {{
    let html = `<span class="call-type-badge" style="background:{call_type_badge_color}">{call_type}</span>`;
    if (vac.level) {{
        html += `<span class="info-pill">{vac.get("level", "")} / Group {vac.get("group", "")}</span>`;
        html += `<span class="info-pill">Advt: {vac.get("advt", "")}</span>`;
        html += `<span class="info-pill">Total Vacancies: {total_vac}</span>`;
        html += `<span class="info-pill">Called: {total_called} candidates</span>`;
        const cats = `SC ${{vac.sc}} ST ${{vac.st}} OBC ${{vac.obc}} EWS ${{vac.ews}} UR ${{vac.ur}}`;
        html += `<span class="info-pill">${{cats}}</span>`;
    }}
    document.getElementById('infoBox').innerHTML = html;
}}

function renderStats() {{
    const marks = allData.map(d => d.marks);
    const highest = Math.max(...marks);
    const lowest = Math.min(...marks);
    const avg = (marks.reduce((a,b) => a+b, 0) / marks.length);
    const sorted = [...marks].sort((a,b) => a-b);
    const median = sorted.length % 2 ? sorted[Math.floor(sorted.length/2)] : (sorted[sorted.length/2-1]+sorted[sorted.length/2])/2;
    const rollsMatch = allData.filter(d => d.roll_csv === d.roll_pdf).length;
    document.getElementById('statsGrid').innerHTML = `
        <div class="stat-card"><div class="label">Total Called</div><div class="value">${{allData.length}}</div></div>
        <div class="stat-card"><div class="label">Highest Marks</div><div class="value green">${{highest.toFixed(2)}}</div></div>
        <div class="stat-card"><div class="label">Lowest Marks</div><div class="value">${{lowest.toFixed(2)}}</div></div>
        <div class="stat-card"><div class="label">Average Marks</div><div class="value">${{avg.toFixed(2)}}</div></div>
        <div class="stat-card"><div class="label">Median Marks</div><div class="value">${{median.toFixed(2)}}</div></div>
        <div class="stat-card"><div class="label">Rolls Match</div><div class="value green">${{rollsMatch}} / ${{allData.length}}</div></div>
    `;
}}

function renderTable(page) {{
    currentPage = page;
    const start = (page - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, allData.length);
    const tbody = document.getElementById('allBody');
    tbody.innerHTML = allData.slice(start, end).map((d, i) => {{
        const rollClass = d.roll_csv === d.roll_pdf ? 'roll-match' : 'roll-diff';
        const rollDisplay = d.roll_csv === d.roll_pdf ? d.roll_csv : `${{d.roll_csv}} <span style="font-size:10px;color:var(--text2)">(PDF: ${{d.roll_pdf}})</span>`;
        const change = d.rank_change;
        const changeClass = change > 0 ? 'rank-up' : change < 0 ? 'rank-down' : 'rank-same';
        const changeText = change > 0 ? `+${{change}}` : change === 0 ? '=' : `${{change}}`;
        return `<tr><td><span class="rank-badge">#${{start + i + 1}}</span></td><td>${{d.reg}}</td><td class="${{rollClass}}">${{rollDisplay}}</td><td><strong>${{d.marks.toFixed(2)}}</strong></td><td>${{d.pctl.toFixed(2)}}%</td><td>#${{d.rank_csv}}</td><td>#${{d.rank_pdf}}</td><td class="${{changeClass}}">${{changeText}}</td></tr>`;
    }}).join('');
    renderPagination();
}}

function renderPagination() {{
    const totalPages = Math.ceil(allData.length / PAGE_SIZE);
    const container = document.getElementById('pagination');
    let html = `<button onclick="renderTable(1)" ${{currentPage===1?'disabled':''}}>&laquo;</button>`;
    for (let p = Math.max(1, currentPage-3); p <= Math.min(totalPages, currentPage+3); p++) {{
        html += `<button onclick="renderTable(${{p}})" class="${{p===currentPage?'active':''}}">${{p}}</button>`;
    }}
    html += `<button onclick="renderTable(${{totalPages}})" ${{currentPage===totalPages?'disabled':''}}>&raquo;</button>`;
    container.innerHTML = html;
}}

function filterTable() {{
    const q = document.getElementById('searchInput').value.toLowerCase();
    const filtered = q ? allData.filter(d => d.reg.toLowerCase().includes(q) || d.roll_csv.includes(q) || d.roll_pdf.includes(q)) : allData;
    const tbody = document.getElementById('allBody');
    if (q) {{
        tbody.innerHTML = filtered.map((d, i) => {{
            const rollClass = d.roll_csv === d.roll_pdf ? 'roll-match' : 'roll-diff';
            const rollDisplay = d.roll_csv === d.roll_pdf ? d.roll_csv : `${{d.roll_csv}} <span style="font-size:10px;color:var(--text2)">(PDF: ${{d.roll_pdf}})</span>`;
            const change = d.rank_change;
            const changeClass = change > 0 ? 'rank-up' : change < 0 ? 'rank-down' : 'rank-same';
            const changeText = change > 0 ? `+${{change}}` : change === 0 ? '=' : `${{change}}`;
            return `<tr><td><span class="rank-badge">#${{i+1}}</span></td><td>${{d.reg}}</td><td class="${{rollClass}}">${{rollDisplay}}</td><td><strong>${{d.marks.toFixed(2)}}</strong></td><td>${{d.pctl.toFixed(2)}}%</td><td>#${{d.rank_csv}}</td><td>#${{d.rank_pdf}}</td><td class="${{changeClass}}">${{changeText}}</td></tr>`;
        }}).join('');
        document.getElementById('pagination').innerHTML = '';
    }} else {{ renderTable(1); }}
}}

function searchCandidate() {{
    const q = document.getElementById('candidateSearchInput').value.trim().toLowerCase();
    if (!q) return;
    document.getElementById('searchInput').value = q;
    filterTable();
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
<strong>Disclaimer:</strong> This list shows candidates shortlisted by SGPGIMS for {call_type}. Roll numbers are cross-verified between the official PDF and CSV data. Green roll numbers indicate a match; red indicates a discrepancy between PDF and CSV roll numbers.
</div>
<div class="footer">Made for public use — <a href="https://www.gnu.org/licenses/agpl-3.0.html">GNU AGPL v3</a> | Source: <a href="https://github.com/goodguysarvagya/sgpgi_results_2026">github.com/goodguysarvagya/sgpgi_results_2026</a></div>
</body>
</html>"""
    return html


def main():
    csv_files = sorted(called_dir.glob("*_PDF_vs_CSV_Ranks.csv"))
    position_pages = []

    for csv_file in csv_files:
        file_key = csv_file.stem.replace("_PDF_vs_CSV_Ranks", "")
        pos_name = POSITION_NAMES.get(file_key, file_key.replace("_", " "))
        safe_name = safe(pos_name)
        rows = read_csv(csv_file)
        call_type = CALL_TYPES.get(pos_name, "Document Verification")

        html = gen_position_html(pos_name, safe_name, rows, call_type)
        html_path = html_dir / f"{safe_name}_called_candidates.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        position_pages.append({
            "pos_name": pos_name,
            "safe_name": safe_name,
            "call_type": call_type,
            "total_called": len(rows),
            "csv_file": csv_file.name,
        })
        print(f"  Generated: {html_path.name} ({len(rows)} candidates, {call_type})")

    print(f"\nTotal: {len(position_pages)} position pages generated")
    return position_pages


if __name__ == "__main__":
    main()
