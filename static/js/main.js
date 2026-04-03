// ── Janus-MD Site JS ──
(function () {
  'use strict';

  var STORAGE_KEY = 'janus.theme';

  var themeToggle = document.getElementById('themeToggle');

  function getPreferredTheme() {
    var savedTheme = localStorage.getItem(STORAGE_KEY);
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

  applyTheme(getPreferredTheme());

  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var currentTheme = document.documentElement.getAttribute('data-theme');
      applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
    });
  }

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (event) {
    if (!localStorage.getItem(STORAGE_KEY)) {
      applyTheme(event.matches ? 'dark' : 'light');
    }
  });

  // ── MathJax helper for Explorer dynamic loading ──
  var MATHJAX_SRC = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
  var mathJaxPromise = null;

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

    mathJaxPromise = new Promise(function (resolve, reject) {
      var existing = document.querySelector('script[src="' + MATHJAX_SRC + '"]');
      if (existing) {
        existing.addEventListener('load', function () { resolve(window.MathJax); }, { once: true });
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      var script = document.createElement('script');
      script.src = MATHJAX_SRC;
      script.async = true;
      script.addEventListener('load', function () {
        var startupPromise = window.MathJax && window.MathJax.startup && window.MathJax.startup.promise;
        if (startupPromise) {
          startupPromise.then(function () { resolve(window.MathJax); }, reject);
          return;
        }
        resolve(window.MathJax);
      }, { once: true });
      script.addEventListener('error', reject, { once: true });
      document.head.appendChild(script);
    }).catch(function (error) {
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

    var mathJax = await ensureMathJax();
    if (typeof mathJax.typesetClear === 'function') {
      mathJax.typesetClear([container]);
    }
    await mathJax.typesetPromise([container]);
  }

  window.JanusSite = Object.assign(window.JanusSite || {}, {
    renderMathInContainer: renderMathInContainer,
  });

  // ── TOC Sidebar: Scroll tracking + mobile toggle ──
  var tocSidebar = document.getElementById('tocSidebar');
  var tocToggle = document.getElementById('tocToggle');
  var tocClose = document.getElementById('tocClose');

  if (tocSidebar && tocToggle) {
    // Mobile toggle
    tocToggle.addEventListener('click', function () {
      tocSidebar.classList.toggle('toc-open');
    });

    if (tocClose) {
      tocClose.addEventListener('click', function () {
        tocSidebar.classList.remove('toc-open');
      });
    }

    // Close on outside click (mobile)
    document.addEventListener('click', function (e) {
      if (tocSidebar.classList.contains('toc-open') &&
          !tocSidebar.contains(e.target) &&
          e.target !== tocToggle) {
        tocSidebar.classList.remove('toc-open');
      }
    });

    // ── IntersectionObserver for scroll tracking ──
    var tocLinks = tocSidebar.querySelectorAll('.toc-nav a[href^="#"]');
    if (tocLinks.length > 0) {
      var headingIds = [];
      tocLinks.forEach(function (link) {
        var id = link.getAttribute('href').slice(1);
        if (id) headingIds.push(id);
      });

      var currentActive = null;

      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var id = entry.target.id;
            if (currentActive) {
              currentActive.classList.remove('toc-active');
            }
            var link = tocSidebar.querySelector('.toc-nav a[href="#' + CSS.escape(id) + '"]');
            if (link) {
              link.classList.add('toc-active');
              currentActive = link;
              // Scroll TOC sidebar to keep active item visible
              var sidebarRect = tocSidebar.getBoundingClientRect();
              var linkRect = link.getBoundingClientRect();
              if (linkRect.top < sidebarRect.top || linkRect.bottom > sidebarRect.bottom) {
                link.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
              }
            }
          }
        });
      }, {
        rootMargin: '-80px 0px -60% 0px',
        threshold: 0,
      });

      headingIds.forEach(function (id) {
        var el = document.getElementById(id);
        if (el) observer.observe(el);
      });
    }
  }
})();
