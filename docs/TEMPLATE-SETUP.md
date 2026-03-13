# Janus-MD · Template Setup Guide

This guide is for users who clicked **"Use this template"** on GitHub.  
If you cloned directly, start at [QUICKSTART.md](./QUICKSTART.md).

---

## What Happens When You Use the Template

GitHub creates a **fresh repository** with the same file structure as Janus-MD, but with **no commit history**. This is intentional — your site is a clean slate.

```
nextclaw/janus-md (template)
         │
         │  "Use this template" → creates
         ▼
your-username/my-site  (new repo, independent history)
```

---

## 5-Step Post-Fork Setup

### Step 1 — Update `janus.config.toml`

This is the **only file you must edit** before your first build:

```toml
[site]
url         = "https://my-site.example.com"   # ← your real domain
name        = "My Site"                        # ← your site name
description = "What this site is about"
language    = "en"                             # e.g. zh-CN, ja, fr
author      = "Your Name"
```

### Step 2 — Set the `SITE_URL` GitHub Variable

The CI/CD workflow reads `SITE_URL` from GitHub Variables so the build knows the canonical URL:

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click the **Variables** tab → **New repository variable**
3. Name: `SITE_URL`, Value: `https://my-site.example.com`

> Use the same value as `url` in `janus.config.toml`.

### Step 3 — Enable Workflow Write Permissions

The workflow pushes built output to the `sites` branch, which requires write access:

1. Go to **Settings** → **Actions** → **General**
2. Under **Workflow permissions**, select **Read and write permissions**
3. Save

### Step 4 — Replace the Sample Articles

Delete the bundled examples and write your own:

```bash
rm articles/welcome.md articles/meta/roadmap.md

# Write your first article
cat > articles/hello-world.md << 'EOF'
---
title: "Hello, World!"
date: 2026-03-14
description: "My first article"
author: "Your Name"
tags: [intro]
draft: false
---

# Hello, World!

Your content here.
EOF
```

### Step 5 — Push and Watch CI Build

```bash
git add -A
git commit -m "chore: initial site configuration"
git push origin main
```

Navigate to **Actions** in your repository — you'll see the **Build & Publish** workflow running. On success, a `sites` branch is automatically created containing the built `dist/` output.

---

## Choose a Deployment Target

After the first successful CI run, connect your `sites` branch to a host:

| Host | Guide |
|------|-------|
| Cloudflare Pages | [DEPLOY.md → Option A](./DEPLOY.md#option-a--github-pages--cloudflare-worker-recommended-for-beginners) |
| VPS + Nginx | [DEPLOY.md → Option B](./DEPLOY.md#option-b--vps-self-hosting-nginx) |
| Cloudflare Pages (direct) | [DEPLOY.md → Option C](./DEPLOY.md#option-c--cloudflare-pages-direct-deploy-no-vps) |

---

## Customisation Checklist

| Task | File | Required? |
|------|------|-----------|
| Set site name, URL, author | `janus.config.toml` | ✅ Yes |
| Set `SITE_URL` GitHub Variable | GitHub Settings | ✅ Yes |
| Enable workflow write permissions | GitHub Settings | ✅ Yes |
| Remove sample articles | `articles/` | ✅ Yes |
| Update header logo letter | `templates/base.html` (`.logo-icon`) | Optional |
| Swap font / color palette | `static/css/style.css` | Optional |
| Update footer text | `templates/base.html` | Optional |
| Swap Pygments color theme | `static/css/codehilite.css` | Optional |

---

## Keeping in Sync with Upstream

If Janus-MD releases new features you want to adopt:

```bash
# Add upstream remote (one-time)
git remote add upstream https://github.com/nextclaw/janus-md.git

# Fetch and merge build engine / templates (not your articles)
git fetch upstream
git merge upstream/main --no-commit --no-ff

# Review changes, keep your config/articles, then commit
git checkout HEAD -- janus.config.toml articles/
git commit -m "chore: merge upstream improvements"
```

---

## File Ownership Map

| Files you **own** (edit freely) | Files from template (update carefully) |
|--------------------------------|---------------------------------------|
| `articles/**` | `build.py` |
| `janus.config.toml` | `templates/` |
| `static/css/style.css` (theme tweaks) | `deploy/nginx.conf` |
| `README.md` (your own readme) | `deploy/cloudflare-worker.js` |
| | `.github/workflows/` |
