(function () {
  'use strict';

  const STORAGE_KEY = 'reposense.studio.locale';
  const SUPPORTED = Object.freeze(['zh-CN', 'en-US']);
  const subscribers = new Set();
  let locale = 'en-US';

  function normalizeLocale(value) {
    if (SUPPORTED.includes(value)) return value;
    return String(value || '').toLowerCase().startsWith('zh') ? 'zh-CN' : 'en-US';
  }

  function readInitialLocale() {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (SUPPORTED.includes(stored)) return stored;
    } catch (error) {
      // Storage can be disabled; navigator fallback remains deterministic.
    }
    try {
      return normalizeLocale(window.navigator.language);
    } catch (error) {
      return 'en-US';
    }
  }

  function interpolate(value, params) {
    return String(value).replace(/\{([A-Za-z0-9_]+)\}/g, (match, key) => (
      Object.prototype.hasOwnProperty.call(params || {}, key) ? String(params[key]) : match
    ));
  }

  function t(key, params) {
    const catalogs = window.RepoSenseStudioLocales || {};
    const active = catalogs[locale] || {};
    const english = catalogs['en-US'] || {};
    const value = active[key] == null ? english[key] : active[key];
    if (value == null) {
      if (['localhost', '127.0.0.1'].includes(window.location.hostname)) {
        console.warn(`[RepoSense Studio i18n] Missing translation: ${key}`);
      }
      return key;
    }
    return interpolate(value, params);
  }

  function setLocale(nextLocale) {
    const normalized = SUPPORTED.includes(nextLocale) ? nextLocale : 'en-US';
    locale = normalized;
    document.documentElement.lang = normalized;
    try { window.localStorage.setItem(STORAGE_KEY, normalized); } catch (error) { /* no-op */ }
    subscribers.forEach(handler => handler(normalized));
    return normalized;
  }

  function getLocale() {
    return locale;
  }

  function subscribeLocaleChange(handler) {
    subscribers.add(handler);
    return () => subscribers.delete(handler);
  }

  function formatStatus(value) {
    const status = String(value || 'unknown').toLowerCase();
    return t(`status.${status}`);
  }

  function formatCount(value, key) {
    return t(key, {count: Number(value || 0)});
  }

  function translateDocument(root) {
    (root || document).querySelectorAll('[data-i18n]').forEach(node => {
      node.textContent = t(node.dataset.i18n);
    });
    (root || document).querySelectorAll('[data-i18n-aria]').forEach(node => {
      node.setAttribute('aria-label', t(node.dataset.i18nAria));
    });
    (root || document).querySelectorAll('[data-i18n-placeholder]').forEach(node => {
      node.setAttribute('placeholder', t(node.dataset.i18nPlaceholder));
    });
  }

  function mountLanguageSwitcher(target) {
    if (!target) return;
    target.innerHTML = `<div class="language-switcher" role="group" aria-label="${t('language.label')}">
      <button type="button" data-locale="zh-CN">${t('language.chinese')}</button>
      <button type="button" data-locale="en-US">${t('language.english')}</button>
    </div>`;
    const update = () => {
      const group = target.querySelector('.language-switcher');
      if (group) group.setAttribute('aria-label', t('language.label'));
      target.querySelectorAll('[data-locale]').forEach(button => {
        const selected = button.dataset.locale === locale;
        button.classList.toggle('active', selected);
        button.setAttribute('aria-pressed', String(selected));
      });
    };
    target.querySelectorAll('[data-locale]').forEach(button => {
      button.addEventListener('click', () => setLocale(button.dataset.locale));
    });
    subscribeLocaleChange(update);
    update();
  }

  function initI18n() {
    locale = readInitialLocale();
    document.documentElement.lang = locale;
    translateDocument(document);
    return locale;
  }

  window.StudioI18n = {
    STORAGE_KEY,
    SUPPORTED,
    initI18n,
    setLocale,
    getLocale,
    t,
    subscribeLocaleChange,
    formatStatus,
    formatCount,
    translateDocument,
    mountLanguageSwitcher,
  };
}());
