import os
import webbrowser
import json
import shutil
from .utils import write_json
from .learn.concept_graph import load_concept_graph, default_concept_graph_path
def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def load_ai_summary(run_dir):
    p = os.path.join(run_dir, "ai_summary.json")
    if not os.path.isfile(p):
        return {"state": "missing", "message": "未生成 AI Summary，请先运行 reposense ai summary <run_dir>", "data": {}}
    d = _read_json(p, None)
    if not isinstance(d, dict):
        return {"state": "invalid", "message": "AI Summary 产物损坏/不完整", "data": {}}
    return {"state": "ok", "message": "", "data": d}


def load_ai_risks(run_dir):
    p = os.path.join(run_dir, "ai_risks", "risks.json")
    if not os.path.isfile(p):
        return {"state": "missing", "message": "尚未生成 AI Risks，请先运行 reposense ai risks <run_dir>", "data": {}}
    d = _read_json(p, None)
    if not isinstance(d, dict):
        return {"state": "invalid", "message": "AI Risks 产物损坏/不完整", "data": {}}
    return {"state": "ok", "message": "", "data": d}


def list_ai_explains(run_dir):
    base = os.path.join(run_dir, "ai_explain")
    rows = []
    if not os.path.isdir(base):
        return rows
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name, "explain.json")
        d = _read_json(p, None)
        if isinstance(d, dict):
            rows.append(d)
    rows.sort(key=lambda x: (str(x.get("target_type") or ""), str(x.get("target_id") or ""), str(x.get("request_id") or "")))
    return rows


def load_ai_explain(run_dir, request_id):
    p = os.path.join(run_dir, "ai_explain", str(request_id), "explain.json")
    d = _read_json(p, None)
    return d if isinstance(d, dict) else {}


def load_snippet_pack(run_dir, request_id):
    p = os.path.join(run_dir, "ai_drilldown", str(request_id), "snippet_pack.json")
    d = _read_json(p, None)
    return d if isinstance(d, dict) else {}


def _known_concept_ids():
    try:
        g = load_concept_graph(default_concept_graph_path())
        out = set()
        for c in g.get("concepts", []):
            cid = str(c.get("concept_id") or c.get("concept") or "").strip().lower()
            if cid:
                out.add(cid)
        return out
    except Exception:
        return set()


def resolve_learn_links(risk_or_explain):
    ptype = str((risk_or_explain or {}).get("pattern_type") or "").strip().lower()
    mapping = {
        "transaction_missing": "data.transaction_boundary",
        "db_write_outside_tx": "data.transaction_boundary",
        "api_write_without_idempotency_guard": "reliability.idempotency",
        "queue_without_consumer": "async.queue",
    }
    cid = mapping.get(ptype) or ""
    if not cid:
        return {}
    if cid.lower() not in _known_concept_ids():
        return {}
    return {"concept_id": cid, "href": f"./learn/index.html?concept_id={cid}"}

def copy_assets(run_dir):
    # Assume webui/static is at ../webui/static relative to this file's package root
    # reposense/report.py -> reposense/ -> root -> webui/static
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(base_dir, "webui", "static")
    dst = os.path.join(run_dir, "assets")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    if os.path.exists(src):
        shutil.copytree(src, dst)

def _render_demo_tour_card(run_dir):
    links = [
        ('REPORT', 'report.html'),
        ('LEARN', 'learn/index.html'),
        ('SARIF', 'exports/report.sarif.json'),
        ('PACK', 'exports/context_pack.zip'),
        ('GATE', 'quality_gate.json'),
    ]
    items = "".join([f'<a class="badge" style="margin-right:8px" href="{h}" target="_blank">{l}</a>' for (l,h) in links])
    if os.path.isfile(os.path.join(run_dir, "baseline_diff.json")):
        items += '<a class="badge" style="margin-right:8px" href="baseline_diff.json" target="_blank">BASELINE DIFF</a>'
    else:
        items += '<span class="badge" style="margin-right:8px;opacity:0.65">BASELINE DIFF: N/A</span>'
    return f"""<!-- REPOSENSE_DEMO_TOUR_CARD -->
        <div class="card" id="demo-tour-card" style="border:1px dashed var(--color-border);background:var(--color-bg-muted)">
          <div style="font-weight:600;margin-bottom:8px">Demo 导览</div>
          <div style="font-size:13px;color:var(--color-text-muted)">这是 demo profile 的快速入口，仅在 demo 下展示，不影响生产报告结构</div>
          <div style="margin-top:8px">{items}</div>
        </div>"""
