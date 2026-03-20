// ── Janus-MD Site JS ──
(function () {
  'use strict';

  const MATHJAX_SRC = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
  const STORAGE_KEY = 'janus.theme';
  let mathJaxPromise = null;

  const themeToggle = document.getElementById('themeToggle');

  function getPreferredTheme() {
    const savedTheme = localStorage.getItem(STORAGE_KEY);
    if (savedTheme) return savedTheme;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    if (themeToggle) {
      themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
  }

  function containerHasMath(container) {
    return Boolean(container && container.querySelector('.arithmatex'));
  }

  function ensureMathJax() {
    if (window.MathJax && typeof window.MathJax.typesetPromise === 'function') {
      return Promise.resolve(window.MathJax);
    }

    if (mathJaxPromise) {
      return mathJaxPromise;
    }

    window.MathJax = window.MathJax || {
      tex: {
        inlineMath: [['\\(', '\\)'], ['$', '$']],
        displayMath: [['\\[', '\\]'], ['$$', '$$']],
        processEscapes: true,
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
      },
      startup: {
        typeset: false,
      },
    };

    mathJaxPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[src="${MATHJAX_SRC}"]`);
      if (existing) {
        existing.addEventListener('load', () => resolve(window.MathJax), { once: true });
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      const script = document.createElement('script');
      script.src = MATHJAX_SRC;
      script.async = true;
      script.addEventListener('load', () => {
        const startupPromise = window.MathJax && window.MathJax.startup && window.MathJax.startup.promise;
        if (startupPromise) {
          startupPromise.then(() => resolve(window.MathJax), reject);
          return;
        }
        resolve(window.MathJax);
      }, { once: true });
      script.addEventListener('error', reject, { once: true });
      document.head.appendChild(script);
    }).catch((error) => {
      console.warn('[janus] MathJax failed to load:', error);
      mathJaxPromise = null;
      throw error;
    });

    return mathJaxPromise;
  }

  async function renderMathInContainer(container) {
    if (!containerHasMath(container)) {
      return;
    }

    const mathJax = await ensureMathJax();
    if (typeof mathJax.typesetClear === 'function') {
      mathJax.typesetClear([container]);
    }
    await mathJax.typesetPromise([container]);
  }

  applyTheme(getPreferredTheme());

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
    });
  }

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (event) => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      applyTheme(event.matches ? 'dark' : 'light');
    }
  });

  window.JanusSite = Object.assign(window.JanusSite || {}, {
    renderMathInContainer,
  });

  var mainContent = document.querySelector('.prose') || document.querySelector('.site-main');
  if (mainContent) renderMathInContainer(mainContent).catch(function () {});
})();
