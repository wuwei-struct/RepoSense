(function () {
  'use strict';

  const formState = {
    sourceMode: 'zip',
    selectedProfile: 'full_review',
    profiles: null,
    localPath: '',
    selectedFile: null,
  };

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  function t(key, params) {
    return window.StudioI18n.t(key, params);
  }

  async function jsonRequest(url, options) {
    const response = await fetch(new URL(url, window.location.origin).toString(), options);
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.message || `HTTP ${response.status}`);
    return body;
  }

  function profileText(profile, field) {
    return t(`profile.${profile.profile_id}.${field}`) || profile[field];
  }

  function outputLabel(value) {
    const labels = {
      'Repository Review': 'Repository Review',
      'Human Review Required': t('workbench.human'),
      'Code Health': t('workbench.health'),
      'Permission and AuthZ': t('workbench.permission'),
      'Context Pack REVIEW': 'Context Pack REVIEW',
      'Validation outputs': t('workbench.validation'),
      'Main HTML Report': 'Main HTML Report',
      'API and event graph facts': t('workbench.architecture'),
      'Context Pack': 'Context Pack',
    };
    return labels[value] || value;
  }

  function profileCard(profile) {
    const capabilities = profile.capabilities || {};
    const tags = [
      capabilities.permission_review ? t('profile.permission') : t('profile.noPermission'),
      capabilities.code_health ? t('profile.codeHealth') : t('profile.coreFacts'),
      capabilities.context_pack ? t('profile.contextPack') : '',
      capabilities.strict_verify ? t('profile.strictVerify') : '',
    ].filter(Boolean);
    const outputs = (profile.generated_outputs || []).map(outputLabel).join(', ');
    return `
      <article class="profile-option ${profile.profile_id === formState.selectedProfile ? 'selected' : ''}" data-profile-id="${escapeHtml(profile.profile_id)}" tabindex="0">
        <header><h3>${escapeHtml(profileText(profile, 'name'))}</h3>${profile.recommended ? `<span class="status-pill pass">${t('analyze.recommended')}</span>` : ''}</header>
        <p>${escapeHtml(profileText(profile, 'description'))}</p>
        <div class="profile-features">${tags.map(tag => `<span>${escapeHtml(tag)}</span>`).join('')}</div>
        <small>${escapeHtml(t('analyze.generates', {outputs}))}</small>
      </article>`;
  }

  async function loadProfiles() {
    if (formState.profiles) return formState.profiles;
    const payload = await jsonRequest('/api/studio/profiles');
    formState.profiles = Array.isArray(payload.profiles) ? payload.profiles : [];
    formState.selectedProfile = formState.selectedProfile || payload.default_profile_id || 'full_review';
    return formState.profiles;
  }

  async function mount(target, options) {
    const config = options || {};
    target.innerHTML = `<div class="loading-panel">${t('analyze.loadingProfiles')}</div>`;
    let profiles;
    try {
      profiles = await loadProfiles();
    } catch (error) {
      target.innerHTML = `<div class="empty-panel">${escapeHtml(t('analyze.profilesFailed', {message: error.message}))}</div>`;
      return;
    }

    target.innerHTML = `
      <div class="section-heading"><div><span class="eyebrow">${t('analyze.kicker')}</span><h2>${t('analyze.title')}</h2></div></div>
      <div class="analyze-layout">
        <section class="analyze-panel">
          <div class="source-switch">
            <button type="button" data-source="zip">${t('analyze.uploadZip')}</button>
            <button type="button" data-source="local">${t('analyze.localPath')}</button>
          </div>
          <div id="source-zip">
            <div class="dropzone" id="studio-dropzone">
              <p class="run-profile">${t('analyze.source')}</p>
              <h3>${t('analyze.dropZip')}</h3>
              <p>${t('analyze.archiveBoundary')}</p>
              <input type="file" id="studio-file" accept=".zip">
              <button type="button" class="studio-button" id="choose-zip">${t('analyze.chooseZip')}</button>
              <div id="selected-zip" class="form-message">${escapeHtml((formState.selectedFile || {}).name || '')}</div>
            </div>
          </div>
          <div id="source-local" hidden>
            <label class="field-label" for="studio-local-path">${t('analyze.localPathLabel')}</label>
            <input class="text-field" id="studio-local-path" type="text" value="${escapeHtml(formState.localPath)}" placeholder="${escapeHtml(t('analyze.localPathPlaceholder'))}">
            <p>${t('analyze.staticBoundary')}</p>
          </div>
          <div id="analysis-message" class="form-message" role="status"></div>
          <button type="button" class="studio-button primary" id="start-analysis">${t('analyze.start')}</button>
        </section>
        <section class="analyze-panel">
          <span class="run-profile">${t('analyze.profile')}</span>
          <h2>${t('analyze.chooseDepth')}</h2>
          <p>${t('analyze.depthDescription')}</p>
          <div class="profile-list" id="profile-list">${profiles.map(profileCard).join('')}</div>
          <p class="state-note">${t('analyze.profileBoundary')}</p>
        </section>
      </div>`;

    const fileInput = target.querySelector('#studio-file');
    const dropzone = target.querySelector('#studio-dropzone');
    const message = target.querySelector('#analysis-message');
    const localPathInput = target.querySelector('#studio-local-path');

    function selectSource(mode) {
      formState.sourceMode = mode;
      target.querySelectorAll('[data-source]').forEach(button => button.classList.toggle('active', button.dataset.source === mode));
      target.querySelector('#source-zip').hidden = mode !== 'zip';
      target.querySelector('#source-local').hidden = mode !== 'local';
      message.textContent = '';
    }

    target.querySelectorAll('[data-source]').forEach(button => button.addEventListener('click', () => selectSource(button.dataset.source)));
    target.querySelector('#choose-zip').addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      formState.selectedFile = fileInput.files.length ? fileInput.files[0] : null;
      target.querySelector('#selected-zip').textContent = (formState.selectedFile || {}).name || '';
    });
    localPathInput.addEventListener('input', () => { formState.localPath = localPathInput.value; });
    ['dragenter', 'dragover'].forEach(name => dropzone.addEventListener(name, event => {
      event.preventDefault(); dropzone.classList.add('dragover');
    }));
    ['dragleave', 'drop'].forEach(name => dropzone.addEventListener(name, event => {
      event.preventDefault(); dropzone.classList.remove('dragover');
    }));
    dropzone.addEventListener('drop', event => {
      if (event.dataTransfer.files.length) {
        formState.selectedFile = event.dataTransfer.files[0];
        target.querySelector('#selected-zip').textContent = formState.selectedFile.name;
      }
    });
    target.querySelectorAll('.profile-option').forEach(card => {
      const choose = () => {
        formState.selectedProfile = card.dataset.profileId;
        target.querySelectorAll('.profile-option').forEach(item => item.classList.toggle('selected', item === card));
      };
      card.addEventListener('click', choose);
      card.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') choose(); });
    });

    target.querySelector('#start-analysis').addEventListener('click', async event => {
      const button = event.currentTarget;
      button.disabled = true;
      message.textContent = t('analyze.preparing');
      try {
        let project;
        if (formState.sourceMode === 'zip') {
          if (!formState.selectedFile) throw new Error(t('analyze.chooseZipFirst'));
          const form = new FormData();
          form.append('file', formState.selectedFile);
          project = await jsonRequest('/api/projects/import-zip', {method: 'POST', body: form});
        } else {
          const repoPath = localPathInput.value.trim();
          formState.localPath = repoPath;
          if (!repoPath) throw new Error(t('analyze.pathRequired'));
          project = await jsonRequest('/api/projects/import-path', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({repo_path: repoPath}),
          });
        }
        message.textContent = t('analyze.starting');
        const run = await jsonRequest('/api/runs', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({project_id: project.project_id, profile_id: formState.selectedProfile}),
        });
        if (typeof config.onRunCreated === 'function') config.onRunCreated(run.run_id);
      } catch (error) {
        message.textContent = error.message;
        button.disabled = false;
      }
    });
    selectSource(formState.sourceMode);
  }

  window.StudioAnalyzeForm = {mount, state: formState};
}());
