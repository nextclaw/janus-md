// ── Janus-MD Cloudflare Worker ──
// Deploy options:
//   A) Cloudflare Pages: place as `_worker.js` in dist output directory
//   B) Workers & Pages dashboard: paste as a standalone Worker script
//   C) Wrangler CLI: wrangler deploy

const AI_UA = /chatgpt-user|gptbot|oai-searchbot|claudebot|anthropic-ai|perplexitybot|ccbot|bytespider|google-extended|applebot-extended|meta-externalagent/i;

/** Static asset extensions — pass through without UA inspection */
const ASSET_RE = /\.(css|js|png|jpg|jpeg|gif|svg|ico|webp|woff2?|ttf|eot|map)$/i;

export default {
  async fetch(request, env) {
    const url  = new URL(request.url);
    const path = url.pathname;

    // 1. Static assets → pass through (no UA negotiation)
    if (ASSET_RE.test(path)) {
      return env.ASSETS.fetch(request);
    }

    // 2. Discovery files → pass through
    if (/^\/(feed\.xml|sitemap\.xml|llms\.txt|robots\.txt)$/.test(path)) {
      return env.ASSETS.fetch(request);
    }

    // 3. Explicit .md requests → serve with correct Content-Type
    if (path.endsWith('.md')) {
      const res = await env.ASSETS.fetch(request);
      if (res.ok) {
        return new Response(res.body, {
          status: res.status,
          headers: {
            ...Object.fromEntries(res.headers),
            'Content-Type': 'text/markdown; charset=utf-8',
            'X-Content-Source': 'markdown',
            'Cache-Control': 'public, max-age=3600',
          },
        });
      }
      return res;
    }

    // 4. Content negotiation for article pages
    const ua     = request.headers.get('user-agent') || '';
    const accept = request.headers.get('accept')      || '';
    const isAI   = AI_UA.test(ua) || accept.includes('text/markdown');

    if (isAI) {
      // Map clean URL → .md counterpart
      const slug  = path.replace(/\/$/, '') || '/index';
      const mdUrl = new URL(`${slug}.md`, url.origin);
      const res   = await env.ASSETS.fetch(new Request(mdUrl.toString()));

      if (res.ok) {
        return new Response(res.body, {
          status: 200,
          headers: {
            'Content-Type': 'text/markdown; charset=utf-8',
            'X-Content-Source': 'markdown',
            'X-Robots-Tag': 'noindex',
            'Cache-Control': 'public, max-age=3600',
          },
        });
      }
      // .md not found → fall through to HTML
    }

    // 5. Default: serve HTML
    return env.ASSETS.fetch(request);
  },
};
