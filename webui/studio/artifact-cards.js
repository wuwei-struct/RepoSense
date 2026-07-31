(function () {
  'use strict';

  function t(key, params) { return window.StudioI18n.t(key, params); }
  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function localizedArtifact(artifact, field) {
    const catalogs = window.RepoSenseStudioLocales || {};
    const locale = window.StudioI18n.getLocale();
    const key = `artifacts.${artifact.artifact_id}.${field}`;
    return (catalogs[locale] || {})[key] || (catalogs['en-US'] || {})[key] || artifact[field === 'name' ? 'display_name' : field] || '';
  }

  function statusLabel(status) {
    return window.StudioI18n.formatStatus(status);
  }

  function statusClass(status) {
    const value = String(status || 'unknown').toLowerCase();
    if (value === 'pass') return 'is-pass';
    if (value === 'warn' || value === 'review' || value === 'needs_review') return 'is-warn';
    if (value === 'fail' || value === 'block') return 'is-fail';
    return 'is-muted';
  }

  function statusItem(label, status, detail) {
    return `
      <div class="artifact-status-item ${statusClass(status)}">
        <div class="artifact-status-label">${escapeHtml(label)}</div>
        <div class="artifact-status-value">${escapeHtml(statusLabel(status))}</div>
        ${detail ? `<div class="artifact-status-detail">${escapeHtml(detail)}</div>` : ''}
      </div>`;
  }

  function metadataLabel(prefix, value) {
    const key = `${prefix}.${String(value || 'other').toLowerCase()}`;
    const translated = t(key);
    return translated === key ? String(value || '') : translated;
  }

  function artifactCard(artifact, compact) {
    const open = artifact.available && artifact.url
      ? `<a class="artifact-open" href="${escapeHtml(artifact.url)}" target="_blank" rel="noopener">${t('artifact.open')}</a>`
      : `<span class="artifact-unavailable">${t('artifact.notGenerated')}</span>`;
    return `
      <article class="artifact-card ${compact ? 'artifact-card-compact' : ''}">
        <div class="artifact-card-heading">
          <h4>${escapeHtml(localizedArtifact(artifact, 'name'))}</h4>
          <span class="artifact-format">${escapeHtml(metadataLabel('format', artifact.format))}</span>
        </div>
        <p>${escapeHtml(localizedArtifact(artifact, 'description'))}</p>
        <dl class="artifact-meta">
          <div><dt>${t('artifact.audience')}</dt><dd>${escapeHtml(metadataLabel('audience', artifact.audience))}</dd></div>
          <div><dt>${t('artifact.priority')}</dt><dd>${escapeHtml(metadataLabel('priority', artifact.priority))}</dd></div>
        </dl>
        <div class="artifact-action">${escapeHtml(localizedArtifact(artifact, 'recommended_action'))}</div>
        <div class="artifact-card-actions">
          ${open}
          <button type="button" class="artifact-copy-path" data-relative-path="${escapeHtml(artifact.relative_path)}">${t('artifact.copyPath')}</button>
        </div>
      </article>`;
  }

  function warningRows(summary, recommended) {
    const rows = [];
    const evidence = summary.evidence_integrity || {};
    const strict = summary.strict_verify || {};
    const gate = summary.quality_gate || {};
    const validation = summary.validation || {};
    const decision = String(summary.review_decision || 'UNKNOWN').toLowerCase();
    const recommendation = recommended && recommended.url
      ? `<a href="${escapeHtml(recommended.url)}" target="_blank" rel="noopener">${t('artifact.open')} ${escapeHtml(localizedArtifact(recommended, 'name'))}</a>.`
      : t('workbench.actionsUnavailable');
    if (evidence.status === 'fail' || evidence.status === 'warn') {
      rows.push(`<li><strong>${t('metric.evidence')} ${escapeHtml(statusLabel(evidence.status))}.</strong> ${recommendation}</li>`);
    }
    if (strict.status === 'fail') {
      rows.push(`<li><strong>${t('metric.strict')} ${escapeHtml(statusLabel(strict.status))}.</strong> ${recommendation}</li>`);
    }
    if (gate.status === 'fail' || gate.status === 'warn') {
      rows.push(`<li><strong>${t('metric.gate')} ${escapeHtml(statusLabel(gate.status))}.</strong> ${escapeHtml((gate.reasons || [])[0] || t('workbench.actionsUnavailable'))}</li>`);
    }
    if (validation.status === 'needs_review' || validation.status === 'fail') {
      rows.push(`<li><strong>${t('artifact.validationStatus')} ${escapeHtml(statusLabel(validation.status))}.</strong> ${recommendation}</li>`);
    }
    if (decision === 'review' || decision === 'block') {
      rows.push(`<li><strong>${t('metric.reviewDecision')}: ${escapeHtml(decision.toUpperCase())}.</strong> ${recommendation}</li>`);
    }
    (summary.warnings || []).forEach(warning => {
      rows.push(`<li><strong>${t('artifact.parseWarning')}</strong> ${escapeHtml(warning)}</li>`);
    });
    if (rows.length === 0 && evidence.status === 'pass' && strict.status === 'pass') {
      rows.push(`<li><strong>${t('artifact.safePass')}</strong> ${t('artifact.notProof')}</li>`);
    }
    return rows;
  }

  function groupName(group) {
    const key = `artifact.group.${group.group_id}`;
    const value = t(key);
    return value === key ? group.display_name : value;
  }

  function localizedCondition(value) {
    if (window.StudioI18n.getLocale() === 'en-US') return value;
    const conditions = {
      'Repository Review is generated': 'repositoryReview',
      'A CI run completes': 'ciRun',
      'Context Pack REVIEW is generated': 'contextReview',
      'Backend verifier report is generated': 'backend',
      'Code Health scan is generated': 'codeHealth',
      'Permission Auditor is generated': 'permission',
      'AuthZ Matrix is generated': 'authz',
      'Transaction correlation is generated': 'transaction',
      'TypeORM DB analysis is generated': 'typeorm',
      'Queue and cache validation is generated': 'queueCache',
      'Queue reliability correlation is generated': 'queueReliability',
      'Route Guard Correlation is generated': 'routeGuard',
      'Review context calibration is generated': 'reviewContext',
      'Quality gate is generated': 'qualityGate',
      'Run manifest is generated': 'manifest',
      'Patch exports are generated': 'exports',
      'Context Pack export is generated': 'contextExport',
      'Learn site is generated': 'learn',
    };
    const suffix = conditions[value];
    return suffix ? t(`artifact.condition.${suffix}`) : value;
  }

  function render(target, run) {
    if (!target) return;
    const summary = (run && run.summary) || {};
    const groups = Array.isArray(run && run.artifact_groups) ? run.artifact_groups : [];
    const recommended = Array.isArray(run && run.recommended_artifacts) ? run.recommended_artifacts.slice(0, 4) : [];
    const missing = Array.isArray(run && run.missing_capabilities) ? run.missing_capabilities : [];
    const firstArtifact = recommended[0];
    const humanCount = summary.human_review_required_status === 'available'
      ? String(summary.human_review_required_count)
      : t('artifact.notGenerated');
    const warnings = warningRows(summary, firstArtifact);
    const groupMarkup = groups.map(group => `
      <details class="artifact-group" ${group.default_expanded ? 'open' : ''}>
        <summary>${escapeHtml(groupName(group))} <span>${t('artifact.availableCount', {count: group.artifacts.length})}</span></summary>
        <div class="artifact-grid">${group.artifacts.map(artifact => artifactCard(artifact, false)).join('')}</div>
      </details>`).join('');
    const recommendedMarkup = recommended.length
      ? `<div class="artifact-grid artifact-grid-primary">${recommended.map(artifact => artifactCard(artifact, true)).join('')}</div>`
      : `<p class="artifact-empty">${t('artifact.noPrimary')}</p>`;
    const missingMarkup = missing.length
      ? `<section class="artifact-missing"><h3>${t('artifact.missing')}</h3><div class="artifact-missing-grid">${missing.map(item => `<div><strong>${escapeHtml(groupName(item))}</strong><p>${escapeHtml(t('artifact.notGenerated'))}</p><small>${escapeHtml(t('artifact.generatedWhen', {conditions: (item.generated_when || []).map(localizedCondition).join('; ')}))}</small></div>`).join('')}</div></section>`
      : '';

    target.innerHTML = `
      <section class="artifact-cards" aria-label="${t('workbench.artifacts')}">
        <header class="artifact-status-header">
          <div><p class="artifact-kicker">${t('artifact.runStatus')}</p><h3>${t('artifact.reviewValidation')}</h3></div>
          <div class="artifact-status-grid">
            ${statusItem(t('metric.reviewDecision'), summary.review_decision || 'unknown')}
            ${statusItem(t('metric.evidence'), (summary.evidence_integrity || {}).status, (summary.evidence_integrity || {}).status === 'not_available' ? t('artifact.notGenerated') : t('common.errors', {count: (summary.evidence_integrity || {}).errors || 0}))}
            ${statusItem(t('metric.strict'), (summary.strict_verify || {}).status)}
            ${statusItem(t('metric.gate'), (summary.quality_gate || {}).status)}
            ${statusItem(t('artifact.validationStatus'), (summary.validation || {}).status)}
            ${statusItem(t('metric.humanReview'), summary.human_review_required_status === 'available' ? 'review' : 'not_available', humanCount)}
          </div>
        </header>
        ${warnings.length ? `<ul class="artifact-warnings">${warnings.join('')}</ul>` : ''}
        <section class="artifact-recommended"><div><p class="artifact-kicker">${t('artifact.recommendedFirst')}</p><h3>${t('artifact.recommendedTitle')}</h3></div>${recommendedMarkup}</section>
        <section class="artifact-groups"><h3>${t('artifact.categories')}</h3>${groupMarkup || `<p class="artifact-empty">${t('artifact.noCatalog')}</p>`}</section>
        ${missingMarkup}
      </section>`;
    target.querySelectorAll('.artifact-copy-path').forEach(button => {
      button.addEventListener('click', () => copyRelativePath(button));
    });
  }

  function copyRelativePath(button) {
    const value = button.dataset.relativePath || '';
    if (!value) return;
    const finish = () => {
      button.textContent = t('artifact.copied');
      window.setTimeout(() => { button.textContent = t('artifact.copyPath'); }, 1200);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(value).then(finish).catch(() => fallbackCopy(value, finish));
      return;
    }
    fallbackCopy(value, finish);
  }

  function fallbackCopy(value, onCopied) {
    const input = document.createElement('textarea');
    input.value = value;
    input.setAttribute('readonly', '');
    input.style.position = 'fixed';
    input.style.opacity = '0';
    document.body.appendChild(input);
    input.select();
    try {
      document.execCommand('copy');
      onCopied();
    } finally {
      document.body.removeChild(input);
    }
  }

  window.StudioArtifactCards = {render, localizedArtifact};
}());