def build_report_html(run_dir):
    copy_assets(run_dir)
    report = {}
    graph = {}
    demo_mode = False
    try:
        with open(os.path.join(run_dir, "report.json"), "r", encoding="utf-8") as rf:
            report = json.load(rf)
    except:
        report = {"findings": []}
    try:
        with open(os.path.join(run_dir, "event_graph.json"), "r", encoding="utf-8") as gf:
            graph = json.load(gf)
    except:
        graph = {"schema_version":"1.0","nodes": [], "edges": []}
    try:
        with open(os.path.join(run_dir, "meta", "config.json"), "r", encoding="utf-8") as f:
            mcfg = json.load(f)
        if (mcfg.get("profile") or "").strip().lower() == "demo":
            demo_mode = True
    except Exception:
        demo_mode = False
    gate = _read_json(os.path.join(run_dir, "quality_gate.json"), {"status":"N/A","violations":[]})
    ai_summary_obj = load_ai_summary(run_dir)
    ai_risks_obj = load_ai_risks(run_dir)
    ai_explains = list_ai_explains(run_dir)
    ai_snippets = {}
    for ex in ai_explains:
        sp = ex.get("snippet_pack_ref") if isinstance(ex.get("snippet_pack_ref"), dict) else {}
        rid = str(sp.get("request_id") or "")
        if rid:
            ai_snippets[rid] = load_snippet_pack(run_dir, rid)
    # enrich risk items with learn links
    if ai_risks_obj.get("state") == "ok":
        risks_data = ai_risks_obj.get("data") or {}
        for item in (risks_data.get("risk_items") or []):
            item["learn_link"] = resolve_learn_links(item)
        ai_risks_obj["data"] = risks_data
    gst = str(gate.get("status") or "N/A").upper()
    gcls = "primary"
    if gst == "FAIL":
        gcls = "danger"
    elif gst == "WARN":
        gcls = "warning"
    
    demo_card_html = _render_demo_tour_card(run_dir) if demo_mode else ""
    html = """<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>RepoSense Report</title>
  <link rel='stylesheet' href='assets/reposense.css'>
</head>
<body>
  <div class="topbar">
    <div style="display:flex;align-items:center">
      <div class="logo">RepoSense</div>
      <div id="top-info" style="font-size:14px;color:#666">
        <span class="badge primary">Findings: """ + str(len(report.get('findings', []))) + """</span>
        <span class="badge primary">Events: """ + str(len(graph.get('nodes', []))) + """</span>
        <span class="badge """ + gcls + """">Gate: """ + gst + """</span>
      </div>
    </div>
    <div style="font-size:12px;color:#999">Generated by RepoSense</div>
  </div>
  """ + demo_card_html + """
  <div class="app-container">
    <div class="sidebar">
      <div class="sidebar-section">Analysis</div>
      <div class="sidebar-item active" id="nav-overview" onclick="switchView('overview')">Overview</div>
      <div class="sidebar-item" id="nav-events" onclick="switchView('events')">Events</div>
      <div class="sidebar-item" id="nav-api" onclick="switchView('api')">API Surface</div>
      <div class="sidebar-item" id="nav-findings" onclick="switchView('findings')">Findings</div>
    </div>
    <div class="main-content" id="main-content"></div>
    <div class="details-pane hidden" id="details-pane">
      <div class="details-header" id="details-header"></div>
      <div class="details-tabs" id="details-tabs"></div>
      <div class="details-body" id="details-body"></div>
    </div>
  </div>
  <script type="application/json" id="report-data">""" + json.dumps(report) + """</script>
  <script type="application/json" id="graph-data">""" + json.dumps(graph) + """</script>
  <script type="application/json" id="api-data">""" + json.dumps(_read_json(os.path.join(run_dir, "api_surface.json"), {"endpoints":[],"stats":{},"mismatches":{}})) + """</script>
  <script type="application/json" id="entrypoints-data">""" + json.dumps(_read_json(os.path.join(run_dir, "entrypoints.json"), {"entrypoints":[],"stats":{}})) + """</script>
  <script type="application/json" id="gate-data">""" + json.dumps(_read_json(os.path.join(run_dir, "quality_gate.json"), {"status":"N/A","violations":[]})) + """</script>
  <script type="application/json" id="baseline-diff-data">""" + json.dumps(_read_json(os.path.join(run_dir, "baseline_diff.json"), {"schema_version":0,"stats":{},"added":[],"removed":[],"severity_changed":[]})) + """</script>
  <script type="application/json" id="manifest-data">""" + json.dumps(_read_json(os.path.join(run_dir, "run_manifest.json"), {"schema_version":0,"meta":{},"artifacts":[]})) + """</script>
  <script type="application/json" id="ai-summary-data">""" + json.dumps(ai_summary_obj) + """</script>
  <script type="application/json" id="ai-risks-data">""" + json.dumps(ai_risks_obj) + """</script>
  <script type="application/json" id="ai-explains-data">""" + json.dumps(ai_explains) + """</script>
  <script type="application/json" id="ai-snippets-data">""" + json.dumps(ai_snippets) + """</script>
  <script>
    function _readJsonEl(id) {
      try { return JSON.parse(document.getElementById(id).textContent); } catch(e) { return {}; }
    }
    const report = _readJsonEl('report-data');
    const graph = _readJsonEl('graph-data');
    const apiSurf = _readJsonEl('api-data');
    const entrypoints = _readJsonEl('entrypoints-data');
    const gate = _readJsonEl('gate-data');
    const baselineDiff = _readJsonEl('baseline-diff-data');
    const runManifest = _readJsonEl('manifest-data');
    const aiSummaryObj = _readJsonEl('ai-summary-data');
    const aiRisksObj = _readJsonEl('ai-risks-data');
    const aiExplains = _readJsonEl('ai-explains-data');
    const aiSnippets = _readJsonEl('ai-snippets-data');
    let learnBase = './learn';
    let currentView = 'overview';

    // Init logic to find learn base
    (async function() {
      try {
        const metaCfg = JSON.parse(await (await fetch('meta/config.json')).text());
        if (metaCfg && metaCfg.learn_base) learnBase = metaCfg.learn_base;
      } catch(e) {}
      switchView('overview');
    })();

    function switchView(view) {
      currentView = view;
      document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
      document.getElementById('nav-' + view).classList.add('active');
      
      const main = document.getElementById('main-content');
      main.innerHTML = '';
      
      // Hide details pane when switching main views
      document.getElementById('details-pane').classList.add('hidden');

      if (view === 'overview') renderOverview(main);
      else if (view === 'events') renderEvents(main);
      else if (view === 'api') renderApi(main);
      else if (view === 'findings') renderFindings(main);
    }

    function renderOverview(container) {
      const s = report.run_summary || {};
      const topSkip = (s.skipped_files_by_reason || []).map(([k,v]) => `<span class="badge">${k}: ${v}</span>`).join(' ');
      const truncBadges = [];
      if (s.truncation && s.truncation.budget_cut) truncBadges.push('<span class="badge danger">budget_cut</span>');
      if (s.truncation && s.truncation.findings_truncated) truncBadges.push('<span class="badge danger">findings_truncated</span>');
      if (s.truncation && s.truncation.events_truncated) truncBadges.push('<span class="badge danger">events_truncated</span>');
      container.innerHTML = `
        <h2>Overview</h2>
        <div class="card" style="margin-bottom:16px">
          <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center">
            <div><span class="badge">profile</span> ${s.profile || ''}</div>
            <div><span class="badge">ruleset</span> ${s.ruleset || ''}</div>
            <div><span class="badge primary">findings</span> ${s.findings_count ?? report.findings.length}</div>
            <div><span class="badge primary">events</span> ${s.events_count ?? (graph.nodes || []).length}</div>
            <div><span class="badge">graph nodes</span> ${s.graph_nodes ?? (graph.nodes||[]).length}</div>
            <div><span class="badge">graph edges</span> ${s.graph_edges ?? (graph.edges||[]).length}</div>
            <div><span class="badge">scanned files</span> ${s.scanned_files ?? 0}</div>
            ${truncBadges.join(' ')}
            <div><span class="badge ${gate.status==='fail'?'danger':(gate.status==='warn'?'warning':'primary')}">Gate: ${String(gate.status || 'N/A').toUpperCase()}</span></div>
          </div>
        </div>
        <div class="card">
          <div style="font-weight:600;margin-bottom:8px">Gate Violations (Top3)</div>
          ${(gate.violations||[]).slice(0,3).map(v=>`<div style="margin-bottom:6px"><span class="badge">${v.level}</span> ${v.metric}: ${v.message}</div>`).join('') || '<span class="badge">none</span>'}
          <div style="margin-top:8px;font-size:12px"><a href="quality_gate.json" target="_blank">查看 quality_gate.json</a></div>
        </div>
        ${renderBaselineCard(gate, baselineDiff)}
        ${renderRunInfo(gate, runManifest)}
        ${renderEdgeTypes()}
        ${renderAiSummaryCard()}
        ${renderAiRisksPanel()}
        <div class="card">
          <div style="font-weight:600;margin-bottom:8px">Top Skip Reasons</div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">${topSkip || '<span class="badge">none</span>'}</div>
        </div>
        ${renderEmptyExplain(s)}
        ${renderStartHere(entrypoints)}
      `;
    }
    function pct(n, d) { if (!d) return 0; return Math.round(n * 100 / d); }
    function renderEmptyExplain(s) {
      const f0 = (s.findings_count ?? 0) === 0;
      const e0 = (s.events_count ?? 0) === 0;
      if (!(f0 || e0)) return '';
      const total = (s.scanned_files ?? 0) + ((s.skipped_files_by_reason || []).reduce((a,[,v])=>a+v,0));
      const skippedTotal = (s.skipped_files_by_reason || []).reduce((a,[,v])=>a+v,0);
      const skipPct = pct(skippedTotal, total);
      const hasBudget = !!(s.truncation && (s.truncation.budget_cut || s.truncation.findings_truncated || s.truncation.events_truncated));
      let reason = '';
      if (hasBudget) {
        reason = '预算截断（建议切换 prod_deep 或增大预算）';
      } else if (skipPct > 70) {
        const parts = (s.skipped_files_by_reason || []).slice(0,3).map(([k,v])=>`${k} ${pct(v,total)}%`).join('、');
        reason = `跳过过多：${skipPct}%（${parts}）`;
      } else if ((s.warnings_top || []).some(w => (w && w.type) === 'ast_parse_error')) {
        const n = (s.warnings_top || []).filter(w => (w && w.type) === 'ast_parse_error').length;
        reason = `解析失败（ast_parse_error ${n}）`;
      } else {
        reason = '未触发规则或风险较低（可切换 ruleset/basic 或增加规则覆盖）';
      }
      return `
        <div class="card" style="margin-top:16px">
          <div style="font-weight:600;margin-bottom:8px">空状态解释</div>
          <div style="color:var(--color-text-muted);font-size:14px">${reason}</div>
        </div>
      `;
    }

    function renderFindings(container) {
      container.innerHTML = '<h2>Findings</h2>';
      report.findings.forEach(f => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-weight:600;font-size:16px">${f.concept}</div>
            <div class="badge primary">${f.confidence.toFixed(2)}</div>
          </div>
          <div style="font-size:13px;color:var(--color-text-muted)">
            <span class="badge">${f.parse_level}</span>
            ${f.path}:${f.start_line}-${f.end_line}
          </div>
        `;
        card.onclick = () => showFindingDetails(f);
        container.appendChild(card);
      });
    }

    function renderEvents(container) {
      container.innerHTML = '<h2>Events</h2>';
      (graph.nodes || []).forEach(n => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-weight:600;font-size:16px">${n.type}</div>
            <div class="badge primary">${n.confidence.toFixed(2)}</div>
          </div>
          <div style="font-size:13px;color:var(--color-text-muted)">
            ${n.key}
          </div>
        `;
        card.onclick = () => showEventDetails(n, graph.edges || [], graph.nodes || []);
        container.appendChild(card);
      });
    }
    function renderApi(container) {
      const stats = apiSurf.stats || {};
      const mism = apiSurf.mismatches || {};
      container.innerHTML = `
        <h2>API Surface</h2>
        <div class="card" style="margin-bottom:16px">
          <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center">
            <div><span class="badge">total</span> ${(apiSurf.endpoints||[]).length}</div>
            <div><span class="badge">unique</span> ${stats.unique_endpoints||0}</div>
            <div><span class="badge">by source</span> ${Object.entries(stats.by_source_kind||{}).map(([k,v])=>`${k}:${v}`).join(' ') || 'n/a'}</div>
            <div><span class="badge">duplicates</span> ${(stats.duplicate_routes||[]).length}</div>
          </div>
        </div>
        <div class="card">
          <div style="font-weight:600;margin-bottom:8px">Mismatches</div>
          <div style="font-size:13px;color:var(--color-text-muted)">
            missing_in_spec: ${(mism.missing_in_spec||[]).length} · missing_in_code: ${(mism.missing_in_code||[]).length} · method_mismatch: ${(mism.method_mismatch||[]).length}
          </div>
          <div style="margin-top:8px">
            ${(mism.missing_in_spec||[]).slice(0,10).map(x=>`<div class="badge danger">${x}</div>`).join('') || '<span class="badge">none</span>'}
          </div>
        </div>
      `;
    }
    function renderRunInfo(gate, manifest) {
      const gb = gate.generated_by || {};
      const rid = gb.ruleset_id || '';
      const rfp = gb.ruleset_fingerprint || '';
      const rv = gb.reposense_version || '';
      const sv = gb.schema_version || '';
      return `
        <div class="card" style="margin-top:16px">
          <div style="font-weight:600;margin-bottom:8px">Run Info / Versions</div>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <div><span class="badge">reposense</span> ${rv}</div>
            <div><span class="badge">ruleset</span> ${rid}</div>
            <div><span class="badge">fingerprint</span> ${rfp}</div>
            <div><span class="badge">schema</span> ${sv}</div>
            <div><a href="run_manifest.json" target="_blank">run_manifest.json</a></div>
          </div>
        </div>
      `;
    }
    function renderEdgeTypes() {
      try {
        const g = JSON.parse(document.getElementById('graph-data').textContent);
        const cnt = {};
        (g.edges||[]).forEach(e => { const t=e.type||'unknown'; cnt[t]=(cnt[t]||0)+1; });
        const rows = Object.keys(cnt).sort().map(t => `<div style="font-size:12px;color:var(--color-text-muted)"><span class="badge">${t}</span> ${cnt[t]}</div>`).join('');
        return `
          <div class="card" style="margin-top:16px">
            <div style="font-weight:600;margin-bottom:8px">Graph Edge Types</div>
            ${rows || '<span class="badge">none</span>'}
          </div>
        `;
      } catch (e) {
        return '';
      }
    }
    function renderBaselineCard(gate, diff) {
      const used = !!gate.baseline_used;
      if (!used) {
        return `
          <div class="card" style="margin-top:16px">
            <div style="font-weight:600;margin-bottom:8px">Baseline & Diff</div>
            <div style="color:var(--color-text-muted)">未启用 Baseline（首次运行请 baseline-out；PR 检测请 baseline-in）</div>
          </div>
        `;
      }
      const st = gate.regressions || {};
      const top = gate.regression_samples_top || [];
      const links = gate.baseline_paths || {};
      const compat = gate.baseline_compatible !== false;
      const items = top.map(x => `
        <div style="font-size:12px;color:var(--color-text-muted);margin-bottom:6px">
          <span class="badge">${(x.severity||'').toUpperCase()}</span> ${x.ruleId||''} · ${x.concept||''} · ${x.path||''}:${x.startLine||0}
        </div>
      `).join('');
      return `
        <div class="card" style="margin-top:16px">
          <div style="font-weight:600;margin-bottom:8px">Baseline & Diff</div>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <div><span class="badge danger">+E</span> ${st.added_error||0}</div>
            <div><span class="badge warning">↑S</span> ${st.severity_upgrades||0}</div>
            <div><span class="badge">+W</span> ${st.added_warning||0}</div>
            <div><span class="badge primary">total</span> ${st.total||0}</div>
            <div><span class="badge ${compat?'primary':'warning'}">compat</span> ${compat?'compatible':'incompatible'}</div>
          </div>
          <div style="margin-top:8px">${items || '<span class="badge">none</span>'}</div>
          ${compat ? '' : '<div style="margin-top:8px;color:var(--color-text-muted);font-size:12px">Baseline incompatible；请在 main 刷新 baseline</div>'}
          <div style="margin-top:8px;font-size:12px">
            ${(links.diff_json?`<a href="baseline_diff.json" target="_blank">baseline_diff.json</a>`:'')}
            ${(links.diff_md?` · <a href="baseline_diff.md" target="_blank">baseline_diff.md</a>`:'')}
            ${(links.baseline_in?` · <a href="baseline_in.json" target="_blank">baseline_in.json</a>`:'')}
          </div>
        </div>
      `;
    }
    function renderStartHere(entry) {
      const eps = (entry.entrypoints || []).slice().sort((a,b) => (b.confidence||0) - (a.confidence||0)).slice(0,5);
      if (eps.length === 0) {
        return `
          <div class="card" style="margin-top:16px">
            <div style="font-weight:600;margin-bottom:8px">Start Here</div>
            <div style="color:var(--color-text-muted)">未检测到标准入口文件/脚本；可查看 package.json/README/compose/openapi</div>
          </div>
        `;
      }
      const items = eps.map(e => `
        <div style="margin-bottom:8px">
          <div style="font-weight:600">${e.title}</div>
          <div style="font-family:var(--font-mono);font-size:12px;color:var(--color-text-muted)">${e.command || ''}</div>
          <div style="font-size:12px;color:var(--color-text-muted)">${(e.source||{}).path || ''}</div>
        </div>
      `).join('');
      return `
        <div class="card" style="margin-top:16px">
          <div style="font-weight:600;margin-bottom:8px">Start Here</div>
          ${items}
        </div>
      `;
    }
    function _escapeHtml(s) {
      return String(s || '').replace(/[&<>"']/g, function(m){ return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m]; });
    }
    function renderAiSummaryCard() {
      const o = aiSummaryObj || {};
      if (o.state !== 'ok') {
        return `
          <div class="card" id="ai-summary" style="margin-top:16px">
            <div style="font-weight:600;margin-bottom:8px">AI Summary</div>
            <div style="color:var(--color-text-muted)">${_escapeHtml(o.message || '未生成 AI Summary')}</div>
          </div>
        `;
      }
      const d = o.data || {};
      const ov = d.project_overview || {};
      const ss = d.surface_summary || {};
      const rs = d.risk_summary || {};
      const acts = (d.priority_actions || []).slice(0,5);
      return `
        <div class="card" id="ai-summary" style="margin-top:16px">
          <div style="font-weight:600;margin-bottom:8px">AI Summary</div>
          <div style="display:flex;flex-wrap:wrap;gap:10px">
            <span class="badge">languages: ${(ov.languages||[]).join(', ') || 'none'}</span>
            <span class="badge">frameworks: ${(ov.frameworks||[]).join(', ') || 'none'}</span>
            <span class="badge">findings/events/edges: ${ov.findings||0}/${ov.events||0}/${ov.graph_edges||0}</span>
            <span class="badge">API/Queue(DB write): ${ss.api_count||0}/${ss.queue_dispatch_count||0}(${ss.db_write_count||0})</span>
            <span class="badge">patterns: ${rs.total_patterns||0}</span>
          </div>
          <div style="margin-top:8px">
            ${(acts.length ? acts.map(a=>`<div style="font-size:13px;color:var(--color-text-muted)">- ${_escapeHtml(a.title||'')}: ${_escapeHtml(a.reason||'')}</div>`).join('') : '<div style="color:var(--color-text-muted)">no priority actions</div>')}
          </div>
        </div>
      `;
    }
    function _riskGroups(items) {
      const immediate = [], review = [], watch = [];
      (items || []).forEach(x => {
        const sev = String(x.severity || 'medium');
        const st = String(x.status || 'suspected');
        if (sev === 'high' || (sev === 'medium' && st === 'confirmed')) immediate.push(x);
        else if (sev === 'medium') review.push(x);
        else watch.push(x);
      });
      return {immediate, review, watch};
    }
    function _findExplainByPattern(patternId) {
      return (aiExplains || []).find(x => String(x.target_type||'') === 'pattern' && String(x.target_id||'') === String(patternId||''));
    }
    function _renderRiskCard(x) {
      const patternId = (x.related_patterns || [])[0] || '';
      const ex = _findExplainByPattern(patternId);
      const hasExplain = !!ex;
      const hasSnippets = !!(x.snippet_refs && x.snippet_refs.length);
      const ll = x.learn_link || {};
      const hasLearn = !!ll.href;
      return `
        <div class="card" style="margin-top:10px">
          <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
            <div style="font-weight:600">${_escapeHtml(x.title || '')}</div>
            <div>
              <span class="badge">${_escapeHtml(x.severity || '')}</span>
              <span class="badge">${_escapeHtml(x.status || '')}</span>
            </div>
          </div>
          <div style="font-size:13px;color:var(--color-text-muted);margin-top:6px">${_escapeHtml(x.why_it_matters || '')}</div>
          <div style="margin-top:6px;font-size:12px;color:var(--color-text-muted)">
            pattern=${_escapeHtml(x.pattern_type || '')} evidence=${(x.evidence_refs||[]).length} snippets=${(x.snippet_refs||[]).length}
          </div>
          <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">
            <button onclick="openExplainByPattern('${_escapeHtml(patternId)}')">Explain</button>
            ${hasSnippets ? `<button onclick="openSnippetsForRisk('${_escapeHtml(x.risk_id||'')}')">View snippets</button>` : ''}
            ${hasLearn ? `<a class="badge primary" href="${_escapeHtml(ll.href)}" target="_blank">Learn this concept</a>` : ''}
            <button onclick="openEvidenceFromRisk('${_escapeHtml(x.risk_id||'')}')">Open evidence</button>
          </div>
          ${hasExplain ? '' : '<div style="margin-top:6px;color:var(--color-text-muted);font-size:12px">该风险尚未生成 Explain，请先运行 reposense ai explain ...</div>'}
        </div>
      `;
    }
    function renderAiRisksPanel() {
      const o = aiRisksObj || {};
      if (o.state !== 'ok') {
        return `
          <div class="card" id="ai-risks" style="margin-top:16px">
            <div style="font-weight:600;margin-bottom:8px">AI Risks</div>
            <div style="color:var(--color-text-muted)">${_escapeHtml(o.message || '尚未生成 AI Risks')}</div>
          </div>
        `;
      }
      const data = o.data || {};
      const g = _riskGroups(data.risk_items || []);
      const renderGroup = (title, rows) => `
        <div style="margin-top:12px">
          <div style="font-weight:600">${title}</div>
          ${rows.length ? rows.map(_renderRiskCard).join('') : '<div style="color:var(--color-text-muted);font-size:13px">none</div>'}
        </div>
      `;
      return `
        <div class="card" id="ai-risks" style="margin-top:16px">
          <div style="font-weight:600;margin-bottom:8px">Risks</div>
          ${renderGroup('Immediate attention', g.immediate)}
          ${renderGroup('Needs review', g.review)}
          ${renderGroup('Contextual watchlist', g.watch)}
        </div>
      `;
    }
    function _renderExplainDetail(ex) {
      if (!ex) {
        return '<div style="color:var(--color-text-muted)">尚未生成 explain，请先运行 reposense ai explain ...</div>';
      }
      const snippets = ex.snippet_pack_ref || {};
      const sReq = String(snippets.request_id || '');
      const learnBtn = (() => {
        const rid = String(ex.target_id || '');
        const risk = ((aiRisksObj.data || {}).risk_items || []).find(x => String((x.related_patterns||[])[0] || '') === rid);
        const ll = (risk && risk.learn_link) || {};
        return ll.href ? `<a class="badge primary" href="${_escapeHtml(ll.href)}" target="_blank">Learn this concept</a>` : '';
      })();
      return `
        <div id="ai-explain" style="margin-top:8px">
          <div><span class="badge">target</span> ${_escapeHtml(ex.target_type)}:${_escapeHtml(ex.target_id)}</div>
          <div><span class="badge">mode</span> ${_escapeHtml(ex.mode)}</div>
          <div style="margin-top:8px"><b>已证实</b>: ${(ex.confirmed||[]).length}</div>
          <div><b>合理推测</b>: ${(ex.inferred||[]).length}</div>
          <div><b>未知</b>: ${(ex.unknown||[]).length}</div>
          <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">
            ${sReq ? `<button onclick="openSnippetByRequest('${_escapeHtml(sReq)}')">View snippets</button>` : '<span style="color:var(--color-text-muted)">本次 Explain 为 facts-only，未触发源码下钻</span>'}
            <button onclick="openEvidenceFromExplain('${_escapeHtml(ex.request_id || '')}')">Open evidence</button>
            ${learnBtn}
          </div>
          <div style="margin-top:8px;color:var(--color-text-muted);font-size:12px">
            本次解释默认基于结构化 facts；如触发 drilldown，仅基于 evidence refs 约束片段；未进行整仓源码阅读。
          </div>
        </div>
      `;
    }
    function openExplainByPattern(patternId) {
      const ex = _findExplainByPattern(patternId);
      const pane = document.getElementById('details-pane');
      pane.classList.remove('hidden');
      document.getElementById('details-header').innerHTML = `<div class="details-title">AI Explain</div><div class="badge primary">${_escapeHtml(patternId)}</div>`;
      document.getElementById('details-tabs').innerHTML = `<div class="tab active">Explain</div>`;
      document.getElementById('details-body').innerHTML = _renderExplainDetail(ex);
    }
    function openSnippetByRequest(reqId) {
      const p = (aiSnippets || {})[reqId];
      if (!p || !p.selected_snippets || !p.selected_snippets.length) {
        const pane = document.getElementById('details-pane');
        pane.classList.remove('hidden');
        document.getElementById('details-header').innerHTML = `<div class="details-title">Snippets</div>`;
        document.getElementById('details-tabs').innerHTML = `<div class="tab active">Snippet</div>`;
        document.getElementById('details-body').innerHTML = '<div style="color:var(--color-text-muted)">无 snippet 产物</div>';
        return;
      }
      const rows = (p.selected_snippets || []).map(s => `
        <div class="evidence-card">
          <div class="evidence-header"><span class="evidence-path">${_escapeHtml(s.file)}:${s.line_start}-${s.line_end}</span></div>
          <div style="font-size:12px;color:var(--color-text-muted);margin:6px 0">why_selected: ${_escapeHtml(s.why_selected || '')}</div>
          <pre class="snippet-block">${_escapeHtml(s.snippet || '')}</pre>
        </div>
      `).join('');
      const pane = document.getElementById('details-pane');
      pane.classList.remove('hidden');
      document.getElementById('details-header').innerHTML = `<div class="details-title">Snippet Pack ${_escapeHtml(reqId)}</div>`;
      document.getElementById('details-tabs').innerHTML = `<div class="tab active">Snippet</div>`;
      document.getElementById('details-body').innerHTML = rows;
    }
    function openSnippetsForRisk(riskId) {
      const risk = ((aiRisksObj.data || {}).risk_items || []).find(x => String(x.risk_id || '') === String(riskId || ''));
      if (!risk) return;
      const pat = (risk.related_patterns || [])[0] || '';
      const ex = _findExplainByPattern(pat);
      const req = ex && ex.snippet_pack_ref ? ex.snippet_pack_ref.request_id : '';
      if (!req) {
        openSnippetByRequest('');
        return;
      }
      openSnippetByRequest(String(req));
    }
    function openEvidenceFromRisk(riskId) {
      const risk = ((aiRisksObj.data || {}).risk_items || []).find(x => String(x.risk_id || '') === String(riskId || ''));
      if (!risk) return;
      const pane = document.getElementById('details-pane');
      pane.classList.remove('hidden');
      document.getElementById('details-header').innerHTML = `<div class="details-title">Risk Evidence</div>`;
      document.getElementById('details-tabs').innerHTML = `<div class="tab active">Evidence</div>`;
      const rows = (risk.evidence_refs || []).map(e => `<div style="font-size:12px;color:var(--color-text-muted)">${_escapeHtml(e.file || '')}:${e.start_line || 0}-${e.end_line || 0}</div>`).join('') || '<div style="color:var(--color-text-muted)">none</div>';
      document.getElementById('details-body').innerHTML = rows;
    }
    function openEvidenceFromExplain(reqId) {
      const ex = (aiExplains || []).find(x => String(x.request_id || '') === String(reqId || ''));
      if (!ex) return;
      const rows = (ex.evidence_index || []).map(e => `<div style="font-size:12px;color:var(--color-text-muted)">${_escapeHtml(e.file || '')}:${e.start_line || 0}-${e.end_line || 0}</div>`).join('') || '<div style="color:var(--color-text-muted)">none</div>';
      const pane = document.getElementById('details-pane');
      pane.classList.remove('hidden');
      document.getElementById('details-header').innerHTML = `<div class="details-title">Explain Evidence</div>`;
      document.getElementById('details-tabs').innerHTML = `<div class="tab active">Evidence</div>`;
      document.getElementById('details-body').innerHTML = rows;
    }

    function showFindingDetails(f) {
      const pane = document.getElementById('details-pane');
      pane.classList.remove('hidden');
      
      // Header
      const header = document.getElementById('details-header');
      header.innerHTML = `
        <div class="details-title">Finding ${f.fid}</div>
        <div class="badge primary">${f.concept}</div>
      `;

      // Tabs
      const tabs = document.getElementById('details-tabs');
      tabs.innerHTML = `
        <div class="tab active" onclick="switchTab('summary')">Summary</div>
        <div class="tab" onclick="switchTab('evidence')">Evidence</div>
      `;

      // Body
      const body = document.getElementById('details-body');
      renderFindingSummary(body, f);
      
      // Store current data for tab switching
      pane.dataset.currentType = 'finding';
      pane.dataset.currentData = JSON.stringify(f);
    }

    function showEventDetails(n, edges, nodes) {
      const pane = document.getElementById('details-pane');
      pane.classList.remove('hidden');

      // Header
      const header = document.getElementById('details-header');
      header.innerHTML = `
        <div class="details-title">Event ${n.event_id}</div>
        <div class="badge primary">${n.type}</div>
      `;

      // Tabs
      const tabs = document.getElementById('details-tabs');
      tabs.innerHTML = `
        <div class="tab active" onclick="switchTab('summary')">Summary</div>
        <div class="tab" onclick="switchTab('evidence')">Evidence</div>
      `;

      // Body
      const body = document.getElementById('details-body');
      renderEventSummary(body, n, edges, nodes);
      
      pane.dataset.currentType = 'event';
      pane.dataset.currentData = JSON.stringify({n, edges, nodes}); // Simplified storage
    }

    function switchTab(tabName) {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      event.target.classList.add('active');
      
      const pane = document.getElementById('details-pane');
      const body = document.getElementById('details-body');
      const type = pane.dataset.currentType;
      
      if (type === 'finding') {
        const f = JSON.parse(pane.dataset.currentData);
        if (tabName === 'summary') renderFindingSummary(body, f);
        else renderFindingEvidence(body, f);
      } else if (type === 'event') {
        const data = JSON.parse(pane.dataset.currentData);
        if (tabName === 'summary') renderEventSummary(body, data.n, data.edges, data.nodes);
        else renderEventEvidence(body, data.n);
      }
    }

    function renderFindingSummary(container, f) {
      const slug = (f.concept||'').toLowerCase().replace(/[^a-z0-9_-]/g,'_');
      const learnLink = `<a href="${learnBase}/concepts/${slug}.html" target="_blank" style="color:var(--color-primary)">Learn more about ${f.concept}</a>`;
      
      container.innerHTML = `
        <div style="margin-bottom:16px">${learnLink}</div>
        <div class="meta-grid">
          <div class="meta-label">ID</div><div>${f.fid}</div>
          <div class="meta-label">Confidence</div><div>${f.confidence}</div>
          <div class="meta-label">Level</div><div>${f.parse_level}</div>
          <div class="meta-label">Location</div><div style="font-family:var(--font-mono)">${f.path}:${f.start_line}-${f.end_line}</div>
        </div>
        <div style="margin-top:16px;font-weight:600">Snippet</div>
        <pre class="snippet-block" style="padding:8px">${f.snippet}</pre>
      `;
    }

    function renderFindingEvidence(container, f) {
      // Finding itself is the evidence
      container.innerHTML = createEvidenceCard(f);
    }

    function renderEventSummary(container, n, edges, nodes) {
      let incoming = edges.filter(e => e.type === 'declares_dependency' && e.to === n.event_id)
        .map(e => nodes.find(x => x.event_id === e.from))
        .filter(x => x).map(x => `<div>${x.type} ${x.key}</div>`).join('');
      
      let outgoing = edges.filter(e => e.type === 'declares_dependency' && e.from === n.event_id)
        .map(e => nodes.find(x => x.event_id === e.to))
        .filter(x => x).map(x => `<div>${x.type} ${x.key}</div>`).join('');

      container.innerHTML = `
        <div class="meta-grid">
          <div class="meta-label">Key</div><div>${n.key}</div>
          <div class="meta-label">Source</div><div>${(n.meta && n.meta.source) || ''}</div>
        </div>
        ${incoming ? '<div style="margin-top:16px;font-weight:600">Incoming Dependencies</div>' + incoming : ''}
        ${outgoing ? '<div style="margin-top:16px;font-weight:600">Outgoing Dependencies</div>' + outgoing : ''}
      `;
    }

    function renderEventEvidence(container, n) {
      container.innerHTML = '<div style="color:var(--color-text-muted)">Loading evidence...</div>';
      Promise.all((n.evidence || []).map(e => fetch('evidence/E' + e.substring(1) + '.json').then(r => r.json()).catch(() => null)))
        .then(items => {
          container.innerHTML = items.filter(Boolean).map(createEvidenceCard).join('');
        });
    }

    function createEvidenceCard(data) {
      // data: {path, start_line, end_line, snippet, parse_level}
      // Create HTML string for evidence card
      const lines = data.snippet.split('\\n');
      const start = data.start_line;
      
      let codeHtml = '';
      lines.forEach((line, i) => {
        codeHtml += `<div class="snippet-line">
          <div class="snippet-ln">${start + i}</div>
          <div class="snippet-code">${line}</div>
        </div>`;
      });

      return `
        <div class="evidence-card">
          <div class="evidence-header">
            <span class="evidence-path">${data.path}</span>
            <span class="badge">${data.parse_level}</span>
          </div>
          <div class="snippet-block" style="border:none;margin:0;border-radius:0">
            ${codeHtml}
          </div>
        </div>
      `;
    }
  </script>
</body>
</html>"""
    with open(os.path.join(run_dir, "report.html"), "w", encoding="utf-8") as f:
        f.write(html)
def show_report(run_dir, do_open):
    path = os.path.abspath(os.path.join(run_dir, "report.html"))
    print(path)
    if do_open:
        webbrowser.open(path)
