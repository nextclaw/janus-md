# Janus-MD · Architecture & Design

Reference document covering key design decisions and the overall architecture.

---

## Core Problem

The modern web has two distinct content consumers:

| Consumer | Expected format | Examples |
|----------|----------------|---------|
| Humans   | Styled HTML    | Browsers |
| AI / Machines | Structured plain text | LLM agents, RAG pipelines, MCP tools |

Traditional SSGs (Hugo, Jekyll, Hexo) serve only the first. Janus-MD generates **both forms at build time** and routes by consumer identity at the gateway — with zero content duplication.

---

## Name

```
Janus-MD
├── Janus  → Roman god of duality (two faces)
└── MD     → Markdown, the source format
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│               Authoring layer               │
│  articles/**/*.md  (YAML frontmatter)       │
└────────────────────┬────────────────────────┘
                     │ uv run build.py
          ┌──────────▼──────────┐
          │      dist/ output   │
          │  <slug>/index.html  │  ← HTML for humans
          │  <slug>.md          │  ← Markdown for AI
          │  index.html         │
          │  feed.xml           │  ← Atom RSS
          │  sitemap.xml        │
          │  llms.txt           │  ← AI discovery
          │  robots.txt         │
          └──────────┬──────────┘
                     │ git push → sites branch
          ┌──────────▼──────────┐
          │    Gateway layer    │
          │  Nginx (VPS)        │
          │  Cloudflare Worker  │
          └──────────┬──────────┘
                     │
         ┌───────────┴───────────┐
   [Browser / crawler]   [AI bot / Accept: text/markdown]
    ↓ <slug>/index.html         ↓ <slug>.md
```

---

## Key Design Decisions

### 1. Single-file Python build engine

**Rationale**: production nodes must not run Python. The output is pure static files pulled via Git. Having a single `build.py` avoids framework lock-in, keeps dependencies minimal (`markdown`, `pyyaml`, `jinja2`, `pygments`), and runs cleanly under `uv run`.

### 2. Dual-signal content negotiation

Both User-Agent and Accept header are checked independently; either alone is sufficient to trigger Markdown delivery:

```
is_ai_bot(UA)?           → serve .md
Accept: text/markdown?   → serve .md
neither                  → serve index.html
```

This means custom tools (MCP, scripts) can request Markdown via `Accept: text/markdown` **without being listed in the UA blocklist**.

### 3. Nginx `map` pattern (no `if` nesting)

Nginx's `if` inside `location` is [documented as dangerous](https://www.nginx.com/resources/wiki/start/topics/depth/ifisevil/). Janus-MD uses `map` in the `http` block to pre-compute a single `$serve_markdown` variable, then a single `try_files` in `location /` consults it:

```nginx
map "$is_ai_bot:$wants_markdown" $serve_markdown { "1:0" "1"; "0:1" "1"; ... }
location / {
    set $target "$uri/index.html";
    if ($serve_markdown = "1") { set $target "$uri.md"; }
    try_files $target $uri $uri/ =404;
}
```

### 4. AI discovery trifecta

| File | Standard | Purpose |
|------|---------|---------|
| `sitemap.xml` | sitemaps.org | Traditional search engine crawlers |
| `llms.txt` | llmstxt.org | LLM agents find content index |
| `robots.txt` | RFC | Declares `Sitemap:` and `Llms-Txt:` locations |

`llms.txt` entries point to `.md` URLs (not HTML), so agents retrieve structured content directly.

### 5. Task status markers — custom Markdown extension

A `Treeprocessor` subclass (`TaskStatusExtension`) post-processes the HTML element tree after standard Markdown parsing. It uses BFS traversal over a **snapshot** of the pre-insertion tree to avoid infinite loops from newly-inserted `<span>` nodes:

```python
queue = [root]
elements = []
while queue:
    el = queue.pop(0)
    elements.append(el)
    queue.extend(list(el))        # snapshot before any mutation

for el in elements:               # process only original nodes
    self._process_element(el)
```

Markers in `.md` output are preserved verbatim; only HTML receives the styled `<span>` badges.

### 6. Recursive article discovery

`ARTICLES_DIR.rglob("*.md")` scans all depths. The slug is derived from the relative path:

```
articles/2026/03/my-post.md  →  slug = "2026/03/my-post"
```

Output paths are created with `mkdir -p`, so deeply nested slugs work transparently.

### 7. CI/CD dual-branch model

```
main branch    ← source code only (articles, templates, build.py)
sites branch   ← built dist/ output only (force_orphan=true, no history)
```

Production servers pull from `sites` via bare Git — no Python, no build tooling on the server.

---

## Dependency Comparison

| Framework | Language | Learning curve | Native dual-state | Hackable |
|-----------|---------|---------------|------------------|---------|
| Hugo | Go | Medium | ❌ | Low |
| Jekyll | Ruby | Low | ❌ | Medium |
| Gatsby | Node/React | High | ❌ | High |
| **Janus-MD** | **Python** | **Minimal** | **✅** | **Full** |

---

## Extension Roadmap

### Phase 1 (shipped)
- [x] Dual-state HTML + Markdown SSG
- [x] Task status markers (5 states)
- [x] Multi-level article directories
- [x] Atom feed + llms.txt + sitemap + robots.txt
- [x] Light / dark theme
- [x] GitHub Actions CI/CD
- [x] Nginx + Cloudflare Worker gateway configs

### Phase 2 (planned)
- [ ] Tag index pages (`/tags/<tag>/index.html`)
- [ ] Client-side search (Fuse.js + build-time JSON index)
- [ ] `pages/` directory for standalone non-article content
- [ ] Image optimisation (WebP conversion + `srcset`)

### Phase 3 (future)
- [ ] Obsidian vault symlink documentation
- [ ] MCP server exposing site content as tools
- [ ] i18n (multi-language article directories)

---

## References

- [llmstxt.org](https://llmstxt.org/) — `llms.txt` standard
- [sitemaps.org](https://www.sitemaps.org/) — Sitemap protocol
- [RFC 4287](https://datatracker.ietf.org/doc/html/rfc4287) — Atom feed
- [Nginx `if` is Evil](https://www.nginx.com/resources/wiki/start/topics/depth/ifisevil/)
- [astral-sh/uv](https://docs.astral.sh/uv/)
- [Cloudflare Workers](https://developers.cloudflare.com/workers/)
- [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages)
