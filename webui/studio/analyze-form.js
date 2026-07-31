(function () {
  'use strict';

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  async function jsonRequest(url, options) {
    const response = await fetch(new URL(url, window.location.origin).toString(), options);
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.message || `HTTP ${response.status}`);
    return body;
  }

  function profileCard(profile, selectedId) {
    const capabilities = profile.capabilities || {};
    const tags = [
      capabilities.permission_review ? 'Permission review' : 'No permission pass',
      capabilities.code_health ? 'Code Health' : 'Core facts only',
      capabilities.context_pack ? 'Context Pack' : '',
      capabilities.strict_verify ? 'Strict Verify' : '',
    ].filter(Boolean);
    return `
      <article class="profile-option ${profile.profile_id === selectedId ? 'selected' : ''}" data-profile-id="${escapeHtml(profile.profile_id)}" tabindex="0">
        <header><h3>${escapeHtml(profile.display_name)}</h3>${profile.recommended ? '<span class="status-pill pass">Recommended</span>' : ''}</header>
        <p>${escapeHtml(profile.description)}</p>
        <div class="profile-features">${tags.map(tag => `<span>${escapeHtml(tag)}</span>`).join('')}</div>
        <small>Generates: ${escapeHtml((profile.generated_outputs || []).join(', '))}</small>
      </article>`;
  }

  async function mount(target, options) {
    const config = options || {};
    let sourceMode = 'zip';
    let selectedProfile = 'full_review';
    let profiles = [];
    target.innerHTML = '<div class="loading-panel">Loading analysis profiles...</div>';
    try {
      const payload = await jsonRequest('/api/studio/profiles');
      profiles = Array.isArray(payload.profiles) ? payload.profiles : [];
      selectedProfile = payload.default_profile_id || 'full_review';
    } catch (error) {
      target.innerHTML = `<div class="empty-panel">Analysis profiles could not be loaded: ${escapeHtml(error.message)}</div>`;
      return;
    }

    target.innerHTML = `
      <div class="section-heading"><div><span class="eyebrow">Start a grounded review</span><h2>Analyze Repository</h2></div></div>
      <div class="analyze-layout">
        <section class="analyze-panel">
          <div class="source-switch">
            <button type="button" data-source="zip" class="active">Upload ZIP</button>
            <button type="button" data-source="local">Use Local Path</button>
          </div>
          <div id="source-zip">
            <div class="dropzone" id="studio-dropzone">
              <p class="run-profile">Repository source</p>
              <h3>Drop a repository ZIP here</h3>
              <p>Archive contents stay in the local Studio workspace.</p>
              <input type="file" id="studio-file" accept=".zip">
              <button type="button" class="studio-button" id="choose-zip">Choose ZIP</button>
              <div id="selected-zip" class="form-message"></div>
            </div>
          </div>
          <div id="source-local" hidden>
            <label class="field-label" for="studio-local-path">Local repository path</label>
            <input class="text-field" id="studio-local-path" type="text" placeholder="Choose a repository path on this machine">
            <p>RepoSense statically reads this directory. It does not execute repository code.</p>
          </div>
          <div id="analysis-message" class="form-message" role="status"></div>
          <button type="button" class="studio-button primary" id="start-analysis">Start analysis</button>
        </section>
        <section class="analyze-panel">
          <span class="run-profile">Analysis profile</span>
          <h2>Choose review depth</h2>
          <p>Full Review is recommended for evidence-backed repository review. Quick Scan keeps a smaller output surface.</p>
          <div class="profile-list" id="profile-list">${profiles.map(p => profileCard(p, selectedProfile)).join('')}</div>
          <p class="state-note">Profiles control generated review artifacts, not repository execution. Missing evidence remains unknown rather than being treated as safe.</p>
        </section>
      </div>`;

    const fileInput = target.querySelector('#studio-file');
    const dropzone = target.querySelector('#studio-dropzone');
    const message = target.querySelector('#analysis-message');

    function selectSource(mode) {
      sourceMode = mode;
      target.querySelectorAll('[data-source]').forEach(button => button.classList.toggle('active', button.dataset.source === mode));
      target.querySelector('#source-zip').hidden = mode !== 'zip';
      target.querySelector('#source-local').hidden = mode !== 'local';
      message.textContent = '';
    }

    target.querySelectorAll('[data-source]').forEach(button => button.addEventListener('click', () => selectSource(button.dataset.source)));
    target.querySelector('#choose-zip').addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      target.querySelector('#selected-zip').textContent = fileInput.files.length ? fileInput.files[0].name : '';
    });
    ['dragenter', 'dragover'].forEach(name => dropzone.addEventListener(name, event => {
      event.preventDefault(); dropzone.classList.add('dragover');
    }));
    ['dragleave', 'drop'].forEach(name => dropzone.addEventListener(name, event => {
      event.preventDefault(); dropzone.classList.remove('dragover');
    }));
    dropzone.addEventListener('drop', event => {
      if (event.dataTransfer.files.length) {
        fileInput.files = event.dataTransfer.files;
        target.querySelector('#selected-zip').textContent = event.dataTransfer.files[0].name;
      }
    });
    target.querySelectorAll('.profile-option').forEach(card => {
      const choose = () => {
        selectedProfile = card.dataset.profileId;
        target.querySelectorAll('.profile-option').forEach(item => item.classList.toggle('selected', item === card));
      };
      card.addEventListener('click', choose);
      card.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') choose(); });
    });

    target.querySelector('#start-analysis').addEventListener('click', async event => {
      const button = event.currentTarget;
      button.disabled = true;
      message.textContent = 'Preparing repository source...';
      try {
        let project;
        if (sourceMode === 'zip') {
          if (!fileInput.files.length) throw new Error('Choose a repository ZIP first.');
          const form = new FormData();
          form.append('file', fileInput.files[0]);
          project = await jsonRequest('/api/projects/import-zip', {method: 'POST', body: form});
        } else {
          const repoPath = target.querySelector('#studio-local-path').value.trim();
          if (!repoPath) throw new Error('Local repository path is required.');
          project = await jsonRequest('/api/projects/import-path', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({repo_path: repoPath}),
          });
        }
        message.textContent = 'Starting review pipeline...';
        const run = await jsonRequest('/api/runs', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({project_id: project.project_id, profile_id: selectedProfile}),
        });
        if (typeof config.onRunCreated === 'function') config.onRunCreated(run.run_id);
      } catch (error) {
        message.textContent = error.message;
        button.disabled = false;
      }
    });
  }

  window.StudioAnalyzeForm = {mount};
}());
