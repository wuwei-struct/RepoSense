(function () {
  'use strict';

  const TABS = ['overview', 'human', 'architecture', 'transactions', 'queue', 'permission', 'health', 'validation', 'context', 'artifacts'];
  // English locale tabs: Overview, Human Review, Architecture & API,
  // Transactions & Database, Queue & Cache, Permission & AuthZ,
  // Code Health, Validation, Context Pack, Artifacts.
  let activeTab = 'overview';

  function t(key, params) { return window.StudioI18n.t(key, params); }
  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  function statusPill(value, label) {
    const status = String(value || 'not_available').toLowerCase();
    return `<span class="status-pill ${escapeHtml(status)}">${escapeHtml(label || window.StudioI18n.formatStatus(status))}</span>`;
  }

  function artifactMap(run) {
    const map = new Map();
    (run.artifact_groups || []).forEach(group => (group.artifacts || []).forEach(item => map.set(item.artifact_id, item)));
    (run.recommended_artifacts || []).forEach(item => map.set(item.artifact_id, item));
    return map;
  }

  function artifactText(item, field) {
    const catalogs = window.RepoSenseStudioLocales || {};
    const locale = window.StudioI18n.getLocale();
    const key = `artifacts.${item.artifact_id}.${field}`;
    return (catalogs[locale] || {})[key] || (catalogs['en-US'] || {})[key] || item[field === 'name' ? 'display_name' : field] || '';
  }

  function openArtifact(item, label) {
    if (!item || !item.url) return '';
    return `<a class="studio-button" target="_blank" rel="noopener" href="${escapeHtml(item.url)}">${escapeHtml(label || t('common.open'))}</a>`;
  }

  function valueCard(label, value, availability, note) {
    if (availability === 'malformed') {
      return `<div class="summary-stat"><span>${escapeHtml(label)}</span><strong>${t('workbench.needsReview')}</strong><small>${t('workbench.malformed')}</small></div>`;
    }
    if (availability !== 'available') {
      return `<div class="summary-stat"><span>${escapeHtml(label)}</span><strong>${t('workbench.notGenerated')}</strong><small>${t('workbench.unavailable')}</small></div>`;
    }
    return `<div class="summary-stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong>${note ? `<small>${escapeHtml(note)}</small>` : ''}</div>`;
  }

  function pipelineMarkup(run) {
    const steps = ((run.pipeline || {}).steps || []);
    if (!steps.length) return `<p class="state-note">${t('pipeline.unavailable')}</p>`;
    return `<div class="pipeline-rail" aria-label="${t('pipeline.label')}">${steps.map(step => {
      const label = t(`pipeline.${step.step_id}`);
      const status = window.StudioI18n.formatStatus(step.status);
      return `<div class="pipeline-step ${escapeHtml(step.status)}" title="${escapeHtml(label)}: ${escapeHtml(status)}">
        <div class="step-line"></div><span>${escapeHtml(label)}</span>
      </div>`;
    }).join('')}</div>`;
  }

  function artifactRows(run, categories) {
    const rows = [];
    (run.artifact_groups || []).forEach(group => {
      (group.artifacts || []).forEach(item => { if (categories.includes(item.category)) rows.push(item); });
    });
    if (!rows.length) return `<p class="state-note">${t('workbench.artifactMissing')}</p>`;
    return `<div class="action-list">${rows.map(item => `
      <div class="artifact-link-row"><div><strong>${escapeHtml(artifactText(item, 'name'))}</strong><br><small>${escapeHtml(artifactText(item, 'description'))}</small></div>${openArtifact(item)}</div>`).join('')}</div>`;
  }

  function overview(run, artifacts) {
    const summary = run.summary || {};
    const facts = summary.repository_facts || {};
    const actions = summary.recommended_actions || [];
    const factCards = [
      ['metric.apiEndpoints', facts.api_endpoints], ['metric.dbReads', facts.db_reads], ['metric.dbWrites', facts.db_writes],
      ['metric.transactions', facts.transaction_correlations], ['metric.queueDispatch', facts.queue_dispatch],
      ['metric.queueConsumers', facts.queue_consumers], ['metric.cacheOperations', facts.cache_operations],
      ['metric.permissionRisks', facts.permission_risks], ['metric.healthFindings', facts.code_health_findings],
    ].map(([key, fact]) => valueCard(t(key), (fact || {}).value || 0, (fact || {}).availability)).join('');
    const reviewCards = [
      ['metric.reviewDecision', window.StudioI18n.formatStatus(summary.review_decision), 'available'],
      ['metric.humanReview', summary.human_review_required_count || 0, summary.human_review_required_status],
      ['metric.patterns', (summary.counts || {}).patterns || 0, (summary.count_availability || {}).patterns],
      ['metric.evidence', window.StudioI18n.formatStatus((summary.evidence_integrity || {}).status), (summary.evidence_integrity || {}).status === 'not_available' ? 'not_generated' : 'available'],
      ['metric.strict', window.StudioI18n.formatStatus((summary.strict_verify || {}).status), (summary.strict_verify || {}).status === 'not_available' ? 'not_generated' : 'available'],
      ['metric.gate', window.StudioI18n.formatStatus((summary.quality_gate || {}).status), (summary.quality_gate || {}).status === 'not_available' ? 'not_generated' : 'available'],
    ].map(([key, value, state]) => valueCard(t(key), value, state)).join('');
    const actionRows = actions.length ? actions.map(action => {
      const item = artifacts.get(action.artifact_id);
      const label = t(`action.${action.action_id}`);
      return `<div class="action-row"><span>${escapeHtml(label)}</span>${openArtifact(item)}</div>`;
    }).join('') : `<p class="state-note">${t('workbench.actionsUnavailable')}</p>`;
    return `
      <div class="section-heading"><div><span class="eyebrow">${t('workbench.decisionSignals')}</span><h3>${t('workbench.reviewSummary')}</h3></div></div>
      <div class="summary-grid">${reviewCards}</div>
      <div class="section-heading"><div><span class="eyebrow">${t('workbench.observedFacts')}</span><h3>${t('workbench.repositoryFacts')}</h3></div></div>
      <div class="domain-grid">${factCards}</div>
      <div class="section-heading"><div><span class="eyebrow">${t('workbench.evidenceRouting')}</span><h3>${t('workbench.nextActions')}</h3></div></div>
      <div class="action-list">${actionRows}</div>`;
  }

  function domainPanel(run, domain, categories, metrics) {
    const data = (((run.summary || {}).domain_summaries || {})[domain]) || {};
    const availability = data.availability || 'not_generated';
    const state = availability === 'available' ? '' : `<p class="state-note ${availability === 'malformed' ? 'malformed' : ''}">${availability === 'malformed' ? t('workbench.malformedSupporting') : t('workbench.missingSupporting')}</p>`;
    const cards = metrics.map(([key, valueKey, noteKey]) => valueCard(t(key), data[valueKey] || 0, availability, noteKey ? t(noteKey) : '')).join('');
    return `${state}<div class="summary-grid">${cards}</div><div class="section-heading"><div><span class="eyebrow">${t('workbench.generatedEvidence')}</span><h3>${t('workbench.relevantArtifacts')}</h3></div></div>${artifactRows(run, categories)}`;
  }

  function tabContent(run, tab, artifacts) {
    const summary = run.summary || {};
    if (tab === 'overview') return overview(run, artifacts);
    if (tab === 'human') {
      const state = summary.human_review_required_status || 'not_available';
      return `${valueCard(t('metric.humanReview'), summary.human_review_required_count || 0, state)}
        <div class="section-heading"><div><span class="eyebrow">${t('workbench.reviewerHandoff')}</span><h3>${t('workbench.reviewReports')}</h3></div></div>
        <div class="action-list">
          <div class="action-row"><span>${t('metric.humanReview')}</span>${openArtifact(artifacts.get('human_review_required'))}</div>
          <div class="action-row"><span>${artifactText(artifacts.get('repository_review_report') || {artifact_id: 'repository_review_report', display_name: 'Repository Review Report'}, 'name')}</span>${openArtifact(artifacts.get('repository_review_report'))}</div>
        </div>`;
    }
    if (tab === 'architecture') return domainPanel(run, 'architecture', ['overview', 'backend'], [
      ['metric.apiEndpoints', 'api_endpoints'], ['metric.crossLanguage', 'cross_language_links'],
    ]);
    if (tab === 'transactions') return domainPanel(run, 'transactions', ['transaction', 'database'], [
      ['metric.dbReads', 'db_reads'], ['metric.dbWrites', 'db_writes'], ['metric.correlations', 'total_correlations'],
      ['metric.covered', 'covered'], ['metric.uncovered', 'uncovered'], ['metric.unknown', 'unknown'],
      ['metric.typeorm', 'typeorm_operations'], ['metric.aliases', 'resolved_aliases'],
    ]);
    if (tab === 'queue') return domainPanel(run, 'queue', ['messaging'], [
      ['metric.dispatch', 'dispatch'], ['metric.consumers', 'consumers'], ['metric.channels', 'matched_channels'],
      ['metric.cacheOperations', 'cache_operations'], ['metric.retryRisks', 'retry_risks'],
    ]);
    if (tab === 'permission') return domainPanel(run, 'permission', ['permission'], [
      ['metric.permissionRisks', 'risks'], ['metric.routes', 'routes'], ['metric.authzMode', 'authz_mode'],
      ['metric.missingAuth', 'missing_auth'], ['metric.humanPermissionReview', 'human_review'],
    ]);
    if (tab === 'health') return domainPanel(run, 'code_health', ['code_health'], [
      ['metric.findings', 'findings'], ['metric.high', 'high'], ['metric.medium', 'medium'], ['metric.score', 'score', 'workbench.heuristicScore'],
    ]);
    if (tab === 'validation') {
      return `<div class="summary-grid">
        ${valueCard(t('metric.evidence'), window.StudioI18n.formatStatus((summary.evidence_integrity || {}).status), (summary.evidence_integrity || {}).status === 'not_available' ? 'not_generated' : 'available')}
        ${valueCard(t('metric.strict'), window.StudioI18n.formatStatus((summary.strict_verify || {}).status), (summary.strict_verify || {}).status === 'not_available' ? 'not_generated' : 'available')}
        ${valueCard(t('metric.gate'), window.StudioI18n.formatStatus((summary.quality_gate || {}).status), (summary.quality_gate || {}).status === 'not_available' ? 'not_generated' : 'available')}
      </div>${(summary.warnings || []).length ? `<p class="state-note malformed">${escapeHtml(summary.warnings.join(' '))}</p>` : ''}
      <div class="section-heading"><div><span class="eyebrow">${t('workbench.trustEvidence')}</span><h3>${t('workbench.validationArtifacts')}</h3></div></div>${artifactRows(run, ['validation'])}`;
    }
    if (tab === 'context') return artifactRows(run, ['context']);
    if (tab === 'artifacts') return '<div id="current-artifact-cards"></div>';
    return '';
  }

  function render(target, run, options) {
    const artifacts = artifactMap(run || {});
    const profile = run.profile || {};
    activeTab = (options || {}).initialTab || activeTab || 'overview';
    const profileName = t(`profile.${profile.profile_id}.name`);
    target.innerHTML = `
      <section class="workbench-run-header">
        <div class="header-row"><div><span class="run-profile">${escapeHtml(profile.profile_id ? profileName : t('runs.historical'))}</span>
        <h2>${escapeHtml(run.repo_label || t('workbench.repositoryReview'))}</h2><div class="run-id">${escapeHtml(run.run_id)}</div></div>
        <div>${statusPill(run.status)} ${statusPill((run.summary || {}).review_decision, t('runs.decision', {value: window.StudioI18n.formatStatus((run.summary || {}).review_decision)}))}</div></div>
        ${pipelineMarkup(run)}
        ${run.error_message ? `<p class="state-note malformed">${escapeHtml(run.error_message)}</p>` : ''}
      </section>
      <nav class="workbench-tabs" aria-label="${t('workbench.sectionsLabel')}">${TABS.map(id => `<button type="button" data-workbench-tab="${id}" class="${id === activeTab ? 'active' : ''}">${t(`workbench.${id}`)}</button>`).join('')}</nav>
      <section id="workbench-tab-content"></section>`;
    const content = target.querySelector('#workbench-tab-content');
    function show(tab) {
      activeTab = tab;
      target.querySelectorAll('[data-workbench-tab]').forEach(button => button.classList.toggle('active', button.dataset.workbenchTab === tab));
      content.innerHTML = tabContent(run, tab, artifacts);
      if (tab === 'artifacts' && window.StudioArtifactCards) {
        window.StudioArtifactCards.render(content.querySelector('#current-artifact-cards'), run);
      }
    }
    target.querySelectorAll('[data-workbench-tab]').forEach(button => button.addEventListener('click', () => show(button.dataset.workbenchTab)));
    show(activeTab);
  }

  window.StudioRunWorkbench = {render, tabs: TABS.slice(), getActiveTab: () => activeTab};
}());
