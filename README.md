# Janus-MD

> **Dual-state static site template** — HTML for humans, Markdown for AI.

[![Build & Publish](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml)

**Janus-MD** is a ready-to-use static site generator template that automatically serves:

- `/<slug>/index.html` → rendered HTML for browsers and traditional crawlers
- `/<slug>.md` → raw Markdown for AI agents, RAG pipelines, and MCP tools

Content negotiation is handled transparently at the gateway layer (Nginx or Cloudflare Worker) — **no changes needed to your content**.

---

## Features

- ✅ **Dual-state output** — HTML + Markdown generated from a single source
- ✅ **Task status markers** — `[ ]` `[-]` `[x]` `[!]` `[~]` rendered as styled badges
- ✅ **Multi-level directories** — `articles/2026/03/post.md` → `/2026/03/post`
- ✅ **AI discovery layer** — `llms.txt`, `sitemap.xml`, `robots.txt`
- ✅ **Atom RSS feed** — `feed.xml`
- ✅ **CI/CD** — GitHub Actions → `sites` branch (no Python on production server)
- ✅ **Gateway configs** — Nginx (VPS) and Cloudflare Worker included
- ✅ **Light/Dark themes** — system preference aware, user overridable
- ✅ **SEO** — Open Graph, JSON-LD structured data, meta descriptions
- ✅ **Obsidian compatible** — frontmatter format matches Obsidian defaults

---

## Quick Start

```bash
# 1. Use this template (GitHub UI) or clone
git clone https://github.com/nextclaw/janus-md.git my-site
cd my-site

# 2. Configure your site
edit janus.config.toml   # set url, name, description, author

# 3. Write
mkdir -p articles
# create articles/hello-world.md with YAML frontmatter

# 4. Build
uv run build.py

# 5. Preview
cd dist && python3 -m http.server 8080
```

See [docs/QUICKSTART.md](.ag_checkpoints/docs/QUICKSTART.md) for the full 5-step guide.

---

## Article Frontmatter

```yaml
---
title: "Article Title"
date: 2026-03-14
description: "One-sentence summary"
author: "Your Name"
tags: [tag1, tag2]
draft: false          # set true to exclude from build
cover: /assets/img/cover.jpg   # optional OG image
---
```

---

## Task Status Markers

Write these anywhere in your Markdown:

| Syntax | Meaning    | Visual |
|--------|------------|--------|
| `[ ]`  | 未开始     | grey badge |
| `[-]`  | 进行中     | blue badge |
| `[x]`  | 已完成     | green badge |
| `[!]`  | 阻塞中     | red badge |
| `[~]`  | 延后/放弃  | strikethrough amber |

Example:

```markdown
- [x] Design complete
- [-] Implementation in progress
- [ ] Tests not started
- [!] Deployment blocked by DNS issue
- [~] Feature dropped
```

---

## Project Structure

```
janus-md/
├── articles/           ← Write here (supports subdirectories)
├── templates/          ← Jinja2 HTML templates
├── static/             ← CSS, JS, images
├── deploy/
│   ├── nginx.conf              ← VPS gateway config
│   └── cloudflare-worker.js   ← Edge gateway config
├── .github/workflows/
│   └── build-and-publish.yml  ← CI/CD pipeline
├── build.py            ← SSG engine (single file, no framework)
├── janus.config.toml   ← Site configuration
└── pyproject.toml      ← Python dependencies (uv)
```

---

## Deployment

| Option | Guide |
|--------|-------|
| GitHub Pages + Cloudflare Worker | [DEPLOY.md](.ag_checkpoints/docs/DEPLOY.md) |
| VPS + Nginx | [DEPLOY.md](.ag_checkpoints/docs/DEPLOY.md) |
| Cloudflare Pages (direct) | [DEPLOY.md](.ag_checkpoints/docs/DEPLOY.md) |

---

## Requirements

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (auto-manages Python deps)

---

## License

MIT — see [LICENSE](LICENSE).
