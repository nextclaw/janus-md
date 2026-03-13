# Janus-MD · Quick Start

Get a local dual-state site running in **5 minutes**.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | ≥ 0.5 | Python package manager |
| Git | ≥ 2.x | Version control & CI/CD |
| Python | ≥ 3.11 | Managed automatically by uv |

Install uv (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Step 1 — Use the Template

Click **"Use this template"** on GitHub, or clone directly:

```bash
git clone https://github.com/nextclaw/janus-md.git my-site
cd my-site
```

> If you used the GitHub template button, see [TEMPLATE-SETUP.md](./TEMPLATE-SETUP.md) for the post-fork configuration steps.

---

## Step 2 — Configure Your Site

Edit `janus.config.toml`:

```toml
[site]
url         = "https://my-site.example.com"   # ← your domain (no trailing slash)
name        = "My Site"
description = "A dual-state static site"
language    = "en"
author      = "Your Name"
```

---

## Step 3 — Write Your First Article

Create `articles/hello-world.md`:

```markdown
---
title: "Hello, World!"
date: 2026-03-14
description: "My first dual-state article"
author: "Your Name"
tags: [intro]
draft: false
---

# Hello, World!

This article is served as **HTML** to browsers and **Markdown** to AI agents.

## Task Status Example

- [x] Article written
- [-] Site deployed
- [ ] First reader arrived
```

---

## Step 4 — Build Locally

```bash
uv run build.py
```

Expected output:

```
🔨 Building My Site …
📝 Found 1 article(s):
   • hello-world — Hello, World!

   ✅ hello-world/index.html
   ✅ hello-world.md
   ✅ index.html  ✅ sitemap.xml  ✅ feed.xml  ✅ llms.txt  ✅ robots.txt  ✅ assets/

🎉 Build complete! 1 article(s) → dist/
```

---

## Step 5 — Preview Locally

```bash
cd dist && python3 -m http.server 8080
```

Open in browser:

| URL | Returns |
|-----|---------|
| `http://localhost:8080/` | Homepage (HTML) |
| `http://localhost:8080/hello-world` | Article (HTML) |
| `http://localhost:8080/hello-world.md` | Article (Markdown) |

Simulate an AI client:

```bash
# Content-type negotiation requires Nginx/Worker — test .md links directly locally
curl http://localhost:8080/hello-world.md
```

---

## Step 6 — Deploy

See [DEPLOY.md](./DEPLOY.md) for GitHub Pages + Cloudflare Worker, VPS Nginx, or direct Cloudflare Pages options.

---

## Article Frontmatter Reference

```yaml
---
title: "Article Title"            # required
date: 2026-03-14                  # required, YYYY-MM-DD
description: "One-line summary"   # recommended (OG, Atom, llms.txt)
author: "Your Name"               # optional (overrides site.author)
tags: [tag1, tag2]                # optional
draft: false                      # set true to exclude from build
cover: /assets/img/cover.jpg      # optional (OG image)
---
```

---

## Task Status Markers

Use anywhere in Markdown to annotate work status:

| Syntax | Meaning     | Style |
|--------|-------------|-------|
| `[ ]`  | Not started | grey  |
| `[-]`  | In progress | blue  |
| `[x]`  | Done        | green |
| `[!]`  | Blocked     | red   |
| `[~]`  | Deferred    | amber / strikethrough |

Markers render as inline badge spans in HTML; the `.md` output preserves them verbatim.

---

## Multi-level Article Directories

Articles can live at any depth inside `articles/`:

```
articles/
  welcome.md               → /welcome
  2026/
    03/
      my-post.md           → /2026/03/my-post
  tutorials/
    getting-started.md     → /tutorials/getting-started
```

---

## FAQ

**Q: Article not appearing?**  
Check that `draft: false` is set and `date` is in `YYYY-MM-DD` format.

**Q: Syntax highlighting not working?**  
Confirm that `static/css/codehilite.css` is present and the `<link>` in `base.html` is intact.

**Q: Use Obsidian as the writing tool?**  
Symlink your Obsidian vault subdirectory to `articles/`:
```bash
ln -s /path/to/obsidian-vault/Blog articles
```
