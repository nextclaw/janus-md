# Janus-MD · Quick Start

Get a local dual-state site running in a few minutes.

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | >= 0.5 | Python package manager |
| Git | >= 2.x | Version control & CI/CD |
| Python | >= 3.11 | Managed by `uv` |

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 1. Use the template

```bash
git clone https://github.com/nextclaw/janus-md.git my-site
cd my-site
```

If you created a repo with GitHub's template button, continue with [TEMPLATE-SETUP.md](./TEMPLATE-SETUP.md).

## 2. Configure your site

Edit `janus.config.toml`:

```toml
[site]
url         = "https://my-site.example.com"
name        = "My Site"
description = "A dual-state static site"
language    = "en"
author      = "Your Name"

[explorer]
enabled = true
expose_in_nav = true
```

Notes:

- Canonical human-facing article URLs default to `/slug/`
- Markdown source URLs remain `/slug.md`
- Explorer can be generated without being exposed in nav by setting `expose_in_nav = false`

## 3. Write your first article

Create `articles/hello-world.md`:

```markdown
---
title: "Hello, World!"
date: 2026-03-20
updated: 2026-03-21
description: "My first dual-state article"
author:
  - "Your Name"
  - "Editor Name"
tags: [intro, demo]
faq:
  - q: "Why Janus-MD?"
    a: "It serves HTML to humans and Markdown to AI from the same source."
---

# Hello, World! :rocket:

This article is served as **HTML** to browsers and **Markdown** to AI agents.

Inline math works: $E = mc^2$.

- [x] Article written
- [-] Site deployed
- [ ] First reader arrived
```

## 4. Build locally

```bash
uv run -- python build.py
```

What the builder does:

- renders HTML to `dist/<slug>/index.html`
- copies raw Markdown to `dist/<slug>.md`
- generates `feed.xml`, `sitemap.xml`, `llms.txt`, `robots.txt`
- converts emoji shortcodes at build time
- preserves math markup for runtime MathJax
- optionally generates `/explorer/`
- copies files from `verification/` into `dist/`

## 5. Preview locally

```bash
cd dist && python3 -m http.server 8080
```

Open:

| URL | Returns |
|-----|---------|
| `http://localhost:8080/` | Homepage HTML |
| `http://localhost:8080/hello-world/` | Article HTML |
| `http://localhost:8080/hello-world.md` | Article Markdown |
| `http://localhost:8080/explorer/` | Explorer, when enabled |

Notes:

- `python -m http.server` does not perform AI/content negotiation
- slash canonical redirects are owned by Nginx or the Cloudflare Worker, not the static preview server

## 6. Built-in Markdown features

Janus-MD ships with:

- Python-Markdown core extensions from `janus.config.toml`
- task status markers: `[ ]`, `[-]`, `[x]`, `[!]`, `[~]`
- `pymdownx.emoji` for `:shortcode:` -> Unicode emoji
- `pymdownx.arithmatex` for MathJax-compatible math markup

No npm or vendor bootstrap step is required.

## 7. Verification files

Place root-level verification files in `verification/`, for example:

```text
verification/google1234567890abcdef.html
verification/brave-rewards-verification.txt
```

They are copied to the built site root unchanged.

## Frontmatter reference

```yaml
---
title: "Article Title"              # required
date: 2026-03-20                    # recommended, YYYY-MM-DD
updated: 2026-03-21                 # optional, YYYY-MM-DD
description: "One-line summary"     # recommended
author: "Your Name"                 # string or list
# author: ["Your Name", "Editor"]
tags: [tag1, tag2]                  # optional
draft: false                        # set true to exclude from build
cover: /assets/img/cover.jpg        # optional OG image
faq:                                # optional FAQ schema input
  - q: "Question?"
    a: "Answer."
---
```

## Next steps

- [DEPLOY.md](./DEPLOY.md): production deployment patterns
- [DESIGN.md](./DESIGN.md): architecture and routing model
- [production-validation-sop.md](./production-validation-sop.md): post-deploy checks
