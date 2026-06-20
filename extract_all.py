import fitz, re, csv, json
from pathlib import Path
from collections import defaultdict

out_dir = Path(r"C:\Users\Sarvagya\Desktop\sgpgi_data")

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

def process_and_export(subj_name, safe_name, records, filename_tag, source_label):
    sorted_recs = sorted(records, key=lambda x: x["Marks"], reverse=True)
    for i, r in enumerate(sorted_recs):
        r["Rank"] = i + 1
    total = len(sorted_recs)
    for r in sorted_recs:
        r["Percentile"] = round((1 - (r["Rank"] - 1) / total) * 100, 2)

    sorted_by_roll = sorted(sorted_recs, key=lambda x: int(x["Roll_No"]))

    csv_path = out_dir / f"{filename_tag}_analysis.csv"
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

    gen_html(subj_name, safe_name, sorted_recs, stats, filename_tag, source_label)
    print(f"  [{source_label}] CSV+HTML: {csv_path.name}")

def gen_html(subj_name, safe_name, sorted_recs, stats, filename_tag, source_label):
    total = stats["total"]
    all_json = json.dumps([{
        "rank": r["Rank"], "day": r.get("Day", ""),
        "reg": r["Registration_No"], "roll": r["Roll_No"],
        "marks": r["Marks"], "pctl": r["Percentile"]
    } for r in sorted_recs])
    cutoffs_json = json.dumps(stats["cutoffs"])
    header_suffix = f" ({source_label})" if source_label != "Combined" else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subj_name}{header_suffix} - Analysis</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; color: #333; padding: 20px; }}
