# Janus-MD

> Dual-state static site template — HTML for humans, Markdown for AI.

[![Build & Publish](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Janus-MD is a ready-to-use static site generator template that emits:

- `/<slug>/index.html` for browsers and traditional crawlers
- `/<slug>.md` for AI agents, RAG pipelines, and other Markdown-aware consumers

The default canonical HTML style is `/<slug>/`. Markdown source URLs stay `/<slug>.md`.

## Features

- dual-state HTML + Markdown output from one source file
- recursive article discovery with nested slugs
- built-in emoji shortcode rendering via `pymdownx.emoji`
- built-in MathJax-compatible math via `pymdownx.arithmatex`
- task status markers: `[ ]`, `[-]`, `[x]`, `[!]`, `[~]`
- optional internal explorer page
- Atom feed, sitemap, `llms.txt`, and `robots.txt`
- generic Nginx and Cloudflare Worker gateway configs
- GitHub Actions -> `sites` branch deployment flow
- no npm or vendor bootstrap requirement

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
- [docs/production-validation-sop.md](docs/production-validation-sop.md)

## Project structure

```text
janus-md/
├── articles/
├── templates/
├── static/
├── deploy/
├── docs/
├── verification/
├── build.py
├── janus.config.toml
└── pyproject.toml
```

## Frontmatter

```yaml
---
title: "Article Title"
date: 2026-03-20
updated: 2026-03-21
description: "One-sentence summary"
author:
  - "Your Name"
  - "Editor Name"
tags: [tag1, tag2]
faq:
  - q: "Question?"
    a: "Answer."
draft: false
cover: /assets/img/cover.jpg
---
```

## Notes

- explorer can be generated but hidden from nav via `janus.config.toml`
- verification files placed in `verification/` are copied to site root on build
- gateway-owned slash canonicalization and AI negotiation should live in one layer only

中文说明见 [README-cn.md](README-cn.md).
