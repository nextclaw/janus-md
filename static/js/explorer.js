(function () {
  'use strict';

  const tree = window.__JANUS_EXPLORER_TREE__;
  const root = document.getElementById('explorer-root');
  const contentPane = document.getElementById('explorer-content');

  if (!tree || !root || !contentPane) {
    return;
  }

  let activeLink = null;

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function countLeaves(node) {
    if (node.slug) {
      return 1;
    }
    return (node.children || []).reduce((sum, child) => sum + countLeaves(child), 0);
  }

  function sortChildren(children) {
    return children.slice().sort((a, b) => {
      const aIsFolder = !a.slug;
      const bIsFolder = !b.slug;
      if (aIsFolder !== bIsFolder) {
        return aIsFolder ? -1 : 1;
      }
      if (aIsFolder) {
        return a.name.localeCompare(b.name);
      }
      if (a.date && b.date && a.date !== b.date) {
        return a.date > b.date ? -1 : 1;
      }
      return (a.title || a.name).localeCompare(b.title || b.name);
    });
  }

  function setActive(linkEl) {
    if (activeLink) {
      activeLink.classList.remove('active');
    }
    activeLink = linkEl;
    if (activeLink) {
      activeLink.classList.add('active');
    }
  }

  function renderMath(container) {
    if (window.JanusSite && typeof window.JanusSite.renderMathInContainer === 'function') {
      return window.JanusSite.renderMathInContainer(container);
    }
    return Promise.resolve();
  }

  async function loadArticle(slug, linkEl) {
    setActive(linkEl);
    contentPane.innerHTML = '<div class="explorer-loading"><span>⏳</span><p>Loading article...</p></div>';

    try {
      const response = await fetch(`/${slug}/`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const html = await response.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const main = doc.querySelector('.site-main');
      if (!main) {
        throw new Error('Missing .site-main in fetched article');
      }

      contentPane.innerHTML = main.innerHTML;
      contentPane.scrollTop = 0;
      await renderMath(contentPane);
    } catch (error) {
      console.warn('[janus] explorer load failed:', error);
      contentPane.innerHTML = '<div class="explorer-error"><p>Failed to load article preview.</p></div>';
    }
  }

  function renderNode(node) {
    const item = document.createElement('li');

    if (node.slug) {
      const link = document.createElement('a');
      link.className = 'explorer-file';
      link.href = `/${node.slug}/`;
      link.innerHTML =
        '<span class="file-icon">📄</span>' +
        `<span class="file-title">${escapeHtml(node.title || node.name)}</span>` +
        (node.date ? `<span class="file-date">${escapeHtml(node.date)}</span>` : '');
      link.addEventListener('click', (event) => {
        event.preventDefault();
        loadArticle(node.slug, link);
      });
      item.appendChild(link);
      return item;
    }

    const folder = document.createElement('div');
    folder.className = 'explorer-folder';
    folder.setAttribute('role', 'button');
    folder.setAttribute('tabindex', '0');
    folder.setAttribute('aria-expanded', 'false');
    folder.innerHTML =
      `<span class="folder-name">${escapeHtml(node.name)}</span>` +
      `<span class="folder-count">${countLeaves(node)}</span>`;

    const childrenContainer = document.createElement('div');
    childrenContainer.className = 'explorer-children';

    if (node.children && node.children.length) {
      const list = document.createElement('ul');
      sortChildren(node.children).forEach((child) => {
        list.appendChild(renderNode(child));
      });
      childrenContainer.appendChild(list);
    }

    function toggleFolder() {
      const expanded = folder.getAttribute('aria-expanded') === 'true';
      folder.setAttribute('aria-expanded', String(!expanded));
      childrenContainer.classList.toggle('open', !expanded);
    }

    folder.addEventListener('click', toggleFolder);
    folder.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggleFolder();
      }
    });

    item.appendChild(folder);
    item.appendChild(childrenContainer);
    return item;
  }

  if (!tree.children || tree.children.length === 0) {
    root.innerHTML = '<div class="explorer-empty"><p>No articles found.</p></div>';
    return;
  }

  const list = document.createElement('ul');
  sortChildren(tree.children).forEach((child) => {
    list.appendChild(renderNode(child));
  });
  root.appendChild(list);
})();
