(function () {
  'use strict';

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function statusLabel(status) {
    const labels = {
      pass: 'passed',
      warn: 'needs attention',
      fail: 'failed',
      review: 'human review required',
      block: 'blocked',
      needs_review: 'needs review',
      not_available: 'not generated',
      unknown: 'unknown'
    };
    return labels[String(status || 'unknown').toLowerCase()] || String(status || 'unknown');
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

  function artifactCard(artifact, compact) {
    const open = artifact.available && artifact.url
      ? `<a class="artifact-open" href="${escapeHtml(artifact.url)}" target="_blank" rel="noopener">Open</a>`
      : '<span class="artifact-unavailable">Not generated</span>';
    return `
      <article class="artifact-card ${compact ? 'artifact-card-compact' : ''}">
        <div class="artifact-card-heading">
          <h4>${escapeHtml(artifact.display_name)}</h4>
          <span class="artifact-format">${escapeHtml(artifact.format)}</span>
        </div>
        <p>${escapeHtml(artifact.description)}</p>
        <dl class="artifact-meta">
          <div><dt>Audience</dt><dd>${escapeHtml(artifact.audience)}</dd></div>
          <div><dt>Priority</dt><dd>${escapeHtml(artifact.priority)}</dd></div>
        </dl>
        <div class="artifact-action">${escapeHtml(artifact.recommended_action)}</div>
        <div class="artifact-card-actions">
          ${open}
          <button type="button" class="artifact-copy-path" data-relative-path="${escapeHtml(artifact.relative_path)}">Copy relative path</button>
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
      ? `<a href="${escapeHtml(recommended.url)}" target="_blank" rel="noopener">Open ${escapeHtml(recommended.display_name)}</a>.`
      : 'Open a generated validation or review artifact before relying on downstream items.';
    if (evidence.status === 'fail' || evidence.status === 'warn') {
      rows.push(`<li><strong>Evidence integrity ${escapeHtml(statusLabel(evidence.status))}.</strong> ${recommendation}</li>`);
    }
    if (strict.status === 'fail') {
      rows.push(`<li><strong>Strict verification failed.</strong> ${recommendation}</li>`);
    }
    if (gate.status === 'fail' || gate.status === 'warn') {
      rows.push(`<li><strong>Quality Gate ${escapeHtml(statusLabel(gate.status))}.</strong> ${escapeHtml((gate.reasons || [])[0] || 'Review the gate artifact for the observed reason.')}</li>`);
    }
    if (validation.status === 'needs_review' || validation.status === 'fail') {
      rows.push(`<li><strong>Validation ${escapeHtml(statusLabel(validation.status))}.</strong> ${recommendation}</li>`);
    }
    if (decision === 'review' || decision === 'block') {
      rows.push(`<li><strong>Repository Review is ${escapeHtml(decision.toUpperCase())}.</strong> ${recommendation}</li>`);
    }
    (summary.warnings || []).forEach((warning) => {
      rows.push(`<li><strong>Artifact parse warning.</strong> ${escapeHtml(warning)}</li>`);
    });
    if (rows.length === 0 && evidence.status === 'pass' && strict.status === 'pass') {
      rows.push('<li><strong>Evidence integrity and strict verification passed for generated artifacts.</strong> This is not a safety or correctness proof.</li>');
    }
    return rows;
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
      : 'not generated';
    const warnings = warningRows(summary, firstArtifact);
    const groupMarkup = groups.map((group) => `
      <details class="artifact-group" ${group.default_expanded ? 'open' : ''}>
        <summary>${escapeHtml(group.display_name)} <span>${group.artifacts.length} available</span></summary>
        <div class="artifact-grid">${group.artifacts.map((artifact) => artifactCard(artifact, false)).join('')}</div>
      </details>`).join('');
    const recommendedMarkup = recommended.length
      ? `<div class="artifact-grid artifact-grid-primary">${recommended.map((artifact) => artifactCard(artifact, true)).join('')}</div>`
      : '<p class="artifact-empty">No primary review artifact was generated for this run.</p>';
    const missingMarkup = missing.length
      ? `<section class="artifact-missing"><h3>Missing / Not Generated</h3><div class="artifact-missing-grid">${missing.map((item) => `<div><strong>${escapeHtml(item.display_name)}</strong><p>${escapeHtml(item.message)}</p><small>Generated when: ${escapeHtml((item.generated_when || []).join('; '))}</small></div>`).join('')}</div></section>`
      : '';

    target.innerHTML = `
      <section class="artifact-cards" aria-label="Run artifact cards">
        <header class="artifact-status-header">
          <div><p class="artifact-kicker">Run status</p><h3>Review and validation</h3></div>
          <div class="artifact-status-grid">
            ${statusItem('Review Decision', summary.review_decision || 'unknown')}
            ${statusItem('Evidence Integrity', (summary.evidence_integrity || {}).status, (summary.evidence_integrity || {}).status === 'not_available' ? 'not generated' : `${(summary.evidence_integrity || {}).errors || 0} errors`)}
            ${statusItem('Strict Verify', (summary.strict_verify || {}).status)}
            ${statusItem('Quality Gate', (summary.quality_gate || {}).status)}
            ${statusItem('Validation Status', (summary.validation || {}).status)}
            ${statusItem('Human Review Required', summary.human_review_required_status === 'available' ? 'review' : 'not_available', humanCount)}
          </div>
        </header>
        ${warnings.length ? `<ul class="artifact-warnings">${warnings.join('')}</ul>` : ''}
        <section class="artifact-recommended"><div><p class="artifact-kicker">Recommended First</p><h3>Open the most useful generated artifacts first</h3></div>${recommendedMarkup}</section>
        <section class="artifact-groups"><h3>Artifact categories</h3>${groupMarkup || '<p class="artifact-empty">No cataloged artifacts are available for this run yet.</p>'}</section>
        ${missingMarkup}
      </section>`;
    target.querySelectorAll('.artifact-copy-path').forEach((button) => {
      button.addEventListener('click', () => copyRelativePath(button));
    });
  }

  function copyRelativePath(button) {
    const value = button.dataset.relativePath || '';
    if (!value) return;
    const finish = () => {
      const original = button.textContent;
      button.textContent = 'Copied';
      window.setTimeout(() => { button.textContent = original; }, 1200);
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

  window.StudioArtifactCards = { render };
}());
