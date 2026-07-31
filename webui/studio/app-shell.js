(function () {
  'use strict';

  const i18n = window.StudioI18n;
  i18n.initI18n();

  // English locale navigation: Home, Analyze Repository, Recent Runs,
  // Review Workspace, Learn, Documentation.

  const state = {view: 'home', runs: [], currentRun: null, pollTimer: null};
  const view = document.getElementById('studio-view');
  const title = document.getElementById('page-title');
  const kicker = document.getElementById('page-kicker');
  const topStatus = document.getElementById('topbar-status');
  const topActions = document.getElementById('topbar-actions');

  function t(key, params) { return i18n.t(key, params); }
  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  function pill(value, label) {
    const status = String(value || 'unknown').toLowerCase();
    return `<span class="status-pill ${escapeHtml(status)}">${escapeHtml(label || i18n.formatStatus(status))}</span>`;
  }

  async function fetchJson(path, options) {
    const response = await fetch(new URL(path, window.location.origin).toString(), options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);
    return data;
  }

  function setHeader(titleKey, kickerKey) {
    title.textContent = t(titleKey);
    kicker.textContent = t(kickerKey || 'app.workbench');
    topStatus.innerHTML = '';
    topActions.innerHTML = '';
  }

  function setActiveNav(name) {
    document.querySelectorAll('[data-view]').forEach(button => button.classList.toggle('active', button.dataset.view === name));
  }

  function profileName(profile) {
    if (!profile.profile_id) return t('runs.historical');
    const key = `profile.${profile.profile_id}.name`;
    const value = t(key);
    return value === key ? profile.display_name || profile.profile_id : value;
  }

  function runCard(run) {
    const summary = run.summary || {};
    const profile = run.profile || {};
    const timestamp = new Date((run.updated_at || run.start_time || 0) * 1000).toLocaleString(i18n.getLocale());
    const human = summary.human_review_required_status === 'available' ? summary.human_review_required_count : t('runs.notGenerated');
    return `
      <article class="run-summary-card" data-open-run="${escapeHtml(run.run_id)}" tabindex="0">
        <div class="run-card-top"><span class="run-profile">${escapeHtml(profileName(profile))}</span>${pill(run.status)}</div>
        <h3>${escapeHtml(run.repo_label || t('runs.repository'))}</h3>
        <div class="run-id">${escapeHtml(run.run_id)}</div>
        <div class="run-card-meta"><span>${escapeHtml(t('runs.decision', {value: i18n.formatStatus(summary.review_decision)}))}</span><span>${escapeHtml(t('runs.humanReview', {value: human}))}</span><span>${escapeHtml(t('runs.gate', {value: i18n.formatStatus((summary.quality_gate || {}).status)}))}</span><span>${escapeHtml(timestamp)}</span></div>
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
    const capabilities = ['backend', 'transactions', 'messaging', 'permission', 'health', 'ai'];
    return capabilities.map((id, index) => `<article class="capability-card"><b>${String(index + 1).padStart(2, '0')}</b><h3>${t(`home.capability.${id}.name`)}</h3><p>${t(`home.capability.${id}.description`)}</p></article>`).join('');
  }

  async function renderHome() {
    setHeader('nav.home', 'app.workbench');
    await refreshRuns();
    const recent = state.runs.slice(0, 6);
    view.innerHTML = `
      <section class="hero-grid">
        <div class="hero-panel"><span class="eyebrow">${t('home.kicker')}</span><h2>${t('home.title')}</h2><p>${t('home.description')}</p><div class="hero-actions"><button class="studio-button primary" data-go="analyze">${t('home.analyzeRepository')}</button><button class="studio-button ghost" data-go="runs">${t('home.browseRuns')}</button></div></div>
        <aside class="principle-panel"><div><h3>${t('home.boundaryTitle')}</h3><ol><li>${t('home.boundaryStatic')}</li><li>${t('home.boundaryMissing')}</li><li>${t('home.boundarySuspected')}</li></ol></div><small>${t('home.boundaryNote')}</small></aside>
      </section>
      <div class="section-heading"><div><span class="eyebrow">${t('home.continue')}</span><h2>${t('home.recentRuns')}</h2></div><button class="studio-button" data-go="runs">${t('common.viewAll')}</button></div>
      <div class="run-grid">${recent.length ? recent.map(runCard).join('') : `<div class="empty-panel">${t('home.noRuns')}</div>`}</div>
      <div class="section-heading"><div><span class="eyebrow">${t('home.nativeSurfaces')}</span><h2>${t('home.whatReviews')}</h2></div></div>
      <div class="capability-grid">${capabilityCards()}</div>`;
    view.querySelectorAll('[data-go]').forEach(button => button.addEventListener('click', () => navigate(button.dataset.go)));
    bindRunCards();
  }

  async function renderRuns() {
    setHeader('nav.runs', 'shell.localHistory');
    await refreshRuns();
    view.innerHTML = `<div class="section-heading"><div><span class="eyebrow">${t('runs.history')}</span><h2>${t('runs.openWorkspace')}</h2></div><button class="studio-button primary" data-go="analyze">${t('runs.newAnalysis')}</button></div><div class="run-grid">${state.runs.length ? state.runs.map(runCard).join('') : `<div class="empty-panel">${t('runs.none')}</div>`}</div>`;
    view.querySelector('[data-go="analyze"]').addEventListener('click', () => navigate('analyze'));
    bindRunCards();
  }

  async function renderAnalyze() {
    setHeader('nav.analyze', 'shell.analyzeSubtitle');
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
    setHeader('shell.reviewWorkspace', 'shell.evidenceReview');
    view.innerHTML = `<div class="loading-panel">${t('shell.loadingWorkbench')}</div>`;
    try {
      state.currentRun = await fetchJson(`/api/runs/${encodeURIComponent(runId)}`);
      renderCurrentRun();
      if (['queued', 'running'].includes(state.currentRun.status)) startPolling(runId);
    } catch (error) {
      view.innerHTML = `<div class="empty-panel">${escapeHtml(t('shell.runLoadFailed', {message: error.message}))}</div>`;
    }
  }

  function renderCurrentRun() {
    const run = state.currentRun;
    const summary = run.summary || {};
    setHeader('shell.reviewWorkspace', 'shell.evidenceReview');
    topStatus.innerHTML = `${pill(run.status)} ${pill(summary.review_decision, t('runs.decision', {value: i18n.formatStatus(summary.review_decision)}))}`;
    topActions.innerHTML = `<button class="studio-button" id="back-to-runs">${t('shell.runList')}</button>`;
    const mainReport = findArtifact(run, 'main_html_report');
    if (mainReport && mainReport.url) topActions.innerHTML += `<a class="studio-button primary" target="_blank" rel="noopener" href="${escapeHtml(mainReport.url)}">${t('shell.openMainReport')}</a>`;
    topActions.querySelector('#back-to-runs').addEventListener('click', () => navigate('runs'));
    window.StudioRunWorkbench.render(view, run, {initialTab: window.StudioRunWorkbench.getActiveTab()});
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
    setHeader('shell.reviewWorkspace', 'shell.selectRun');
    await refreshRuns();
    view.innerHTML = `<div class="section-heading"><div><span class="eyebrow">${t('shell.chooseEvidence')}</span><h2>${t('shell.selectRunTitle')}</h2></div></div><div class="run-grid">${state.runs.map(runCard).join('') || `<div class="empty-panel">${t('runs.none')}</div>`}</div>`;
    bindRunCards();
  }

  async function renderLearn() {
    setHeader('nav.learn', 'shell.learnSubtitle');
    await refreshRuns();
    const withLearn = state.runs.filter(run => findArtifact(run, 'learn_index'));
    view.innerHTML = `<div class="section-heading"><div><span class="eyebrow">${t('shell.learnViews')}</span><h2>${t('shell.learnTitle')}</h2></div></div><div class="run-grid">${withLearn.map(runCard).join('') || `<div class="empty-panel">${t('shell.noLearn')}</div>`}</div>`;
    bindRunCards();
  }

  function renderDocumentation() {
    setHeader('nav.docs', 'shell.docsSubtitle');
    view.innerHTML = `<article class="docs-panel"><span class="run-profile">${t('shell.docsEntry')}</span><h2>${t('shell.docsTitle')}</h2><p>${t('shell.docsProfiles')}</p><h3>${t('shell.sourceDocs')}</h3><p>${t('shell.sourceDocsText')}</p><h3>${t('shell.interpretation')}</h3><p>${t('shell.interpretationText')}</p></article>`;
  }

  async function renderCurrentView() {
    if (state.view === 'home') await renderHome();
    else if (state.view === 'analyze') await renderAnalyze();
    else if (state.view === 'runs') await renderRuns();
    else if (state.view === 'workbench') await renderWorkbenchPicker();
    else if (state.view === 'learn') await renderLearn();
    else if (state.view === 'documentation') renderDocumentation();
  }

  async function navigate(name) {
    stopPolling();
    state.view = name;
    setActiveNav(name);
    view.focus();
    try {
      await renderCurrentView();
    } catch (error) {
      view.innerHTML = `<div class="empty-panel">${escapeHtml(t('shell.loadFailed', {message: error.message}))}</div>`;
    }
  }

  document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => navigate(button.dataset.view)));
  i18n.mountLanguageSwitcher(document.getElementById('language-switcher-mount'));
  i18n.subscribeLocaleChange(async () => {
    i18n.translateDocument(document);
    try { await renderCurrentView(); } catch (error) { /* Existing safe view remains visible. */ }
  });
  window.StudioWorkbenchApp = {navigate, openRun, state};
  navigate('home');
}());
