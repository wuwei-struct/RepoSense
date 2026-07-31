(function () {
  'use strict';

  const TABS = [
    ['overview', 'Overview'],
    ['human', 'Human Review'],
    ['architecture', 'Architecture & API'],
    ['transactions', 'Transactions & Database'],
    ['queue', 'Queue & Cache'],
    ['permission', 'Permission & AuthZ'],
    ['health', 'Code Health'],
    ['validation', 'Validation'],
    ['context', 'Context Pack'],
    ['artifacts', 'Artifacts'],
  ];

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  function statusPill(value, label) {
    const status = String(value || 'not_available').toLowerCase();
    return `<span class="status-pill ${escapeHtml(status)}">${escapeHtml(label || status.replaceAll('_', ' '))}</span>`;
  }

  function artifactMap(run) {
    const map = new Map();
    (run.artifact_groups || []).forEach(group => (group.artifacts || []).forEach(item => map.set(item.artifact_id, item)));
    (run.recommended_artifacts || []).forEach(item => map.set(item.artifact_id, item));
    return map;
  }

  function openArtifact(item, label) {
    if (!item || !item.url) return '';
    return `<a class="studio-button" target="_blank" rel="noopener" href="${escapeHtml(item.url)}">${escapeHtml(label || 'Open')}</a>`;
  }

  function valueCard(label, value, availability, note) {
    if (availability === 'malformed') {
      return `<div class="summary-stat"><span>${escapeHtml(label)}</span><strong>Needs review</strong><small>Artifact could not be parsed.</small></div>`;
    }
    if (availability !== 'available') {
      return `<div class="summary-stat"><span>${escapeHtml(label)}</span><strong>Not generated</strong><small>Capability output is unavailable for this run.</small></div>`;
    }
    return `<div class="summary-stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong>${note ? `<small>${escapeHtml(note)}</small>` : ''}</div>`;
  }

  function pipelineMarkup(run) {
    const steps = ((run.pipeline || {}).steps || []);
    if (!steps.length) return '<p class="state-note">Structured pipeline progress is not available for this historical run.</p>';
    return `<div class="pipeline-rail" aria-label="Pipeline progress">${steps.map(step => `
      <div class="pipeline-step ${escapeHtml(step.status)}" title="${escapeHtml(step.label)}: ${escapeHtml(step.status)}">
        <div class="step-line"></div><span>${escapeHtml(step.label)}</span>
      </div>`).join('')}</div>`;
  }

  function artifactRows(run, categories) {
    const rows = [];
    (run.artifact_groups || []).forEach(group => {
      (group.artifacts || []).forEach(item => {
        if (categories.includes(item.category)) rows.push(item);
      });
    });
    if (!rows.length) return '<p class="state-note">Artifact not generated for this review area.</p>';
    return `<div class="action-list">${rows.map(item => `
      <div class="artifact-link-row"><div><strong>${escapeHtml(item.display_name)}</strong><br><small>${escapeHtml(item.description)}</small></div>${openArtifact(item)}</div>`).join('')}</div>`;
  }

  function overview(run, artifacts) {
    const summary = run.summary || {};
    const facts = summary.repository_facts || {};
    const actions = summary.recommended_actions || [];
    const factCards = [
      ['API endpoints', facts.api_endpoints], ['DB reads', facts.db_reads], ['DB writes', facts.db_writes],
      ['Transaction correlations', facts.transaction_correlations], ['Queue dispatch', facts.queue_dispatch],
      ['Queue consumers', facts.queue_consumers], ['Cache operations', facts.cache_operations],
      ['Permission risks', facts.permission_risks], ['Code Health findings', facts.code_health_findings],
    ].map(([label, fact]) => valueCard(label, (fact || {}).value || 0, (fact || {}).availability)).join('');
    const reviewCards = [
      ['Review Decision', summary.review_decision || 'UNKNOWN', 'available'],
      ['Human Review Required', summary.human_review_required_count || 0, summary.human_review_required_status],
      ['Patterns', (summary.counts || {}).patterns || 0, (summary.count_availability || {}).patterns],
      ['Evidence Integrity', (summary.evidence_integrity || {}).status || 'not available', (summary.evidence_integrity || {}).status === 'not_available' ? 'not_generated' : 'available'],
      ['Strict Verify', (summary.strict_verify || {}).status || 'not available', (summary.strict_verify || {}).status === 'not_available' ? 'not_generated' : 'available'],
      ['Quality Gate', (summary.quality_gate || {}).status || 'not available', (summary.quality_gate || {}).status === 'not_available' ? 'not_generated' : 'available'],
    ].map(([label, value, state]) => valueCard(label, value, state)).join('');
    const actionRows = actions.length ? actions.map(action => {
      const item = artifacts.get(action.artifact_id);
      return `<div class="action-row"><span>${escapeHtml(action.label)}</span>${openArtifact(item)}</div>`;
    }).join('') : '<p class="state-note">Recommended actions will appear when supporting artifacts are generated.</p>';
    return `
      <div class="section-heading"><div><span class="eyebrow">Decision and trust signals</span><h3>Review Summary</h3></div></div>
      <div class="summary-grid">${reviewCards}</div>
      <div class="section-heading"><div><span class="eyebrow">Observed facts</span><h3>Repository Facts</h3></div></div>
      <div class="domain-grid">${factCards}</div>
      <div class="section-heading"><div><span class="eyebrow">Evidence-backed routing</span><h3>Recommended Next Actions</h3></div></div>
      <div class="action-list">${actionRows}</div>`;
  }

  function domainPanel(run, domain, categories, metrics) {
    const data = (((run.summary || {}).domain_summaries || {})[domain]) || {};
    const availability = data.availability || 'not_generated';
    const state = availability === 'available' ? '' : `<p class="state-note ${availability === 'malformed' ? 'malformed' : ''}">${availability === 'malformed' ? 'A supporting artifact could not be parsed.' : 'This capability artifact was not generated. Values below are not interpreted as zero.'}</p>`;
    const cards = metrics.map(([label, key, note]) => valueCard(label, data[key] || 0, availability, note)).join('');
    return `${state}<div class="summary-grid">${cards}</div><div class="section-heading"><div><span class="eyebrow">Generated evidence</span><h3>Relevant artifacts</h3></div></div>${artifactRows(run, categories)}`;
  }

  function tabContent(run, tab, artifacts) {
    const summary = run.summary || {};
    if (tab === 'overview') return overview(run, artifacts);
    if (tab === 'human') {
      const state = summary.human_review_required_status || 'not_available';
      return `${valueCard('Human Review Required', summary.human_review_required_count || 0, state)}
        <div class="section-heading"><div><span class="eyebrow">Reviewer handoff</span><h3>Review reports</h3></div></div>
        <div class="action-list">
          <div class="action-row"><span>Human Review Required</span>${openArtifact(artifacts.get('human_review_required'))}</div>
          <div class="action-row"><span>Repository Review Report</span>${openArtifact(artifacts.get('repository_review_report'))}</div>
        </div>`;
    }
    if (tab === 'architecture') return domainPanel(run, 'architecture', ['overview', 'backend'], [
      ['API endpoints', 'api_endpoints'], ['Cross-language links', 'cross_language_links'],
    ]);
    if (tab === 'transactions') return domainPanel(run, 'transactions', ['transaction', 'database'], [
      ['DB reads', 'db_reads'], ['DB writes', 'db_writes'], ['Correlations', 'total_correlations'],
      ['Covered', 'covered'], ['Uncovered', 'uncovered'], ['Unknown', 'unknown'],
      ['TypeORM operations', 'typeorm_operations'], ['Resolved aliases', 'resolved_aliases'],
    ]);
    if (tab === 'queue') return domainPanel(run, 'queue', ['messaging'], [
      ['Dispatch', 'dispatch'], ['Consumers', 'consumers'], ['Matched channels', 'matched_channels'],
      ['Cache operations', 'cache_operations'], ['Retry / idempotency risks', 'retry_risks'],
    ]);
    if (tab === 'permission') return domainPanel(run, 'permission', ['permission'], [
      ['Permission risks', 'risks'], ['Routes', 'routes'], ['AuthZ Matrix mode', 'authz_mode'],
      ['Missing auth', 'missing_auth'], ['Human review', 'human_review'],
    ]);
    if (tab === 'health') return domainPanel(run, 'code_health', ['code_health'], [
      ['Findings', 'findings'], ['High', 'high'], ['Medium', 'medium'], ['Experimental score', 'score', 'Heuristic, not a correctness score'],
    ]);
    if (tab === 'validation') {
      return `<div class="summary-grid">
        ${valueCard('Evidence Integrity', (summary.evidence_integrity || {}).status, (summary.evidence_integrity || {}).status === 'not_available' ? 'not_generated' : 'available')}
        ${valueCard('Strict Verify', (summary.strict_verify || {}).status, (summary.strict_verify || {}).status === 'not_available' ? 'not_generated' : 'available')}
        ${valueCard('Quality Gate', (summary.quality_gate || {}).status, (summary.quality_gate || {}).status === 'not_available' ? 'not_generated' : 'available')}
      </div>${(summary.warnings || []).length ? `<p class="state-note malformed">${escapeHtml(summary.warnings.join(' '))}</p>` : ''}
      <div class="section-heading"><div><span class="eyebrow">Trust evidence</span><h3>Validation artifacts</h3></div></div>${artifactRows(run, ['validation'])}`;
    }
    if (tab === 'context') return artifactRows(run, ['context']);
    if (tab === 'artifacts') return '<div id="current-artifact-cards"></div>';
    return '';
  }

  function render(target, run, options) {
    const artifacts = artifactMap(run || {});
    const profile = run.profile || {};
    target.innerHTML = `
      <section class="workbench-run-header">
        <div class="header-row"><div><span class="run-profile">${escapeHtml(profile.display_name || profile.profile_id || 'Historical run')}</span>
        <h2>${escapeHtml(run.repo_label || 'Repository review')}</h2><div class="run-id">${escapeHtml(run.run_id)}</div></div>
        <div>${statusPill(run.status)} ${statusPill((run.summary || {}).review_decision, 'Decision ' + ((run.summary || {}).review_decision || 'unknown'))}</div></div>
        ${pipelineMarkup(run)}
        ${run.error_message ? `<p class="state-note malformed">${escapeHtml(run.error_message)}</p>` : ''}
      </section>
      <nav class="workbench-tabs" aria-label="Review workspace sections">${TABS.map(([id, label], index) => `<button type="button" data-workbench-tab="${id}" class="${index === 0 ? 'active' : ''}">${label}</button>`).join('')}</nav>
      <section id="workbench-tab-content"></section>`;
    const content = target.querySelector('#workbench-tab-content');
    function show(tab) {
      target.querySelectorAll('[data-workbench-tab]').forEach(button => button.classList.toggle('active', button.dataset.workbenchTab === tab));
      content.innerHTML = tabContent(run, tab, artifacts);
      if (tab === 'artifacts' && window.StudioArtifactCards) {
        window.StudioArtifactCards.render(content.querySelector('#current-artifact-cards'), run);
      }
    }
    target.querySelectorAll('[data-workbench-tab]').forEach(button => button.addEventListener('click', () => show(button.dataset.workbenchTab)));
    show((options || {}).initialTab || 'overview');
  }

  window.StudioRunWorkbench = {render, tabs: TABS.map(item => item[0])};
}());
