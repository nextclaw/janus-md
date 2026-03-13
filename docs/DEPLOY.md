# Janus-MD · Deployment Guide

Three deployment options, ordered by complexity.

---

## Option A — GitHub Pages + Cloudflare Worker (Recommended for beginners)

**Architecture**: GitHub Actions builds → pushes to `sites` branch → Cloudflare Pages serves + Worker handles content negotiation.

### 1. Push source to GitHub

```bash
git remote add origin https://github.com/<you>/my-site.git
git push -u origin main
```

### 2. Set the `SITE_URL` variable

GitHub repo → **Settings → Variables → Actions → New repository variable**:

| Name | Value |
|------|-------|
| `SITE_URL` | `https://your-site.pages.dev` or your custom domain |

### 3. CI/CD workflow (built-in)

`.github/workflows/build-and-publish.yml` runs on every push to `main`:

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv run build.py
        env:
          SITE_URL: ${{ vars.SITE_URL }}
      - uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
          publish_branch: sites
          force_orphan: true
```

> **Permissions**: Enable *Read and write permissions* under **Settings → Actions → General → Workflow permissions**.

### 4. Connect to Cloudflare Pages

1. Cloudflare Dashboard → **Pages** → Create a project → Connect to Git
2. Select your repo, set **Production branch** to `sites`
3. **Build command**: *(leave empty — `sites` branch contains pre-built output)*
4. **Build output directory**: `/`

### 5. Deploy the Cloudflare Worker

Copy `deploy/cloudflare-worker.js` into your Cloudflare Pages project:

- Place it as `_worker.js` at the root of your `dist/` output, **or**
- Use the Cloudflare dashboard Workers editor to paste and deploy the script.

```bash
# With Wrangler CLI
npx wrangler pages deploy dist --project-name my-site
```

---

## Option B — VPS Self-Hosting (Nginx)

**Architecture**: GitHub Actions → `sites` branch → VPS pulls via Git → Nginx serves `dist/` directly.

### 1. Initialise the VPS

```bash
apt-get install -y nginx git

# Clone the sites branch
git clone --branch sites --single-branch \
    https://github.com/<you>/my-site.git \
    /var/www/my-site
```

### 2. Configure Nginx

```bash
cp /path/to/deploy/nginx.conf /etc/nginx/sites-available/my-site
# Edit server_name and root path in the file
ln -s /etc/nginx/sites-available/my-site /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

Key content-negotiation design (full config in `deploy/nginx.conf`):

```nginx
# http {} block — map variables (computed once per request, zero if-nesting)
map $http_user_agent $is_ai_bot { ... }
map $http_accept    $wants_markdown { ... }
map "$is_ai_bot:$wants_markdown" $serve_markdown { ... }

# server {} block
location / {
    set $target "$uri/index.html";
    if ($serve_markdown = "1") { set $target "$uri.md"; }
    try_files $target $uri $uri/ =404;
}
```

### 3. Auto-pull on deploy

**Option 1 — cron** (poll every 5 minutes):

```bash
# /opt/deploy/pull-sites.sh
#!/bin/bash
cd /var/www/my-site
git fetch origin sites
git reset --hard origin/sites
echo "$(date): deployed" >> /var/log/janus-deploy.log
```

```bash
chmod +x /opt/deploy/pull-sites.sh
echo "*/5 * * * * /opt/deploy/pull-sites.sh" | crontab -
```

**Option 2 — GitHub webhook** (instant, recommended):  
Use [adnanh/webhook](https://github.com/adnanh/webhook) or any lightweight HTTP listener.

### 4. HTTPS with Let's Encrypt

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

---

## Option C — Cloudflare Pages Direct Deploy (no VPS)

Bypass the `sites` branch and deploy straight from CI:

```yaml
# Replace the peaceiris step with:
- name: Deploy to Cloudflare Pages
  uses: cloudflare/pages-action@v1
  with:
    apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
    projectName: my-site
    directory: dist
    gitHubToken: ${{ secrets.GITHUB_TOKEN }}
```

---

## Production Checklist

```bash
DOMAIN="https://your-site.example.com"

curl -sI "$DOMAIN/"                                    # HTML homepage
curl -sI "$DOMAIN/welcome"                             # HTML article
curl -sI "$DOMAIN/welcome.md" | grep content-type      # text/markdown
curl -sI -H "Accept: text/markdown" "$DOMAIN/welcome" \
  | grep content-type                                  # text/markdown (needs gateway)
curl -sI "$DOMAIN/feed.xml"  | grep content-type       # application/atom+xml
curl -s  "$DOMAIN/llms.txt"  | head -5
curl -s  "$DOMAIN/sitemap.xml" | head -5
```

---

## Common Issues

**Q: `sites` branch push fails with permission error?**  
Go to **Settings → Actions → General → Workflow permissions** and enable *Read and write permissions*.

**Q: Content negotiation not working on Nginx?**  
The `map` directives must be inside the `http {}` block, not inside `server {}`. Check with `nginx -T`.

**Q: Cloudflare shows stale content?**  
Dashboard → **Caching → Purge Everything**, or trigger a new Pages deployment.
