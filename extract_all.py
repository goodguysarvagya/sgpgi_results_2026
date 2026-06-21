import fitz, re, csv, json
from pathlib import Path
from collections import defaultdict

out_dir = Path(r"C:\Users\Sarvagya\Desktop\sgpgi_data")
data_combined = out_dir / "data" / "combined"
data_per_day = out_dir / "data" / "per_day"
html_combined = out_dir / "analysis" / "combined"
html_per_day = out_dir / "analysis" / "per_day"
for d in [data_combined, data_per_day, html_combined, html_per_day]:
    d.mkdir(parents=True, exist_ok=True)

VACANCIES = {
    "Nursing Officer": {"advt": "I/08/1/Rectt/2025-26", "sc": 253, "st": 24, "obc": 324, "ews": 119, "ur": 480, "total": 1200, "level": "Level-7", "group": "B"},
    "Junior Accounts Officer": {"advt": "I/08/2/Rectt/2025-26", "sc": 2, "st": 0, "obc": 1, "ews": 0, "ur": 3, "total": 6, "level": "Level-6", "group": "C"},
    "Technical Officer (CWS Biomedical)": {"advt": "I/08/3/Rectt/2025-26", "sc": 1, "st": 0, "obc": 0, "ews": 0, "ur": 0, "total": 1, "level": "Level-6", "group": "C"},
    "Nuclear Medicine Technologist": {"advt": "I/08/4/Rectt/2025-26", "sc": 2, "st": 0, "obc": 2, "ews": 0, "ur": 3, "total": 7, "level": "Level-5", "group": "C"},
    "Store Keeper": {"advt": "I/08/5/Rectt/2025-26", "sc": 5, "st": 0, "obc": 6, "ews": 2, "ur": 9, "total": 22, "level": "Level-6", "group": "C"},
    "Medical Social Service Officer Gr-II": {"advt": "I/08/6/Rectt/2025-26", "sc": 0, "st": 0, "obc": 0, "ews": 0, "ur": 2, "total": 2, "level": "Level-6", "group": "C"},
    "Senior Administrative Assistant": {"advt": "I/08/7/Rectt/2025-26", "sc": 7, "st": 1, "obc": 8, "ews": 3, "ur": 13, "total": 32, "level": "Level-4", "group": "C"},
    "Stenographer": {"advt": "I/08/8/Rectt/2025-26", "sc": 13, "st": 1, "obc": 18, "ews": 6, "ur": 26, "total": 64, "level": "Level-4", "group": "C"},
    "CSSD Assistant": {"advt": "I/08/9/Rectt/2025-26", "sc": 4, "st": 0, "obc": 6, "ews": 2, "ur": 8, "total": 20, "level": "Level-4", "group": "C"},
    "Draftsman": {"advt": "I/08/10/Rectt/2025-26", "sc": 0, "st": 0, "obc": 0, "ews": 0, "ur": 1, "total": 1, "level": "Level-4", "group": "C"},
    "Hospital Attendant Gr-II": {"advt": "I/08/11/Rectt/2025-26", "sc": 9, "st": 0, "obc": 13, "ews": 4, "ur": 17, "total": 43, "level": "Level-1", "group": "D"},
    "O.T. Assistant": {"advt": "I/08/12/Rectt/2025-26", "sc": 21, "st": 2, "obc": 30, "ews": 0, "ur": 28, "total": 81, "level": "Level-5", "group": "C"},
}

def safe(n):
    return re.sub(r'[^\w\s-]', '', n).strip().replace(' ', '_').replace('.', '')

