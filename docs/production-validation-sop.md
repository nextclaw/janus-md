# Janus-MD Production Validation SOP

Use this checklist after changes to:

- build output
- Nginx routing
- Cloudflare Worker behavior
- discovery-layer files

Examples below assume the sample `welcome` article still exists. Replace `welcome` with any real article slug on your site.

```bash
export BASE="https://example.com"
export ARTICLE="welcome"
export ARTICLE_URL="$BASE/$ARTICLE"
export ARTICLE_CANONICAL_URL="$BASE/$ARTICLE/"
export ARTICLE_MD_URL="$BASE/$ARTICLE.md"
```

## 1. Human request to slashless article URL should redirect to `/slug/`

```bash
curl -sI "$ARTICLE_URL"
```

Expected:

- `301`
- `location: https://example.com/welcome/`

## 2. Human request to canonical article URL should return HTML

```bash
curl -sI "$ARTICLE_CANONICAL_URL"
curl -s -o /dev/null -w "%{content_type}\n" "$ARTICLE_CANONICAL_URL"
```

Expected:

- `200`
- `text/html`

## 3. AI crawler UA to slashless article URL should return Markdown directly

```bash
curl -sI -A "GPTBot/1.0" "$ARTICLE_URL"
curl -s -A "GPTBot/1.0" "$ARTICLE_URL" | head -5
```

Expected:

- `200`
- `content-type: text/markdown; charset=utf-8`
- body begins with frontmatter, usually `---`

## 4. `Accept: text/markdown` should also return Markdown directly

```bash
curl -sI -H "Accept: text/markdown" "$ARTICLE_URL"
curl -s -H "Accept: text/markdown" "$ARTICLE_URL" | head -5
```

Expected:

- `200`
- `content-type: text/markdown; charset=utf-8`
- `x-content-source: markdown`

## 5. Negotiated Markdown responses should carry stable headers

```bash
curl -sI -A "ClaudeBot/1.0" "$ARTICLE_URL" | grep -Ei "^(content-type|x-content-source|x-robots-tag|cache-control|vary):"
```

Expected:

- `content-type: text/markdown; charset=utf-8`
- `x-content-source: markdown`
- `x-robots-tag: noindex`
- `cache-control: public, max-age=3600`
- `vary: Accept, User-Agent`

## 6. Direct `.md` requests should always return Markdown

```bash
curl -sI "$ARTICLE_MD_URL"
curl -s "$ARTICLE_MD_URL" | head -5
```

Expected:

- `200`
- `content-type: text/markdown; charset=utf-8`
- `x-content-source: markdown`

## 7. Homepage should return HTML

```bash
curl -sI "$BASE/"
curl -s -o /dev/null -w "%{content_type}\n" "$BASE/"
```

Expected:

- `200`
- `text/html`

## 8. Discovery-layer files should be reachable

```bash
curl -sI "$BASE/robots.txt"
curl -sI "$BASE/sitemap.xml"
curl -sI "$BASE/feed.xml"
curl -sI "$BASE/llms.txt"
```

Expected:

- all return `200`

## 9. `sitemap.xml` should use canonical `/slug/` article URLs

```bash
curl -s "$BASE/sitemap.xml" | grep -F "<loc>$ARTICLE_CANONICAL_URL</loc>"
```

Expected:

- one exact match

## 10. `feed.xml` should use canonical HTML links and `.md` alternates

```bash
curl -s "$BASE/feed.xml" | grep -F "<link href=\"$ARTICLE_CANONICAL_URL\" rel=\"alternate\" type=\"text/html\"/>"
curl -s "$BASE/feed.xml" | grep -F "<link href=\"$ARTICLE_MD_URL\" rel=\"alternate\" type=\"text/markdown\"/>"
```

Expected:

- both lines are present

## 11. `llms.txt` should point to `.md` URLs

```bash
curl -s "$BASE/llms.txt" | grep -F "/$ARTICLE.md"
```

Expected:

- at least one matching line

## 12. Missing paths should return real `404`

```bash
curl -sI "$BASE/does-not-exist/"
curl -sI -H "Accept: text/markdown" "$BASE/does-not-exist"
```

Expected:

- both return `404`

## 13. Optional origin-only verification

Useful when you need to bypass Cloudflare and inspect origin behavior directly:

```bash
curl -i -H "Host: example.com" "http://127.0.0.1/$ARTICLE" | head -20
curl -i -H "Host: example.com" -A "GPTBot/1.0" "http://127.0.0.1/$ARTICLE" | head -20
curl -i -H "Host: example.com" -H "Accept: text/markdown" "http://127.0.0.1/$ARTICLE" | head -20
```

Expected:

- plain origin request to slashless URL: `301` to canonical `/slug/`
- AI / markdown origin requests: `200 text/markdown`

## 14. Operational note

If public requests behave differently from origin-only checks:

- inspect Cloudflare Redirect Rules first
- confirm slash canonicalization is not duplicated at the edge