.container {{ max-width: 1400px; margin: 0 auto; }}
h1 {{ text-align: center; margin-bottom: 4px; color: #1a237e; font-size: 26px; }}
.subtitle {{ text-align: center; color: #666; margin-bottom: 20px; font-size: 13px; }}
.back-link {{ display: inline-block; margin-bottom: 12px; color: #1a237e; text-decoration: none; font-size: 13px; font-weight: 600; }}
.back-link:hover {{ text-decoration: underline; }}
.vacancy-box {{ background: white; border-radius: 10px; padding: 14px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 8px 20px; align-items: center; font-size: 13px; }}
.vacancy-box .vac-tag {{ background: #e8eaf6; color: #1a237e; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; }}
.vacancy-box .vac-advt {{ color: #555; }}
.vacancy-box .vac-cat {{ display: inline-flex; align-items: center; gap: 4px; }}
.vacancy-box .vac-cat span {{ background: #f5f5ff; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.stat-card {{ background: white; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.stat-card .label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
.stat-card .value {{ font-size: 24px; font-weight: 700; margin-top: 4px; color: #1a237e; }}
.stat-card .value.green {{ color: #2e7d32; }}
.stat-card .value.red {{ color: #c62828; }}
.search-section {{ background: white; border-radius: 10px; padding: 16px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
.search-section input {{ flex: 1; min-width: 200px; padding: 9px 14px; border: 2px solid #ddd; border-radius: 8px; font-size: 13px; outline: none; }}
.search-section input:focus {{ border-color: #1a237e; }}
.search-section button {{ padding: 9px 22px; background: #1a237e; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; }}
.search-section button:hover {{ background: #283593; }}
.search-result {{ background: white; border-radius: 10px; padding: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; overflow: hidden; display: none; }}
.search-result.show {{ display: block; }}
.search-result-header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; }}
.search-result-header h2 {{ font-size: 16px; }}
.search-result-header .close-btn {{ background: rgba(255,255,255,0.2); border: none; color: white; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-size: 16px; line-height: 1; }}
.search-result-body {{ padding: 16px 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }}
.search-stat {{ text-align: center; padding: 10px; background: #f5f5ff; border-radius: 8px; }}
.search-stat .label {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
.search-stat .value {{ font-size: 20px; font-weight: 700; margin-top: 4px; color: #1a237e; }}
.search-stat .value.green {{ color: #2e7d32; }}
.search-stat .value.red {{ color: #c62828; }}
.search-stat .value.orange {{ color: #e65100; }}
.rank-gauge-wrap {{ padding: 0 20px 16px; }}
.rank-gauge {{ height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; }}
.rank-gauge-fill {{ height: 100%; background: linear-gradient(90deg, #c62828, #e65100, #f9a825, #2e7d32); border-radius: 4px; transition: width 0.6s ease; }}
.rank-gauge-label {{ display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-top: 3px; }}
.tabs {{ display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; }}
.tab-btn {{ padding: 7px 18px; border: none; background: #ddd; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; }}
.tab-btn.active {{ background: #1a237e; color: white; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px; }}
.chart-box {{ background: white; border-radius: 10px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.chart-box.full {{ grid-column: 1 / -1; }}
.chart-box h3 {{ font-size: 14px; margin-bottom: 10px; color: #333; }}
canvas {{ max-height: 300px; }}
.table-wrap {{ background: white; border-radius: 10px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow-x: auto; margin-bottom: 16px; }}
.table-wrap h3 {{ font-size: 14px; margin-bottom: 10px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th {{ background: #1a237e; color: white; padding: 8px 10px; text-align: left; font-weight: 600; white-space: nowrap; }}
td {{ padding: 6px 10px; border-bottom: 1px solid #eee; }}
tr:hover td {{ background: #f5f5ff; }}
.rank-badge {{ background: #1a237e; color: white; border-radius: 4px; padding: 1px 6px; font-size: 11px; font-weight: 600; }}
.day-badge {{ background: #e8eaf6; color: #1a237e; border-radius: 4px; padding: 1px 6px; font-size: 10px; font-weight: 600; }}
.pagination {{ display: flex; justify-content: center; gap: 4px; margin-top: 12px; flex-wrap: wrap; }}
.pagination button {{ padding: 5px 12px; border: 1px solid #ccc; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; }}
.pagination button.active {{ background: #1a237e; color: white; border-color: #1a237e; }}
.pagination button:hover:not(.active) {{ background: #e8eaf6; }}
@media (max-width: 900px) {{ .charts-row {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
<a class="back-link" href="index.html">&larr; Back to All Positions</a>
<h1>{subj_name}{header_suffix}</h1>
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
<table><thead><tr><th>Rank</th><th>Day</th><th>Registration No</th><th>Roll No</th><th>Marks</th><th>Percentile</th></tr></thead>
<tbody id="top100Body"></tbody></table>
</div>
</div>

<div id="tab-all" class="tab-content">
<div class="table-wrap">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
<h3 style="margin:0">All Candidates</h3>
<input id="searchInput" type="text" placeholder="Filter by Reg No or Roll No..." style="padding:7px 12px;border:1px solid #ccc;border-radius:6px;font-size:12px;width:240px;" oninput="filterTable()">
</div>
<table><thead><tr><th>Rank</th><th>Day</th><th>Registration No</th><th>Roll No</th><th>Marks</th><th>Percentile</th></tr></thead>
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
options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'Marks Range' }} }}, y: {{ title: {{ display: true, text: 'Candidates' }}, beginAtZero: true }} }} }}
}});
}}

function renderPctlChart() {{
const sorted = [...allData].sort((a,b) => a.marks - b.marks);
const pts = sorted.map((d,i) => ({{ pctl: ((i+1)/sorted.length)*100, marks: d.marks }}));
new Chart(document.getElementById('pctlChart'), {{
type: 'line',
data: {{ labels: pts.map(d => d.pctl.toFixed(0)), datasets: [{{ label: 'Marks', data: pts.map(d => d.marks), borderColor: '#1a237e', backgroundColor: 'rgba(26,35,126,0.1)', fill: true, tension: 0.4, pointRadius: 0 }}] }},
options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'Percentile' }} }}, y: {{ title: {{ display: true, text: 'Marks' }} }} }} }}
}});
}}

function renderTopChart() {{
const top = allData.slice(0, 20);
new Chart(document.getElementById('topChart'), {{
type: 'bar',
data: {{ labels: top.map(d => d.reg), datasets: [{{ label: 'Marks', data: top.map(d => d.marks), backgroundColor: 'rgba(46, 125, 50, 0.7)', borderColor: '#2e7d32', borderWidth: 1 }}] }},
options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'Marks' }}, beginAtZero: true }}, y: {{ title: {{ display: true, text: 'Registration No' }} }} }} }}
}});
}}

function renderCutoffChart() {{
const labels = Object.keys(cutoffs);
const vals = Object.values(cutoffs);
new Chart(document.getElementById('cutoffChart'), {{
type: 'bar',
data: {{ labels, datasets: [{{ label: 'Min Marks', data: vals, backgroundColor: 'rgba(198, 40, 40, 0.7)', borderColor: '#c62828', borderWidth: 1 }}] }},
options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'Category' }} }}, y: {{ title: {{ display: true, text: 'Marks' }}, beginAtZero: true }} }} }}
}});
}}

function renderCutoffTable() {{
document.getElementById('cutoffTableBody').innerHTML = Object.entries(cutoffs).map(([k,v]) => `<tr><td><strong>${{k}}</strong></td><td>${{v}}</td></tr>`).join('');
}}

function renderTop100() {{
document.getElementById('top100Body').innerHTML = allData.slice(0, 100).map(d => `<tr><td><span class="rank-badge">#${{d.rank}}</span></td><td><span class="day-badge">${{d.day||''}}</span></td><td>${{d.reg}}</td><td>${{d.roll}}</td><td><strong>${{d.marks.toFixed(2)}}</strong></td><td>${{d.pctl.toFixed(2)}}</td></tr>`).join('');
}}

function renderTable(page) {{
currentPage = page;
const start = (page - 1) * PAGE_SIZE;
const end = Math.min(start + PAGE_SIZE, allData.length);
const tbody = document.getElementById('allBody');
tbody.innerHTML = allData.slice(start, end).map(d => `<tr><td><span class="rank-badge">#${{d.rank}}</span></td><td><span class="day-badge">${{d.day||''}}</span></td><td>${{d.reg}}</td><td>${{d.roll}}</td><td><strong>${{d.marks.toFixed(2)}}</strong></td><td>${{d.pctl.toFixed(2)}}</td></tr>`).join('');
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
tbody.innerHTML = filtered.map(d => `<tr><td><span class="rank-badge">#${{d.rank}}</span></td><td><span class="day-badge">${{d.day||''}}</span></td><td>${{d.reg}}</td><td>${{d.roll}}</td><td><strong>${{d.marks.toFixed(2)}}</strong></td><td>${{d.pctl.toFixed(2)}}</td></tr>`).join('');
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
</script>
</body>
</html>"""
    html_path = out_dir / f"{filename_tag}_analysis.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

def gen_index(all_positions):
    # Merge positions from exam data and vacancy data
    all_pos_names = set(all_positions.keys()) | set(VACANCIES.keys())
    position_days = {}

    for pos_name in all_pos_names:
        records = all_positions.get(pos_name, [])
        days = sorted(set(r["Day"] for r in records))
        exams = sorted(set(r["Exam_Date"] for r in records))
        safe_name = safe(pos_name)
        position_days[pos_name] = {
            "total": len(records),
            "days": days,
            "exams": exams,
            "safe": safe_name
        }

    total_all = sum(pd["total"] for pd in position_days.values())
    all_totals = [pd["total"] for pd in position_days.values()]
    max_total = max(all_totals) if all_totals else 1

    # Sort: positions with exam data first (by count), then vacancy-only
    def sort_key(item):
        pos_name, info = item
        has_exam = info["total"] > 0
        return (0 if has_exam else 1, -info["total"])

    cards = ""
    for pos_name, info in sorted(position_days.items(), key=sort_key):
        safe_name = info["safe"]
        day_badges = "".join(f'<span class="day-pill">{d}</span>' for d in info["days"])
        vac = VACANCIES.get(pos_name, {})

        links = ""
        if info["total"] > 0 and len(info["days"]) > 1:
            links = f'<div class="links"><a href="{safe_name}_analysis.html">Combined ({info["total"]})</a>'
            for d in info["days"]:
                ds = d.lower().replace(" ", "_").replace("(", "").replace(")", "")
                dc = sum(1 for r in all_positions[pos_name] if r["Day"] == d)
                links += f'<a href="{safe_name}_{ds}_analysis.html">{d} ({dc})</a>'
            links += "</div>"
        if info["total"] > 0 and len(info["days"]) == 1:
            d = list(info["days"])[0]
            ds = d.lower().replace(" ", "_").replace("(", "").replace(")", "")
            links = f'<div class="links"><a href="{safe_name}_{ds}_analysis.html">{info["total"]} candidates</a></div>'
        if info["total"] == 0:
            links = '<div class="links" style="color:#999;font-size:12px;">No exam data yet</div>'

        total = info["total"]
        records = all_positions.get(pos_name, [])
        if total > 0:
            marks_list = [r["Marks"] for r in records]
            avg = sum(marks_list) / total
            highest = max(marks_list)
            median = sorted(marks_list)[total // 2]
            count_str = f"{total} candidates &middot; Avg: {avg:.2f} &middot; Highest: {highest:.2f} &middot; Median: {median:.2f}"
        else:
            count_str = "No exam data"
        width_pct = total / max_total * 100 if max_total else 0

        vac_line = ""
        if vac:
            vac_line = f'<div class="vac-line"><span class="vac-pill">{vac["level"]} / Group {vac["group"]}</span><span class="vac-pill">{vac["advt"]}</span><span class="vac-pill">Vacancies: {vac["total"]} (SC {vac["sc"]} ST {vac["st"]} OBC {vac["obc"]} EWS {vac["ews"]} UR {vac["ur"]})</span></div>'

        cards += f"""
        <div class="pos-card">
            <div class="pos-name">{pos_name}</div>
            <div class="pos-count">{count_str}</div>
            {vac_line}
            <div class="day-pills">{day_badges}</div>
            {links}
            <div class="pos-bar"><div class="pos-bar-fill" style="width:{width_pct}%"></div></div>
        </div>"""

    total_exams = sorted(set(e for pd in position_days.values() for e in pd["exams"]))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SGPGIMS Results - All Positions</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; color: #333; padding: 30px; }}
.container {{ max-width: 960px; margin: 0 auto; }}
h1 {{ text-align: center; color: #1a237e; font-size: 28px; }}
.subtitle {{ text-align: center; color: #666; margin-bottom: 6px; font-size: 14px; }}
.exam-list {{ text-align: center; margin-bottom: 24px; font-size: 13px; color: #555; }}
.exam-list strong {{ color: #1a237e; }}
.pos-card {{ background: white; border-radius: 12px; padding: 18px 24px; margin-bottom: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
.pos-name {{ font-size: 20px; font-weight: 700; color: #1a237e; }}
.pos-count {{ font-size: 13px; color: #666; margin-top: 4px; }}
.vac-line {{ margin-top: 6px; display: flex; gap: 6px; flex-wrap: wrap; }}
.vac-pill {{ background: #fff3e0; color: #e65100; font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 10px; }}
.day-pills {{ margin-top: 6px; display: flex; gap: 6px; flex-wrap: wrap; }}
.day-pill {{ background: #e8eaf6; color: #1a237e; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; }}
.links {{ margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; }}
.links a {{ padding: 5px 14px; background: #1a237e; color: white; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: 600; transition: background 0.15s; }}
.links a:hover {{ background: #283593; }}
.pos-bar {{ height: 4px; background: #e0e0e0; border-radius: 2px; margin-top: 10px; overflow: hidden; }}
.pos-bar-fill {{ height: 100%; background: linear-gradient(90deg, #1a237e, #5c6bc0); border-radius: 2px; }}
.total-badge {{ text-align: center; margin-bottom: 20px; font-size: 15px; color: #555; }}
.total-badge strong {{ color: #1a237e; }}
</style>
</head>
<body>
<div class="container">
<h1>SGPGIMS Exam Results</h1>
<p class="subtitle">Raw Score Analysis &mdash; Advt I/08/1-12/Rectt/2025-26</p>
<div class="exam-list">Exams: <strong>{', '.join(total_exams)}</strong></div>
<div class="total-badge">Total Candidates: <strong>{total_all}</strong> across {len(position_days)} positions</div>
{cards}
</div>
</body>
</html>"""
    html_path = out_dir / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nIndex HTML: index.html")

pdfs = [
    (r"C:\Users\Sarvagya\Desktop\sgpgi_data\Day1_Raw_Score_19_July_2026.pdf", "Day 1 (19 July 2026)", "19 July 2026"),
    (r"C:\Users\Sarvagya\Desktop\sgpgi_data\Day2_Raw_Score_20_June_2026.pdf", "Day 2 (20 June 2026)", "20 June 2026"),
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
        process_and_export(subj_name, safe_name, records, filename_tag, day_label)

    print(f"  Processed: {day_label} ({exam_date}) — {len(matches)} records across {len(day_records)} positions")

for subj_name, records in sorted(all_positions.items()):
    safe_name = re.sub(r'[^\w\s-]', '', subj_name).strip().replace(' ', '_').replace('.', '')
    process_and_export(subj_name, safe_name, records, safe_name, "Combined")
    print(f"  Combined: {subj_name} — {len(records)} records")

gen_index(all_positions)
print("\nAll done!")