def process_and_export(subj_name, safe_name, records, filename_tag, source_label, is_combined=True):
    sorted_recs = sorted(records, key=lambda x: x["Marks"], reverse=True)
    for i, r in enumerate(sorted_recs):
        r["Rank"] = i + 1
    total = len(sorted_recs)
    for r in sorted_recs:
        r["Percentile"] = round((1 - (r["Rank"] - 1) / total) * 100, 2)

    sorted_by_roll = sorted(sorted_recs, key=lambda x: int(x["Roll_No"]))

    if is_combined:
        csv_dir = data_combined
        html_dir = html_combined
        csv_rel = f"data/combined/{filename_tag}_analysis.csv"
    else:
        csv_dir = data_per_day
        html_dir = html_per_day
        csv_rel = f"data/per_day/{filename_tag}_analysis.csv"

    csv_path = csv_dir / f"{filename_tag}_analysis.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Day", "Exam_Date", "Rank", "Registration_No", "Roll_No", "Marks", "Percentile"])
        writer.writeheader()
        writer.writerows(sorted_by_roll)

    marks_list = [r["Marks"] for r in sorted_recs]
    sorted_desc = sorted(marks_list, reverse=True)
    avg = sum(marks_list) / total
    std = (sum((m - avg)**2 for m in marks_list) / total) ** 0.5
    sorted_asc = sorted(marks_list)
    median = sorted_asc[total // 2] if total % 2 else (sorted_asc[total//2-1] + sorted_asc[total//2])/2
    pos = sum(1 for m in marks_list if m >= 0)
    neg = total - pos

    cutoffs = {}
    for p in [1, 5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 99]:
        idx = max(0, min(total - 1, total * (100 - p) // 100))
        cutoffs[f"Top {p}%"] = round(sorted_desc[idx], 2)

    vac = VACANCIES.get(subj_name, {})
    stats = {
        "name": subj_name, "total": total,
        "highest": round(max(marks_list), 2), "lowest": round(min(marks_list), 2),
        "average": round(avg, 2), "median": round(median, 2), "std_dev": round(std, 2),
        "positive": pos, "negative": neg, "cutoffs": cutoffs,
        "advt": vac.get("advt", ""), "vac_total": vac.get("total", 0),
        "sc": vac.get("sc", 0), "st": vac.get("st", 0), "obc": vac.get("obc", 0),
        "ews": vac.get("ews", 0), "ur": vac.get("ur", 0),
        "level": vac.get("level", ""), "group": vac.get("group", "")
    }

    days_count = len(set(r.get("Day", "") for r in sorted_recs))
    show_day_col = "true" if days_count > 1 else "false"

    gen_html(subj_name, safe_name, sorted_recs, stats, filename_tag, source_label, csv_rel, html_dir, show_day_col)
    print(f"  [{source_label}] CSV+HTML: {csv_path.name}")

def gen_html(subj_name, safe_name, sorted_recs, stats, filename_tag, source_label, csv_rel, html_dir, show_day_col="true"):
    total = stats["total"]
    day_th = "<th>Day</th>" if show_day_col == "true" else ""
    all_json = json.dumps([{
        "rank": r["Rank"], "day": r.get("Day", ""),
        "reg": r["Registration_No"], "roll": r["Roll_No"],
        "marks": r["Marks"], "pctl": r["Percentile"]
    } for r in sorted_recs])
    cutoffs_json = json.dumps(stats["cutoffs"])
    header_suffix = f" ({source_label})" if source_label != "Combined" else ""
    back_link = "../../index.html"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subj_name}{header_suffix} - Analysis</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
:root {{ --bg: #e8eaf0; --surface: #fff; --text: #222; --text2: #555; --accent: #1a237e; --accent2: #283593; --border: #d0d4dc; --bar-bg: #d0d4dc; --hover-bg: #f0f2f8; --input-bg: #fff; }}
body.dark {{ --bg: #121212; --surface: #1e1e1e; --text: #e0e0e0; --text2: #aaa; --accent: #7c8cdb; --accent2: #5c6bc0; --border: #333; --bar-bg: #333; --hover-bg: #2a2a35; --input-bg: #2a2a2a; }}
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
.vacancy-box {{ background: var(--surface); padding: 12px 16px; border: 1px solid var(--border); margin-bottom: 14px; display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: center; font-size: 13px; }}
.vacancy-box .vac-tag {{ background: var(--hover-bg); color: var(--accent); padding: 2px 8px; font-weight: 600; font-size: 11px; }}
.vacancy-box .vac-advt {{ color: var(--text2); }}
.vacancy-box .vac-cat {{ display: inline-flex; align-items: center; gap: 4px; }}
.vacancy-box .vac-cat span {{ background: var(--hover-bg); padding: 2px 6px; font-size: 11px; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 16px; }}
.stat-card {{ background: var(--surface); padding: 14px; text-align: center; border: 1px solid var(--border); }}
.stat-card .label {{ font-size: 10px; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; }}
.stat-card .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; color: var(--accent); }}
.stat-card .value.green {{ color: #2e7d32; }}
.stat-card .value.red {{ color: #c62828; }}
body.dark .stat-card .value.green {{ color: #66bb6a; }}
body.dark .stat-card .value.red {{ color: #ef5350; }}
.search-section {{ background: var(--surface); padding: 14px 16px; border: 1px solid var(--border); margin-bottom: 14px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
.search-section input {{ flex: 1; min-width: 180px; padding: 8px 12px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 13px; outline: none; }}
.search-section input:focus {{ border-color: var(--accent); }}
.search-section button {{ padding: 8px 20px; background: var(--accent); color: var(--surface); border: none; cursor: pointer; font-size: 13px; font-weight: 600; }}
.search-section button:hover {{ background: var(--accent2); }}
.search-result {{ background: var(--surface); border: 1px solid var(--border); margin-bottom: 14px; display: none; }}
.search-result.show {{ display: block; }}
.search-result-header {{ background: var(--accent); color: var(--surface); padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; }}
.search-result-header h2 {{ font-size: 15px; }}
.search-result-header .close-btn {{ background: rgba(255,255,255,0.2); border: none; color: var(--surface); width: 26px; height: 26px; cursor: pointer; font-size: 16px; line-height: 1; }}
.search-result-body {{ padding: 14px 16px; display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; }}
.search-stat {{ text-align: center; padding: 10px; background: var(--hover-bg); }}
.search-stat .label {{ font-size: 10px; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; }}
.search-stat .value {{ font-size: 18px; font-weight: 700; margin-top: 4px; color: var(--accent); }}
.search-stat .value.green {{ color: #2e7d32; }}
.search-stat .value.red {{ color: #c62828; }}
.search-stat .value.orange {{ color: #e65100; }}
body.dark .search-stat .value.green {{ color: #66bb6a; }}
body.dark .search-stat .value.red {{ color: #ef5350; }}
body.dark .search-stat .value.orange {{ color: #ffb74d; }}
.rank-gauge-wrap {{ padding: 0 16px 14px; }}
.rank-gauge {{ height: 6px; background: var(--bar-bg); }}
.rank-gauge-fill {{ height: 100%; background: linear-gradient(90deg, #c62828, #e65100, #f9a825, #2e7d32); transition: width 0.6s ease; }}
.rank-gauge-label {{ display: flex; justify-content: space-between; font-size: 10px; color: var(--text2); margin-top: 2px; }}
.tabs {{ display: flex; gap: 4px; margin-bottom: 12px; flex-wrap: wrap; }}
.tab-btn {{ padding: 6px 16px; border: 1px solid var(--border); background: var(--surface); color: var(--text); cursor: pointer; font-size: 12px; font-weight: 600; }}
.tab-btn.active {{ background: var(--accent); color: var(--surface); border-color: var(--accent); }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; min-width: 0; }}
.chart-box {{ background: var(--surface); padding: 14px; border: 1px solid var(--border); min-width: 0; overflow: hidden; }}
.chart-box.full {{ grid-column: 1 / -1; }}
.chart-box h3 {{ font-size: 13px; margin-bottom: 8px; color: var(--text); }}
canvas {{ width: 100% !important; max-width: 100%; height: auto !important; max-height: 300px; }}
.table-wrap {{ background: var(--surface); padding: 14px; border: 1px solid var(--border); overflow-x: auto; margin-bottom: 14px; }}
.table-wrap h3 {{ font-size: 13px; margin-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th {{ background: var(--accent); color: var(--surface); padding: 7px 8px; text-align: left; font-weight: 600; white-space: nowrap; }}
td {{ padding: 5px 8px; border-bottom: 1px solid var(--border); }}
tr:hover td {{ background: var(--hover-bg); }}
.rank-badge {{ background: var(--accent); color: var(--surface); padding: 1px 6px; font-size: 11px; font-weight: 600; }}
.day-badge {{ background: var(--hover-bg); color: var(--accent); padding: 1px 6px; font-size: 10px; font-weight: 600; }}
.pagination {{ display: flex; justify-content: center; gap: 4px; margin-top: 10px; flex-wrap: wrap; }}
.pagination button {{ padding: 4px 10px; border: 1px solid var(--border); background: var(--surface); color: var(--text); cursor: pointer; font-size: 12px; }}
.pagination button.active {{ background: var(--accent); color: var(--surface); border-color: var(--accent); }}
.pagination button:hover:not(.active) {{ background: var(--hover-bg); }}
.filter-input {{ padding: 7px 12px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 12px; width: 240px; outline: none; }}
.filter-input:focus {{ border-color: var(--accent); }}
@media (max-width: 900px) {{ .charts-row {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
<div class="header-row">
<div><a class="back-link" href="{back_link}">&larr; Back to All Positions</a><h1>{subj_name}{header_suffix}</h1></div>
<label class="toggle"><span>Dark</span><input type="checkbox" id="darkToggle"><span class="slider"></span></label>
</div>
<p class="subtitle">SGPGIMS Raw Score Analysis</p>

<div class="vacancy-box" id="vacancyBox"></div>

<div class="stats-grid" id="statsGrid"></div>

<div class="search-section">
<input id="candidateSearchInput" type="text" placeholder="Enter Registration No or Roll No..." onkeydown="if(event.key==='Enter') searchCandidate()">
<button onclick="searchCandidate()">Search</button>
</div>

<div class="search-result" id="searchResult">
<div class="search-result-header">
<h2 id="searchResultTitle">Candidate Details</h2>
<button class="close-btn" onclick="closeSearch()">&times;</button>
</div>
<div class="search-result-body" id="searchResultBody"></div>
<div class="rank-gauge-wrap" id="rankGaugeWrap">
<div class="rank-gauge"><div class="rank-gauge-fill" id="rankGaugeFill" style="width:0%"></div></div>
<div class="rank-gauge-label"><span>Last (Rank {total})</span><span id="gaugeMiddleLabel">Middle</span><span>Topper (Rank 1)</span></div>
</div>
</div>

<div class="tabs">
<button class="tab-btn active" onclick="switchTab('charts')">Charts</button>
<button class="tab-btn" onclick="switchTab('top100')">Top 100</button>
<button class="tab-btn" onclick="switchTab('all')">All Candidates</button>
</div>

<div id="tab-charts" class="tab-content active">
<div class="charts-row">
<div class="chart-box"><h3>Marks Distribution</h3><canvas id="distChart"></canvas></div>
<div class="chart-box"><h3>Percentile Curve</h3><canvas id="pctlChart"></canvas></div>
</div>
<div class="charts-row">
<div class="chart-box"><h3>Top 20 Rankers</h3><canvas id="topChart"></canvas></div>
<div class="chart-box"><h3>Percentile Cutoffs</h3><canvas id="cutoffChart"></canvas></div>
</div>
<div class="table-wrap full">
<h3>Percentile Cutoff Table</h3>
<table><thead><tr><th>Rank Group</th><th>Minimum Marks</th></tr></thead>
<tbody id="cutoffTableBody"></tbody></table>
</div>
</div>

<div id="tab-top100" class="tab-content">
<div class="table-wrap">
<h3>Top 100 Candidates</h3>
<table><thead><tr><th>Rank</th>{day_th}<th>Registration No</th><th>Roll No</th><th>Marks</th><th>Percentile</th></tr></thead>
<tbody id="top100Body"></tbody></table>
</div>
</div>

<div id="tab-all" class="tab-content">
<div class="table-wrap">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
<h3 style="margin:0">All Candidates</h3>
<input id="searchInput" type="text" placeholder="Filter by Reg No or Roll No..." class="filter-input" oninput="filterTable()">
</div>
<table><thead><tr><th>Rank</th>{day_th}<th>Registration No</th><th>Roll No</th><th>Marks</th><th>Percentile</th></tr></thead>
<tbody id="allBody"></tbody></table>
<div class="pagination" id="pagination"></div>
</div>
</div>
</div>

<script>
const PAGE_SIZE = 50;
let allData = {all_json};
let currentPage = 1;
const stats = {json.dumps(stats)};
const cutoffs = {cutoffs_json};
const showDay = {show_day_col};

function loadData() {{
renderVacancy(); renderStats(); renderDistChart(); renderPctlChart();
renderTopChart(); renderCutoffChart(); renderCutoffTable();
renderTop100(); renderTable(1);
}}

function renderVacancy() {{
const v = stats;
if (!v.advt) return;
document.getElementById('vacancyBox').innerHTML = `
<span class="vac-advt"><strong>Advt:</strong> ${{v.advt}}</span>
<span class="vac-tag">${{v.level}} / Group ${{v.group}}</span>
<span class="vac-tag">Total Vacancies: ${{v.vac_total}}</span>
<span class="vac-cat"><span>SC ${{v.sc}}</span><span>ST ${{v.st}}</span><span>OBC ${{v.obc}}</span><span>EWS ${{v.ews}}</span><span>UR ${{v.ur}}</span></span>
`;
}}

function renderStats() {{
document.getElementById('statsGrid').innerHTML = `
<div class="stat-card"><div class="label">Total Candidates</div><div class="value">${{stats.total}}</div></div>
<div class="stat-card"><div class="label">Highest Marks</div><div class="value green">${{stats.highest}}</div></div>
<div class="stat-card"><div class="label">Lowest Marks</div><div class="value red">${{stats.lowest}}</div></div>
<div class="stat-card"><div class="label">Average Marks</div><div class="value">${{stats.average}}</div></div>
<div class="stat-card"><div class="label">Median Marks</div><div class="value">${{stats.median}}</div></div>
<div class="stat-card"><div class="label">Std Deviation</div><div class="value">${{stats.std_dev}}</div></div>
<div class="stat-card"><div class="label">Positive Scores</div><div class="value green">${{stats.positive}}</div></div>
<div class="stat-card"><div class="label">Negative Scores</div><div class="value red">${{stats.negative}}</div></div>
`;
}}

function renderDistChart() {{
const marks = allData.map(d => d.marks);
const mn = Math.floor(Math.min(...marks));
const mx = Math.ceil(Math.max(...marks));
const binSize = 5;
const bins = [];
for (let s = mn; s <= mx; s += binSize) bins.push({{ label: `${{s}}-${{s+binSize}}`, count: 0 }});
marks.forEach(m => {{
const idx = Math.min(bins.length - 1, Math.max(0, Math.floor((m - mn) / binSize)));
bins[idx].count++;
}});
new Chart(document.getElementById('distChart'), {{
type: 'bar',
data: {{ labels: bins.map(b => b.label), datasets: [{{ label: 'Candidates', data: bins.map(b => b.count), backgroundColor: 'rgba(26, 35, 126, 0.7)', borderColor: '#1a237e', borderWidth: 1 }}] }},
options: {{ responsive: true, maintainAspectRatio: true, aspectRatio: 1.6, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'Marks Range' }} }}, y: {{ title: {{ display: true, text: 'Candidates' }}, beginAtZero: true }} }} }}
}});
}}

function renderPctlChart() {{
const sorted = [...allData].sort((a,b) => a.marks - b.marks);
const pts = sorted.map((d,i) => ({{ pctl: ((i+1)/sorted.length)*100, marks: d.marks }}));
new Chart(document.getElementById('pctlChart'), {{
type: 'line',
data: {{ labels: pts.map(d => d.pctl.toFixed(0)), datasets: [{{ label: 'Marks', data: pts.map(d => d.marks), borderColor: '#1a237e', backgroundColor: 'rgba(26,35,126,0.1)', fill: true, tension: 0.4, pointRadius: 0 }}] }},
options: {{ responsive: true, maintainAspectRatio: true, aspectRatio: 1.6, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'Percentile' }} }}, y: {{ title: {{ display: true, text: 'Marks' }} }} }} }}
}});
}}

function renderTopChart() {{
const top = allData.slice(0, 20);
new Chart(document.getElementById('topChart'), {{
type: 'bar',
data: {{ labels: top.map(d => d.reg), datasets: [{{ label: 'Marks', data: top.map(d => d.marks), backgroundColor: 'rgba(46, 125, 50, 0.7)', borderColor: '#2e7d32', borderWidth: 1 }}] }},
options: {{ responsive: true, maintainAspectRatio: true, aspectRatio: 1.2, indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'Marks' }}, beginAtZero: true }}, y: {{ title: {{ display: true, text: 'Registration No' }} }} }} }}
}});
}}

function renderCutoffChart() {{
const labels = Object.keys(cutoffs);
const vals = Object.values(cutoffs);
new Chart(document.getElementById('cutoffChart'), {{
type: 'bar',
data: {{ labels, datasets: [{{ label: 'Min Marks', data: vals, backgroundColor: 'rgba(198, 40, 40, 0.7)', borderColor: '#c62828', borderWidth: 1 }}] }},
options: {{ responsive: true, maintainAspectRatio: true, aspectRatio: 1.6, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'Category' }} }}, y: {{ title: {{ display: true, text: 'Marks' }}, beginAtZero: true }} }} }}
}});
}}

function renderCutoffTable() {{
document.getElementById('cutoffTableBody').innerHTML = Object.entries(cutoffs).map(([k,v]) => `<tr><td><strong>${{k}}</strong></td><td>${{v}}</td></tr>`).join('');
}}

function renderTop100() {{
document.getElementById('top100Body').innerHTML = allData.slice(0, 100).map(d => `<tr><td><span class="rank-badge">#${{d.rank}}</span></td>${{showDay?`<td><span class="day-badge">${{d.day||''}}</span></td>`:''}}<td>${{d.reg}}</td><td>${{d.roll}}</td><td><strong>${{d.marks.toFixed(2)}}</strong></td><td>${{d.pctl.toFixed(2)}}</td></tr>`).join('');
}}

function renderTable(page) {{
currentPage = page;
const start = (page - 1) * PAGE_SIZE;
const end = Math.min(start + PAGE_SIZE, allData.length);
const tbody = document.getElementById('allBody');
tbody.innerHTML = allData.slice(start, end).map(d => `<tr><td><span class="rank-badge">#${{d.rank}}</span></td>${{showDay?`<td><span class="day-badge">${{d.day||''}}</span></td>`:''}}<td>${{d.reg}}</td><td>${{d.roll}}</td><td><strong>${{d.marks.toFixed(2)}}</strong></td><td>${{d.pctl.toFixed(2)}}</td></tr>`).join('');
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
const filtered = q ? allData.filter(d => d.reg.toLowerCase().includes(q) || d.roll.includes(q)) : allData;
const tbody = document.getElementById('allBody');
if (q) {{
tbody.innerHTML = filtered.map(d => `<tr><td><span class="rank-badge">#${{d.rank}}</span></td>${{showDay?`<td><span class="day-badge">${{d.day||''}}</span></td>`:''}}<td>${{d.reg}}</td><td>${{d.roll}}</td><td><strong>${{d.marks.toFixed(2)}}</strong></td><td>${{d.pctl.toFixed(2)}}</td></tr>`).join('');
document.getElementById('pagination').innerHTML = '';
}} else {{ renderTable(1); }}
}}

function searchCandidate() {{
const q = document.getElementById('candidateSearchInput').value.trim().toLowerCase();
if (!q) return;
const d = allData.find(x => x.reg.toLowerCase() === q || x.roll === q);
const result = document.getElementById('searchResult');
const body = document.getElementById('searchResultBody');
const title = document.getElementById('searchResultTitle');
const gauge = document.getElementById('rankGaugeFill');
const midLabel = document.getElementById('gaugeMiddleLabel');
if (!d) {{
title.textContent = 'Candidate Not Found';
body.innerHTML = `<div class="search-stat" style="grid-column:1/-1;padding:30px;"><div class="label">No candidate found: "${{q}}"</div></div>`;
gauge.style.width = '0%'; result.classList.add('show'); return;
}}
const total = allData.length;
const above = d.rank - 1;
const below = total - d.rank;
const pctPos = ((total - d.rank) / (total - 1)) * 100;
title.textContent = `${{d.reg}} — ${{d.roll}} ${{d.day ? '('+d.day+')' : ''}}`;
body.innerHTML = `
<div class="search-stat"><div class="label">Rank</div><div class="value">#${{d.rank}} / ${{total}}</div></div>
<div class="search-stat"><div class="label">Marks</div><div class="value ${{d.marks >= 0 ? 'green' : 'red'}}">${{d.marks.toFixed(2)}}</div></div>
<div class="search-stat"><div class="label">Percentile</div><div class="value">${{d.pctl.toFixed(2)}}%</div></div>
<div class="search-stat"><div class="label">Scored Above</div><div class="value green">${{above}}</div></div>
<div class="search-stat"><div class="label">Scored Below</div><div class="value orange">${{below}}</div></div>
<div class="search-stat"><div class="label">Top %</div><div class="value">${{(above/total*100).toFixed(1)}}%</div></div>
`;
gauge.style.width = `${{Math.max(1, pctPos)}}%`;
midLabel.textContent = `You are here (${{d.rank}} of ${{total}})`;
result.classList.add('show');
result.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
}}

function closeSearch() {{
document.getElementById('searchResult').classList.remove('show');
document.getElementById('candidateSearchInput').value = '';
}}

function switchTab(tab) {{
document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
document.querySelector(`.tab-btn[onclick*='${{tab}}']`).classList.add('active');
document.getElementById(`tab-${{tab}}`).classList.add('active');
}}

loadData();
const t = document.getElementById('darkToggle');
const m = window.matchMedia('(prefers-color-scheme:dark)');
t.checked = localStorage.getItem('dark') === '1' || (!localStorage.getItem('dark') && m.matches);
t.onchange = () => {{ document.body.classList.toggle('dark', t.checked); localStorage.setItem('dark', t.checked ? '1' : '0'); }};
if (t.checked) document.body.classList.add('dark');
</script>
</body>
</html>"""
    html_path = html_dir / f"{filename_tag}_analysis.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

def gen_index(all_positions):
    all_pos_names = set(all_positions.keys()) | set(VACANCIES.keys())
    position_days = {}
    for pos_name in all_pos_names:
        records = all_positions.get(pos_name, [])
        days = sorted(set(r["Day"] for r in records))
        exams = sorted(set(r["Exam_Date"] for r in records))
        safe_name = safe(pos_name)
        position_days[pos_name] = {"total": len(records), "days": days, "exams": exams, "safe": safe_name}

    total_all = sum(pd["total"] for pd in position_days.values())
    all_totals = [pd["total"] for pd in position_days.values()]
    max_total = max(all_totals) if all_totals else 1

    def sort_key(item):
        pos_name, info = item
        return (0 if info["total"] > 0 else 1, -info["total"])

    cards = ""
    for pos_name, info in sorted(position_days.items(), key=sort_key):
        safe_name = info["safe"]
        days_html = "".join(f'<span class="day-pill">{d}</span>' for d in info["days"])
        vac = VACANCIES.get(pos_name, {})
        total = info["total"]
        records = all_positions.get(pos_name, [])

        if total > 0:
            if len(info["days"]) > 1:
                card_link = f"analysis/combined/{safe_name}_analysis.html"
            else:
                d = list(info["days"])[0]
                ds = d.lower().replace(" ", "_").replace("(", "").replace(")", "")
                card_link = f"analysis/per_day/{safe_name}_{ds}_analysis.html"
            marks_list = [r["Marks"] for r in records]
            avg = sum(marks_list) / total
            highest = max(marks_list)
            median = sorted(marks_list)[total // 2]
            stat_line = f'<span class="stat">{total} candidates</span><span class="stat-sep">|</span><span class="stat">Avg {avg:.2f}</span><span class="stat-sep">|</span><span class="stat">Highest {highest:.2f}</span><span class="stat-sep">|</span><span class="stat">Median {median:.2f}</span>'
        else:
            card_link = ""
            stat_line = '<span class="stat">No exam data</span>'

        day_links = ""
        if total > 0 and len(info["days"]) > 1:
            for d in info["days"]:
                ds = d.lower().replace(" ", "_").replace("(", "").replace(")", "")
                dc = sum(1 for r in all_positions[pos_name] if r["Day"] == d)
                day_links += f'<a href="analysis/per_day/{safe_name}_{ds}_analysis.html">{d}</a>'

        vac_line = ""
        if vac:
            cats = f'SC {vac["sc"]} ST {vac["st"]} OBC {vac["obc"]} EWS {vac["ews"]} UR {vac["ur"]}'
            vac_line = f'<div class="vac-line"><span class="vac-pill">{vac["level"]} / Gr {vac["group"]}</span><span class="vac-pill">{vac["advt"]}</span><span class="vac-pill">Vacancies: {vac["total"]} ({cats})</span></div>'

        width_pct = total / max_total * 100 if max_total else 0
        card_tag = "a" if card_link else "div"
        extra_attr = f'href="{card_link}"' if card_link else ""

        cards += f"""
        <{card_tag} class="pos-card" {extra_attr}>
            <div class="pos-name">{pos_name}</div>
            <div class="pos-stats">{stat_line}</div>
            {vac_line}
            <div class="pos-meta"><div class="day-pills">{days_html}</div>{'<div class="day-links">'+day_links+'</div>' if day_links else ''}</div>
            <div class="pos-bar"><div class="pos-bar-fill" style="width:{width_pct}%"></div></div>
        </{card_tag}>"""

    total_exams = sorted(set(e for pd in position_days.values() for e in pd["exams"]))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SGPGIMS Exam Results</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
:root {{ --bg: #e8eaf0; --surface: #fff; --text: #222; --text2: #555; --accent: #1a237e; --accent2: #283593; --border: #d0d4dc; --bar-bg: #d0d4dc; --pill-bg: #eef0f6; --pill-text: #1a237e; --vac-bg: #fff3e0; --vac-text: #e65100; }}
body.dark {{ --bg: #121212; --surface: #1e1e1e; --text: #e0e0e0; --text2: #aaa; --accent: #7c8cdb; --accent2: #5c6bc0; --border: #333; --bar-bg: #333; --pill-bg: #2a2a3a; --pill-text: #7c8cdb; --vac-bg: #2a2010; --vac-text: #ffb74d; }}
body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); padding: 24px; transition: background 0.2s, color 0.2s; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
.header {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 6px; }}
h1 {{ font-size: 26px; color: var(--accent); }}
.toggle {{ display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer; color: var(--text2); user-select: none; }}
.toggle input {{ display: none; }}
.toggle .slider {{ width: 40px; height: 22px; background: var(--border); position: relative; cursor: pointer; transition: 0.2s; }}
.toggle .slider::after {{ content: ''; position: absolute; width: 16px; height: 16px; background: var(--surface); top: 3px; left: 3px; transition: 0.2s; }}
.toggle input:checked + .slider {{ background: var(--accent); }}
.toggle input:checked + .slider::after {{ left: 21px; }}
.subtitle {{ color: var(--text2); margin-bottom: 4px; font-size: 14px; }}
.exam-list {{ color: var(--text2); margin-bottom: 20px; font-size: 13px; }}
.exam-list strong {{ color: var(--accent); }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; }}
.pos-card {{ display: block; background: var(--surface); padding: 18px 20px; text-decoration: none; color: inherit; box-shadow: 0 1px 4px rgba(0,0,0,0.06); transition: box-shadow 0.15s, transform 0.15s; border: 1px solid var(--border); }}
.pos-card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.1); transform: translateY(-2px); }}
.pos-name {{ font-size: 18px; font-weight: 700; color: var(--accent); }}
.pos-stats {{ font-size: 12px; color: var(--text2); margin-top: 4px; display: flex; gap: 4px; flex-wrap: wrap; align-items: center; }}
.stat-sep {{ color: var(--border); }}
.vac-line {{ margin-top: 6px; display: flex; gap: 4px; flex-wrap: wrap; }}
.vac-pill {{ background: var(--vac-bg); color: var(--vac-text); font-size: 10px; font-weight: 600; padding: 2px 8px; }}
.pos-meta {{ margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
.day-pills {{ display: flex; gap: 4px; flex-wrap: wrap; }}
.day-pill {{ background: var(--pill-bg); color: var(--pill-text); font-size: 10px; font-weight: 600; padding: 2px 8px; }}
.day-links {{ display: flex; gap: 4px; flex-wrap: wrap; }}
.day-links a {{ padding: 2px 10px; background: var(--accent); color: var(--surface); text-decoration: none; font-size: 11px; font-weight: 600; transition: background 0.15s; }}
.day-links a:hover {{ background: var(--accent2); }}
.pos-bar {{ height: 3px; background: var(--bar-bg); margin-top: 12px; }}
.pos-bar-fill {{ height: 100%; background: var(--accent); }}
.total-badge {{ text-align: center; margin-bottom: 18px; font-size: 14px; color: var(--text2); }}
.total-badge strong {{ color: var(--accent); }}
@media (max-width: 720px) {{ .grid {{ grid-template-columns: 1fr; }} body {{ padding: 16px; }} h1 {{ font-size: 22px; }} }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>SGPGIMS Exam Results</h1>
<label class="toggle"><span>Dark</span><input type="checkbox" id="darkToggle"><span class="slider"></span></label>
</div>
<p class="subtitle">Raw Score Analysis &mdash; Advt I/08/1-12/Rectt/2025-26</p>
<div class="exam-list">Exams: <strong>{', '.join(total_exams)}</strong></div>
<div class="total-badge">Total Candidates: <strong>{total_all}</strong> across {len(position_days)} positions</div>
<div class="grid">{cards}</div>
</div>
<script>
const t = document.getElementById('darkToggle');
const m = window.matchMedia('(prefers-color-scheme:dark)');
t.checked = localStorage.getItem('dark') === '1' || (!localStorage.getItem('dark') && m.matches);
t.onchange = () => {{ document.body.classList.toggle('dark', t.checked); localStorage.setItem('dark', t.checked ? '1' : '0'); }};
if (t.checked) document.body.classList.add('dark');
</script>
</body>
</html>"""
    html_path = out_dir / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nIndex HTML: index.html")

pdfs = [
    (r"C:\Users\Sarvagya\Desktop\sgpgi_data\raw\Day1_Raw_Score_19_July_2026.pdf", "Day 1 (19 July 2026)", "19 July 2026"),
    (r"C:\Users\Sarvagya\Desktop\sgpgi_data\raw\Day2_Raw_Score_20_June_2026.pdf", "Day 2 (20 June 2026)", "20 June 2026"),
    (r"C:\Users\Sarvagya\Desktop\sgpgi_data\raw\Day3_Raw_Score_21_June_2026.pdf", "Day 3 (21 June 2026)", "21 June 2026"),
]

all_positions = defaultdict(list)

for pdf_path, day_label, exam_date in pdfs:
    doc = fitz.open(pdf_path)
    all_text = ""
    for page in doc:
        all_text += page.get_text() + "\n"

    pattern = r"(SG\d+)\s+(\d+)\s+([-\d.]+)\s+(.+)"
    matches = re.findall(pattern, all_text)

    day_records = defaultdict(list)
    for reg, roll, marks, subj in matches:
        subj = subj.strip()
        rec = {
            "Day": day_label,
            "Exam_Date": exam_date,
            "Registration_No": reg,
            "Roll_No": roll,
            "Marks": float(marks)
        }
        day_records[subj].append(rec)
        all_positions[subj].append(rec)

    for subj_name, records in sorted(day_records.items()):
        safe_name = re.sub(r'[^\w\s-]', '', subj_name).strip().replace(' ', '_').replace('.', '')
        day_safe = day_label.lower().replace(' ', '_').replace('(', '').replace(')', '')
        filename_tag = f"{safe_name}_{day_safe}"
        process_and_export(subj_name, safe_name, records, filename_tag, day_label, is_combined=False)

    print(f"  Processed: {day_label} ({exam_date}) — {len(matches)} records across {len(day_records)} positions")

for subj_name, records in sorted(all_positions.items()):
    safe_name = re.sub(r'[^\w\s-]', '', subj_name).strip().replace(' ', '_').replace('.', '')
    process_and_export(subj_name, safe_name, records, safe_name, "Combined", is_combined=True)
    print(f"  Combined: {subj_name} — {len(records)} records")

gen_index(all_positions)
print("\nAll done!")

