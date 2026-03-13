# Janus-MD

> **Dual-state static site template** — HTML for humans, Markdown for AI.

[![Build & Publish](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Janus-MD** is a ready-to-use static site generator template that automatically serves:

- `/<slug>/index.html` → rendered HTML for browsers and traditional crawlers
- `/<slug>.md` → raw Markdown for AI agents, RAG pipelines, and MCP tools

Content negotiation happens transparently at the gateway layer (Nginx or Cloudflare Worker) — **no changes needed to your content**.

---

## ✨ Features

- ✅ **Dual-state output** — HTML + Markdown from a single Markdown source
- ✅ **Task status markers** — `[ ]` `[-]` `[x]` `[!]` `[~]` rendered as styled badges
- ✅ **Multi-level directories** — `articles/2026/03/post.md` → `/2026/03/post`
- ✅ **AI discovery layer** — `llms.txt`, `sitemap.xml`, `robots.txt`
- ✅ **Atom RSS feed** — `feed.xml`
- ✅ **CI/CD** — GitHub Actions → `sites` branch (no Python on production)
- ✅ **Gateway configs** — Nginx (VPS) and Cloudflare Worker included
- ✅ **Light / Dark theme** — system-preference aware, user overridable
- ✅ **SEO** — Open Graph, JSON-LD structured data, meta descriptions
- ✅ **Obsidian compatible** — frontmatter format matches Obsidian defaults

---

## 🚀 Quick Start

### Using the Template (recommended)

1. Click **[Use this template](https://github.com/nextclaw/janus-md/generate)** on GitHub
2. Create your repository
3. Follow **[docs/TEMPLATE-SETUP.md](docs/TEMPLATE-SETUP.md)** for the 5-step post-fork configuration

### Clone Directly

```bash
git clone https://github.com/nextclaw/janus-md.git my-site
cd my-site

# Edit site config
nano janus.config.toml

# Build
uv run build.py

# Preview
cd dist && python3 -m http.server 8080
```

See **[docs/QUICKSTART.md](docs/QUICKSTART.md)** for the full guide.

---

## 📁 Project Structure

```
janus-md/
├── articles/           ← Write here (supports subdirectories)
├── templates/          ← Jinja2 HTML templates
├── static/             ← CSS, JS, images
├── deploy/
│   ├── nginx.conf              ← VPS gateway config
│   └── cloudflare-worker.js   ← Edge gateway config
├── .github/workflows/
│   └── build-and-publish.yml  ← CI/CD: main → build → sites branch
├── docs/
│   ├── QUICKSTART.md           ← 5-minute getting started guide
│   ├── TEMPLATE-SETUP.md       ← Post "Use this template" guide
│   ├── DEPLOY.md               ← Deployment options (CF / Nginx / VPS)
│   └── DESIGN.md               ← Architecture & design decisions
├── build.py            ← SSG engine (single file, zero framework)
├── janus.config.toml   ← Site configuration
└── pyproject.toml      ← Python dependencies (uv)
```

---

## ✍️ Writing Articles

### Frontmatter

```yaml
---
title: "Article Title"
date: 2026-03-14
description: "One-sentence summary"
author: "Your Name"
tags: [tag1, tag2]
draft: false
cover: /assets/img/cover.jpg   # optional OG image
---
```

### Task Status Markers

| Syntax | Meaning     | Badge colour |
|--------|-------------|-------------|
| `[ ]`  | Not started | grey |
| `[-]`  | In progress | blue |
| `[x]`  | Done        | green |
| `[!]`  | Blocked     | red |
| `[~]`  | Deferred    | amber / strikethrough |

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | 5-minute local setup guide |
| [docs/TEMPLATE-SETUP.md](docs/TEMPLATE-SETUP.md) | Post "Use this template" configuration |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Cloudflare Pages, Nginx VPS, direct deploy |
| [docs/DESIGN.md](docs/DESIGN.md) | Architecture, design decisions, roadmap |

中文文档: [README-cn.md](README-cn.md)

---

## 🛠 Requirements

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) — manages Python dependencies automatically

---

## 📦 Deployment

| Option | Guide |
|--------|-------|
| Cloudflare Pages + Worker | [docs/DEPLOY.md](docs/DEPLOY.md#option-a) |
| VPS + Nginx | [docs/DEPLOY.md](docs/DEPLOY.md#option-b) |
| Cloudflare Pages direct | [docs/DEPLOY.md](docs/DEPLOY.md#option-c) |

---

## 📜 License

MIT — see [LICENSE](LICENSE).
