(function () {
  'use strict';

  const state = {view: 'home', runs: [], currentRun: null, pollTimer: null};
  const view = document.getElementById('studio-view');
  const title = document.getElementById('page-title');
  const kicker = document.getElementById('page-kicker');
  const topStatus = document.getElementById('topbar-status');
  const topActions = document.getElementById('topbar-actions');

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  function pill(value, label) {
    const status = String(value || 'unknown').toLowerCase();
    return `<span class="status-pill ${escapeHtml(status)}">${escapeHtml(label || status.replaceAll('_', ' '))}</span>`;
  }

  async function fetchJson(path, options) {
    const response = await fetch(new URL(path, window.location.origin).toString(), options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);
    return data;
  }

  function setHeader(pageTitle, pageKicker) {
    title.textContent = pageTitle;
    kicker.textContent = pageKicker || 'Repository Review Workbench';
    topStatus.innerHTML = '';
    topActions.innerHTML = '';
  }

  function setActiveNav(name) {
    document.querySelectorAll('[data-view]').forEach(button => button.classList.toggle('active', button.dataset.view === name));
  }

  function runCard(run) {
    const summary = run.summary || {};
    const profile = run.profile || {};
    const timestamp = new Date((run.updated_at || run.start_time || 0) * 1000).toLocaleString();
    const human = summary.human_review_required_status === 'available' ? summary.human_review_required_count : 'not generated';
    return `
      <article class="run-summary-card" data-open-run="${escapeHtml(run.run_id)}" tabindex="0">
        <div class="run-card-top"><span class="run-profile">${escapeHtml(profile.display_name || profile.profile_id || 'Historical run')}</span>${pill(run.status)}</div>
        <h3>${escapeHtml(run.repo_label || 'Repository')}</h3>
        <div class="run-id">${escapeHtml(run.run_id)}</div>
        <div class="run-card-meta"><span>Decision ${escapeHtml(summary.review_decision || 'unknown')}</span><span>Human review ${escapeHtml(human)}</span><span>Gate ${escapeHtml((summary.quality_gate || {}).status || 'not available')}</span><span>${escapeHtml(timestamp)}</span></div>
      </article>`;
  }

  function bindRunCards() {
    document.querySelectorAll('[data-open-run]').forEach(card => {
      const open = () => openRun(card.dataset.openRun);
      card.addEventListener('click', open);
      card.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') open(); });
    });
  }

  async function refreshRuns() {
    state.runs = await fetchJson('/api/runs');
    return state.runs;
  }

  function capabilityCards() {
    const capabilities = [
      ['01', 'Backend Side Effects', 'Inspect API, database and external side-effect evidence.'],
      ['02', 'Transactions & Database', 'Review explicit coverage, unknowns and TypeORM provenance.'],
      ['03', 'Queue & Cache', 'Correlate producers, consumers, retry and idempotency signals.'],
      ['04', 'Permission & AuthZ', 'Surface route protection and authorization review gaps.'],
      ['05', 'Code Health', 'Prioritize maintainability findings without claiming correctness.'],
      ['06', 'AI Maintenance Context', 'Build a grounded Context Pack REVIEW handoff.'],
    ];
    return capabilities.map(([number, name, description]) => `<article class="capability-card"><b>${number}</b><h3>${name}</h3><p>${description}</p></article>`).join('');
  }

  async function renderHome() {
    setHeader('Home', 'Repository Review Workbench');
    await refreshRuns();
    const recent = state.runs.slice(0, 6);
    view.innerHTML = `
      <section class="hero-grid">
        <div class="hero-panel"><span class="eyebrow">Facts → Patterns → Review</span><h2>Turn a repository into an evidence-backed review workspace.</h2><p>Run the complete Repository Review pipeline, follow each stage, then move through human review, transactions, permissions, reliability, and AI maintenance context.</p><div class="hero-actions"><button class="studio-button primary" data-go="analyze">Analyze Repository</button><button class="studio-button ghost" data-go="runs">Browse Recent Runs</button></div></div>
        <aside class="principle-panel"><div><h3>Review boundaries stay visible.</h3><ol><li>Static evidence only</li><li>Missing is not zero</li><li>Suspected requires review</li></ol></div><small>RepoSense does not execute target repositories and does not certify that a repository is secure or correct.</small></aside>
      </section>
      <div class="section-heading"><div><span class="eyebrow">Continue where you left off</span><h2>Recent Runs</h2></div><button class="studio-button" data-go="runs">View all</button></div>
      <div class="run-grid">${recent.length ? recent.map(runCard).join('') : '<div class="empty-panel">No local runs yet. Start with Full Repository Review.</div>'}</div>
      <div class="section-heading"><div><span class="eyebrow">Native review surfaces</span><h2>What RepoSense Reviews</h2></div></div>
      <div class="capability-grid">${capabilityCards()}</div>`;
    view.querySelectorAll('[data-go]').forEach(button => button.addEventListener('click', () => navigate(button.dataset.go)));
    bindRunCards();
  }

  async function renderRuns() {
    setHeader('Recent Runs', 'Local review history');
    await refreshRuns();
    view.innerHTML = `<div class="section-heading"><div><span class="eyebrow">Run history</span><h2>Open a Review Workspace</h2></div><button class="studio-button primary" data-go="analyze">New analysis</button></div><div class="run-grid">${state.runs.length ? state.runs.map(runCard).join('') : '<div class="empty-panel">No runs are available.</div>'}</div>`;
    view.querySelector('[data-go="analyze"]').addEventListener('click', () => navigate('analyze'));
    bindRunCards();
  }

  async function renderAnalyze() {
    setHeader('Analyze Repository', 'Choose source and review depth');
    await window.StudioAnalyzeForm.mount(view, {onRunCreated: runId => openRun(runId)});
  }

  function findArtifact(run, artifactId) {
    let match = null;
    (run.artifact_groups || []).some(group => (group.artifacts || []).some(item => {
      if (item.artifact_id === artifactId) { match = item; return true; }
      return false;
    }));
    return match;
  }

  async function openRun(runId) {
    stopPolling();
    state.view = 'workbench';
    setActiveNav('workbench');
    setHeader('Review Workspace', 'Evidence-backed repository review');
    view.innerHTML = '<div class="loading-panel">Loading review workspace...</div>';
    try {
      state.currentRun = await fetchJson(`/api/runs/${encodeURIComponent(runId)}`);
      renderCurrentRun();
      if (['queued', 'running'].includes(state.currentRun.status)) startPolling(runId);
    } catch (error) {
      view.innerHTML = `<div class="empty-panel">Run could not be loaded: ${escapeHtml(error.message)}</div>`;
    }
  }

  function renderCurrentRun() {
    const run = state.currentRun;
    const summary = run.summary || {};
    topStatus.innerHTML = `${pill(run.status)} ${pill(summary.review_decision, 'Decision ' + (summary.review_decision || 'unknown'))}`;
    topActions.innerHTML = '<button class="studio-button" id="back-to-runs">Run List</button>';
    const mainReport = findArtifact(run, 'main_html_report');
    if (mainReport && mainReport.url) topActions.innerHTML += `<a class="studio-button primary" target="_blank" rel="noopener" href="${escapeHtml(mainReport.url)}">Open Main Report</a>`;
    topActions.querySelector('#back-to-runs').addEventListener('click', () => navigate('runs'));
    window.StudioRunWorkbench.render(view, run);
  }

  function startPolling(runId) {
    state.pollTimer = window.setInterval(async () => {
      try {
        const updated = await fetchJson(`/api/runs/${encodeURIComponent(runId)}`);
        if (state.view !== 'workbench' || updated.run_id !== runId) return;
        state.currentRun = updated;
        renderCurrentRun();
        if (!['queued', 'running'].includes(updated.status)) stopPolling();
      } catch (error) {
        stopPolling();
      }
    }, 1200);
  }

  function stopPolling() {
    if (state.pollTimer) window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }

  async function renderWorkbenchPicker() {
    if (state.currentRun) { renderCurrentRun(); return; }
    setHeader('Review Workspace', 'Select a local run');
    await refreshRuns();
    view.innerHTML = `<div class="section-heading"><div><span class="eyebrow">Choose evidence</span><h2>Select a Run</h2></div></div><div class="run-grid">${state.runs.map(runCard).join('') || '<div class="empty-panel">No runs are available.</div>'}</div>`;
    bindRunCards();
  }

  async function renderLearn() {
    setHeader('Learn', 'Grounded Concepts → Cases → Evidence');
    await refreshRuns();
    const withLearn = state.runs.filter(run => findArtifact(run, 'learn_index'));
    view.innerHTML = `<div class="section-heading"><div><span class="eyebrow">Generated learning views</span><h2>Learn from a completed run</h2></div></div><div class="run-grid">${withLearn.map(runCard).join('') || '<div class="empty-panel">No run with a generated Learn site is available.</div>'}</div>`;
    bindRunCards();
  }

  function renderDocumentation() {
    setHeader('Documentation', 'Workbench quick reference');
    view.innerHTML = `<article class="docs-panel"><span class="run-profile">Local documentation entry</span><h2>Repository Review Workbench</h2><p>Use <strong>Full Repository Review</strong> for the complete review workflow. Use <strong>Quick Scan</strong> for API, event graph, report, Context Pack and validation outputs with the deeper domain review stages skipped.</p><h3>Source documentation</h3><p>The source distribution documents this UI in <code>docs/studio/STUDIO_UI.md</code> and <code>docs/studio/STUDIO_WORKBENCH.md</code>.</p><h3>Interpretation boundary</h3><p>Available means the artifact was generated. Zero means a generated artifact reported zero observations. Not generated means no conclusion can be drawn from that capability. Malformed means the artifact requires inspection.</p></article>`;
  }

  async function navigate(name) {
    stopPolling();
    state.view = name;
    setActiveNav(name);
    view.focus();
    try {
      if (name === 'home') await renderHome();
      else if (name === 'analyze') await renderAnalyze();
      else if (name === 'runs') await renderRuns();
      else if (name === 'workbench') await renderWorkbenchPicker();
      else if (name === 'learn') await renderLearn();
      else if (name === 'documentation') renderDocumentation();
    } catch (error) {
      view.innerHTML = `<div class="empty-panel">Studio could not load this view: ${escapeHtml(error.message)}</div>`;
    }
  }

  document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => navigate(button.dataset.view)));
  window.StudioWorkbenchApp = {navigate, openRun, state};
  navigate('home');
}());
