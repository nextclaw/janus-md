# Janus-MD · Architecture & Design

Reference document for the template's build model, URL semantics, and gateway behavior.

## Core model

Janus-MD is a dual-state static site template:

- humans get rendered HTML
- AI agents can get the original Markdown

Both outputs are generated at build time from the same source file.

## Output contract

For an article at `articles/tutorials/getting-started.md`:

- human HTML: `/tutorials/getting-started/`
- AI Markdown: `/tutorials/getting-started.md`
- build output:
  - `dist/tutorials/getting-started/index.html`
  - `dist/tutorials/getting-started.md`

The default canonical style is trailing slash for HTML, because the generated site is directory-based and relative asset handling is more stable with `/slug/`.

## Build pipeline

Input:

- `articles/**/*.md`
- Jinja templates
- static assets
- optional files from `verification/`

Output:

- article HTML
- article Markdown copies
- homepage
- optional explorer
- `feed.xml`
- `sitemap.xml`
- `llms.txt`
- `robots.txt`

Production servers do not run Python. They only serve static files produced by `build.py`.

## Metadata normalization

The builder normalizes frontmatter before rendering:

- `date` and `updated` become stable `YYYY-MM-DD` strings
- `author` can be a string or list
- `tags` are normalized into a list
- `faq` is normalized into a safe list of `{q, a}` pairs

This normalized metadata is then used for:

- article templates
- Atom feed
- sitemap
- `llms.txt`
- JSON-LD structured data

## Structured data model

JSON-LD is built in Python and serialized with `json.dumps`, then injected into templates as a ready-made string.

This avoids fragile template interpolation when titles, descriptions, or FAQ answers contain:

- quotes
- newlines
- punctuation that would otherwise break inline JSON

The template emits:

- article pages: `Article` + `BreadcrumbList`, optionally `FAQPage`
- homepage: `WebSite` + `Organization` + `ItemList`

## Markdown rendering model

Janus-MD intentionally avoids a vendor bootstrap step.

### Emoji

Emoji shortcodes such as `:rocket:` are converted at build time via `pymdownx.emoji`.

### Math

Math is preserved as MathJax-compatible markup via `pymdownx.arithmatex`.

At runtime:

- `static/js/main.js` loads MathJax on demand only when `.arithmatex` content exists
- article pages and explorer previews both reuse the same shared renderer

This keeps the default path light while still supporting formulas.

## Explorer behavior

Explorer is configurable:

```toml
[explorer]
enabled = true
expose_in_nav = true
```

Rules:

- if `enabled = true`, build `/explorer/`
- if `expose_in_nav = false`, the page is generated but hidden from top nav
- explorer is always excluded from sitemap, feed, and `llms.txt`
- explorer always emits:
  - `noindex`
  - `nofollow`
  - `noarchive`

The explorer is intended as an internal browsing utility, not a discovery surface.

## Discovery layer

Janus-MD emits four discovery files:

- `sitemap.xml` for search engines
- `feed.xml` for RSS / Atom readers
- `llms.txt` for AI-aware discovery
- `robots.txt` for crawler hints

Semantics:

- all human-facing article URLs use `/slug/`
- all machine-facing article URLs use `/slug.md`
- Atom entry HTML links and IDs use `/slug/`
- `llms.txt` points to `.md` URLs

## Gateway semantics

Routing happens at the gateway, not in the static files.

### Human requests

- `/slug` -> `301` -> `/slug/`
- `/slug/` -> HTML

### AI / Markdown requests

Either signal is enough:

- recognized AI crawler `User-Agent`
- `Accept: text/markdown`

Behavior:

- `/slug` -> Markdown `200`
- `/slug/` -> Markdown `200`
- `/slug.md` -> Markdown `200`

Missing paths must return real `404`, not a homepage fallback.

## Nginx pattern

The shipped Nginx example uses:

- `map` to precompute AI / markdown intent
- `@markdown` and `@html` named locations
- canonical redirect only for normal HTML requests

The slash redirect is explicit:

```nginx
return 301 https://$host$canonical_redirect;
```

This avoids accidental `Location: http://...` responses when TLS is terminated upstream.

## Cloudflare guidance

If the Cloudflare Worker owns routing:

- keep slash canonicalization in the Worker
- do not duplicate it with Redirect Rules

If Nginx owns routing:

- disable overlapping Cloudflare Redirect Rules

Duplicate canonical redirects at the edge are a common cause of AI requests being redirected to HTML canonical URLs before Markdown negotiation can happen.
