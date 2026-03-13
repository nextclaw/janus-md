// ── Janus-MD Minimal JS ──
(function () {
  'use strict';

  // ── Theme toggle ──────────────────────────────────────────────────────────
  const STORAGE_KEY = 'janus.theme';
  const btn = document.getElementById('themeToggle');

  function getPreferred() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
  }

  applyTheme(getPreferred());

  if (btn) {
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  // Follow system preference changes (only when no explicit user choice stored)
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      applyTheme(e.matches ? 'dark' : 'light');
    }
  });
})();
