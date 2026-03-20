# Janus-MD · Template Setup Guide

This guide is for repositories created with GitHub's **Use this template** button.

If you cloned directly, start with [QUICKSTART.md](./QUICKSTART.md).

## What the template gives you

A fresh repo with:

- sample articles
- a production-ready static build pipeline
- generic templates
- gateway examples for Nginx and Cloudflare Worker
- documentation for deployment and validation

## 1. Update `janus.config.toml`

At minimum, set:

```toml
[site]
url         = "https://my-site.example.com"
name        = "My Site"
description = "What this site is about"
language    = "en"
author      = "Your Name"

[explorer]
enabled = true
expose_in_nav = true
```

Recommended decisions:

- keep canonical HTML URLs as `/slug/`
- keep Markdown URLs as `/slug.md`
- hide explorer from nav if it is only for internal use

## 2. Set the GitHub `SITE_URL` variable

The workflow reads `SITE_URL` at build time.

1. Open your repo -> `Settings` -> `Secrets and variables` -> `Actions`
2. Create a repository variable named `SITE_URL`
3. Set it to the same value as `site.url`

## 3. Enable workflow write permissions

The build workflow publishes `dist/` to the `sites` branch.

GitHub repo -> `Settings` -> `Actions` -> `General` -> `Workflow permissions`

Select:

- `Read and write permissions`

## 4. Replace the sample content

Remove or edit the bundled articles in `articles/`.

The template includes:

- `articles/welcome.md`
- `articles/meta/roadmap.md`
- `articles/mathjax-emoji-test.md`

Use the math/emoji article if you want a quick smoke test for the built-in renderer.

## 5. Add optional verification files

Put root-level verification artifacts in `verification/`:

```text
verification/google1234567890abcdef.html
verification/brave-rewards-verification.txt
```

During build, these files are copied to `dist/` root unchanged.

## 6. Build and preview

```bash
uv run -- python build.py
cd dist && python3 -m http.server 8080
```

Use [production-validation-sop.md](./production-validation-sop.md) after your first real deployment.

## Explorer customization

Explorer is configurable, not hardcoded:

```toml
[explorer]
enabled = true
expose_in_nav = false
```

Behavior:

- `enabled = false`: no explorer page is built
- `enabled = true`, `expose_in_nav = false`: page exists at `/explorer/` but stays out of navigation

Explorer is always treated as an internal page and stays out of sitemap, feed, and `llms.txt`.

## Safe upstream merges after customization

After you start customizing templates and routing, upstream pulls should be selective.

Recommended approach:

```bash
git remote add upstream https://github.com/nextclaw/janus-md.git
git fetch upstream
git diff --stat main..upstream/main
```

When bringing changes in:

- merge content and docs freely
- review `build.py`, `templates/`, and `deploy/` carefully
- preserve your own `janus.config.toml` and `articles/`

A safe merge pattern is:

```bash
git merge upstream/main --no-commit --no-ff
git checkout HEAD -- janus.config.toml articles/
git commit -m "chore: merge upstream improvements"
```

If your site has heavily customized routing or templates, prefer cherry-picking specific upstream improvements instead of full merges.
