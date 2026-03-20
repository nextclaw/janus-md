# Janus-MD · Deployment Guide

Three deployment options, ordered by operational complexity.

## Option A — GitHub Actions + Cloudflare Pages + Worker

Architecture:

- `main` branch stores source
- GitHub Actions builds `dist/`
- built output is published to the `sites` branch
- Cloudflare Pages serves `sites`
- Cloudflare Worker handles slash canonicalization and AI/Markdown negotiation

### 1. Push source to GitHub

```bash
git remote add origin https://github.com/<you>/my-site.git
git push -u origin main
```

### 2. Set `SITE_URL`

GitHub repo -> `Settings` -> `Variables` -> `Actions`:

| Name | Value |
|------|-------|
| `SITE_URL` | `https://your-site.pages.dev` or your custom domain |

### 3. CI/CD workflow

The built-in workflow builds on every push to `main` and publishes `dist/` to `sites`.

Make sure GitHub Actions has **Read and write permissions** enabled.

### 4. Connect Cloudflare Pages

1. Cloudflare Dashboard -> `Pages` -> `Create a project`
2. Connect your Git repo
3. Set **Production branch** to `sites`
4. Leave build command empty
5. Use `/` as the output directory

### 5. Deploy the Worker

Use `deploy/cloudflare-worker.js`:

- as `_worker.js` in the built output, or
- as a standalone Worker / Pages Function

Important behavior:

- normal `/slug` requests redirect to `/slug/`
- AI UA or `Accept: text/markdown` requests to `/slug` return Markdown directly
- explicit `.md` requests always return Markdown with `X-Content-Source`, `X-Robots-Tag`, and `Vary`

## Option B — VPS + Nginx

Architecture:

- GitHub Actions builds `dist/` into `sites`
- VPS pulls the `sites` branch
- Nginx serves the static files directly

### 1. Initialize the VPS

```bash
apt-get install -y nginx git

git clone --branch sites --single-branch \
  https://github.com/<you>/my-site.git \
  /var/www/janus-site
```

### 2. Install the Nginx config

```bash
cp /path/to/deploy/nginx.conf /etc/nginx/sites-available/janus-site
ln -s /etc/nginx/sites-available/janus-site /etc/nginx/sites-enabled/janus-site
nginx -t
systemctl reload nginx
```

Update at least:

- `server_name`
- `root`

The shipped config implements:

- AI bot / `Accept: text/markdown` detection via `map`
- canonical HTML URLs as `/slug/`
- explicit `.md` handling with `text/markdown`
- negotiated Markdown responses for AI requests
- real `404` for missing paths
- no homepage soft-404 fallback

### 3. Auto-pull the `sites` branch

Use cron, a webhook receiver, or your deployment system of choice.

### 4. TLS

If Nginx terminates TLS directly:

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

If TLS is terminated at Cloudflare and origin stays on `80`, keep the shipped origin-style config and proxy through Cloudflare.

## Option C — Cloudflare Pages direct from CI

Instead of publishing to `sites`, CI can upload `dist/` directly to Cloudflare Pages.

Use `cloudflare/pages-action` in GitHub Actions and keep the same Worker semantics.

## Gateway ownership rules

Choose one place to own slash canonicalization:

- Nginx, or
- the Cloudflare Worker

Do not duplicate `/slug -> /slug/` redirects in both places.

Also do not add a Cloudflare Redirect Rule for slash canonicalization unless it explicitly excludes:

- AI crawler user agents
- requests with `Accept: text/markdown`

If edge redirects run unconditionally, they will break Markdown negotiation by redirecting AI requests before the origin logic runs.

## Validation examples

Assume:

```bash
export BASE="https://your-site.example.com"
export ARTICLE="welcome"
```

Human HTML flow:

```bash
curl -sI "$BASE/$ARTICLE"
curl -sI "$BASE/$ARTICLE/"
```

Expected:

- `/welcome` returns `301` to `/welcome/`
- `/welcome/` returns `200 text/html`

Markdown negotiation:

```bash
curl -sI -A "GPTBot/1.0" "$BASE/$ARTICLE"
curl -sI -H "Accept: text/markdown" "$BASE/$ARTICLE"
curl -sI "$BASE/$ARTICLE.md"
```

Expected:

- all return `200`
- `content-type: text/markdown; charset=utf-8`
- `x-content-source: markdown`

Discovery layer:

```bash
curl -sI "$BASE/robots.txt"
curl -sI "$BASE/sitemap.xml"
curl -sI "$BASE/feed.xml"
curl -sI "$BASE/llms.txt"
```

For a fuller checklist, use [production-validation-sop.md](./production-validation-sop.md).

## Common issues

**Content negotiation does not work on Nginx**

- `map` directives must be placed in the `http {}` block, not inside `server {}`
- run `nginx -T` to confirm the live config

**AI requests still get redirected to `/slug/`**

- disable duplicate Cloudflare Redirect Rules
- check whether the Worker or Nginx is the actual owner of canonical redirects

**Missing paths return the homepage instead of `404`**

- remove any `try_files ... /index.html` fallback unless you are intentionally serving an SPA

**Cloudflare serves stale content**

- purge cache or redeploy
- if origin-only checks are correct but public behavior is wrong, inspect Cloudflare rules first
