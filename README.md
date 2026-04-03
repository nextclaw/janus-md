# Janus-MD

> Dual-state static site template — HTML for humans, Markdown for AI.

[![Build & Publish](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Janus-MD is a ready-to-use static site generator template that emits:

- `/<slug>/index.html` for browsers and traditional crawlers
- `/<slug>.md` for AI agents, RAG pipelines, and other Markdown-aware consumers

The default canonical HTML style is `/<slug>/`. Markdown source URLs stay `/<slug>.md`.

## Features

**Core**
- Dual-state HTML + Markdown output from a single source file
- Recursive article discovery with nested slugs
- Title deduplication — strips redundant `<h1>` when it matches frontmatter title
- Cache-busting — SHA-256 content hashes on all CSS/JS asset URLs

**Content Enrichment** (opt-in via `[features]` in config)
- TOC sidebar — sticky right-side with scroll tracking + mobile drawer
- Cover images — hero-style frontmatter-driven cover rendering
- Rating stars — numeric rating (0–5) → ⭐/☆ display
- Lastmod priority — `display_date` prefers `lastmod` over `date`
- Math/Mermaid on-demand — template-driven CDN loading with 3-level priority (frontmatter > config > content detection)

**Content Organization** (opt-in)
- Category navigation — auto-collected from frontmatter, exposed in nav bar + `/category/<slug>/` listing pages
- Tags system — tag cloud at `/tags/` + per-tag listing at `/tags/<tag>/`
- Mermaid diagrams — custom preprocessor converts fenced blocks before codehilite (no dark background bug)

**Built-in**
- Emoji shortcode rendering via `pymdownx.emoji`
- MathJax-compatible math via `pymdownx.arithmatex`
- Highlight syntax `==text==` via `pymdownx.mark`
- Obsidian-compatible `[[wiki links]]`
- Task status markers: `[ ]`, `[-]`, `[x]`, `[!]`, `[~]`
- Internal Explorer page (split-pane article browser)
- Index pagination
- Static pages injection (`pages/` directory)
- Atom feed, sitemap, `llms.txt`, `robots.txt`
- JSON-LD structured data
- Generic Nginx and Cloudflare Worker gateway configs
- GitHub Actions → `sites` branch deployment flow
- No npm or vendor bootstrap required

## Quick start

```bash
git clone https://github.com/nextclaw/janus-md.git my-site
cd my-site
uv run -- python build.py
cd dist && python3 -m http.server 8080
```

Read:

- [docs/QUICKSTART.md](docs/QUICKSTART.md)
- [docs/TEMPLATE-SETUP.md](docs/TEMPLATE-SETUP.md)
- [docs/DEPLOY.md](docs/DEPLOY.md)
- [docs/DESIGN.md](docs/DESIGN.md)

## Project structure

```text
janus-md/
├── articles/            # Markdown articles (recursive subdirectories)
├── templates/
│   ├── base.html        # Base layout (header/footer/theme toggle)
│   ├── index.html       # Home page article listing
│   ├── article.html     # Article page (cover/TOC/rating/tags)
│   ├── explorer.html    # Explorer split-pane browser
│   ├── category.html    # Category article listing
│   ├── tags.html        # Tag cloud index
│   └── tag.html         # Single tag article listing
├── static/
│   ├── css/             # style.css + codehilite.css + theme.css + custom.css
│   └── js/              # main.js + explorer.js
├── pages/               # [Optional] Static pages injected into dist/
├── deploy/              # Nginx + Cloudflare Worker configs
├── verification/        # Root-level verification files
├── build.py             # Core build script (single file, ~1120 lines)
├── janus.config.toml    # Site configuration
└── pyproject.toml       # Python dependency declaration
```

## Configuration

```toml
[features]
toc = false              # Article TOC sidebar
rating = false           # Rating stars display
lastmod = false          # Prefer lastmod over date
cover = false            # Hero cover images
math = true              # MathJax on-demand (backward compat)
mermaid = true           # Mermaid on-demand

[categories]
expose_in_nav = false    # Show categories in navigation bar

[tags]
enabled = false          # Enable /tags/ and /tags/<tag>/ pages
```

All features default to **off** (except math/mermaid), so existing forks see zero behavior change.

## Frontmatter

```yaml
---
title: "Article Title"
date: 2026-03-20
lastmod: 2026-04-01       # [features.lastmod] preferred over date
description: "One-sentence summary"
author:
  - "Your Name"
tags: [tag1, tag2]
category: "guide"          # [categories] auto-collected for nav + listing pages
rating: 4                  # [features.rating] renders as ⭐⭐⭐⭐☆
cover: /assets/img/hero.jpg  # [features.cover] hero image
toc: true                  # Override global [features.toc] per-article
math: true                 # Override global [features.math] per-article
mermaid: false             # Override global [features.mermaid] per-article
draft: false
faq:
  - q: "Question?"
    a: "Answer."
---
```

## Notes

- Explorer can be generated but hidden from nav via `janus.config.toml`
- Verification files placed in `verification/` are copied to site root on build
- Static pages in `pages/` override same-name generated files (last-write wins)
- Gateway-owned slash canonicalization and AI negotiation should live in one layer only
- Mermaid blocks are preprocessed before codehilite — no Pygments interference

中文说明见 [README-cn.md](README-cn.md).
