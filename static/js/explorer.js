// ── Janus-MD Explorer View (Split-Pane, Fetch) ──
(function () {
  'use strict';

  var tree = window.__JANUS_TREE__;
  var root = document.getElementById('explorer-root');
  var contentPane = document.getElementById('explorer-content');
  var welcome = document.getElementById('explorer-welcome');
  if (!tree || !root || !contentPane) return;

  var activeLink = null;

  /**
   * Load an article into the right pane via fetch.
   */
  function loadArticle(slug, linkEl) {
    // Update active highlight immediately
    if (activeLink) activeLink.classList.remove('active');
    linkEl.classList.add('active');
    activeLink = linkEl;

    // Show loading state
    contentPane.innerHTML = '<div class="explorer-loading"><span>⏳</span></div>';

    fetch('/' + slug + '/')
      .then(function (res) { return res.text(); })
      .then(function (html) {
        // Parse the fetched HTML and extract the <main> content
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var main = doc.querySelector('.site-main');
        if (main) {
          contentPane.innerHTML = main.innerHTML;
        } else {
          contentPane.innerHTML = '<div class="explorer-error"><p>Failed to load article.</p></div>';
        }
        // Re-run any inline scripts (e.g. MathJax) in the loaded content
        contentPane.querySelectorAll('script').forEach(function (old) {
          var s = document.createElement('script');
          if (old.src) { s.src = old.src; } else { s.textContent = old.textContent; }
          old.replaceWith(s);
        });
      })
      .catch(function () {
        contentPane.innerHTML = '<div class="explorer-error"><p>Failed to load article.</p></div>';
      });
  }

  /**
   * Count total leaf (article) nodes in a subtree.
   */
  function countLeaves(node) {
    if (node.slug) return 1;
    if (!node.children) return 0;
    return node.children.reduce(function (s, c) { return s + countLeaves(c); }, 0);
  }

  /**
   * Sort children: folders first (alphabetical), then files (by date desc, then name).
   */
  function sortChildren(children) {
    return children.slice().sort(function (a, b) {
      var aIsFolder = !a.slug;
      var bIsFolder = !b.slug;
      if (aIsFolder !== bIsFolder) return aIsFolder ? -1 : 1;
      if (aIsFolder) return a.name.localeCompare(b.name);
      if (a.date && b.date && a.date !== b.date) return a.date > b.date ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
  }

  /**
   * Build DOM nodes for a single tree node.
   */
  function renderNode(node) {
    var li = document.createElement('li');

    // Leaf node → article link (click loads via fetch)
    if (node.slug) {
      var a = document.createElement('a');
      a.className = 'explorer-file';
      a.setAttribute('data-slug', node.slug);
      a.href = '/' + node.slug;
      a.innerHTML =
        '<span class="file-icon">📄</span>' +
        '<span class="file-title">' + escapeHtml(node.title || node.name) + '</span>' +
        (node.date ? '<span class="file-date">' + escapeHtml(node.date) + '</span>' : '');

      a.addEventListener('click', function (e) {
        e.preventDefault();
        loadArticle(node.slug, a);
      });

      li.appendChild(a);
      return li;
    }

    // Folder node
    var count = countLeaves(node);
    var folder = document.createElement('div');
    folder.className = 'explorer-folder';
    folder.setAttribute('role', 'button');
    folder.setAttribute('aria-expanded', 'false');
    folder.innerHTML =
      '<span class="folder-icon">📁</span>' +
      '<span class="folder-name">' + escapeHtml(node.name) + '</span>' +
      '<span class="folder-count">' + count + '</span>';

    var childrenContainer = document.createElement('div');
    childrenContainer.className = 'explorer-children';

    if (node.children && node.children.length) {
      var ul = document.createElement('ul');
      sortChildren(node.children).forEach(function (child) {
        ul.appendChild(renderNode(child));
      });
      childrenContainer.appendChild(ul);
    }

    folder.addEventListener('click', function () {
      var expanded = folder.getAttribute('aria-expanded') === 'true';
      folder.setAttribute('aria-expanded', String(!expanded));
      childrenContainer.classList.toggle('open', !expanded);
    });

    li.appendChild(folder);
    li.appendChild(childrenContainer);
    return li;
  }

  /**
   * Minimal HTML escaper.
   */
  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ── Render ──
  if (!tree.children || tree.children.length === 0) {
    root.innerHTML = '<div class="explorer-empty"><p>No articles found.</p></div>';
    return;
  }

  var ul = document.createElement('ul');
  sortChildren(tree.children).forEach(function (child) {
    ul.appendChild(renderNode(child));
  });
  root.appendChild(ul);

  // Auto-expand all top-level folders
  var topFolders = root.querySelectorAll(':scope > ul > li > .explorer-folder');
  topFolders.forEach(function (f) {
    f.setAttribute('aria-expanded', 'true');
    var children = f.nextElementSibling;
    if (children) children.classList.add('open');
  });
})();
