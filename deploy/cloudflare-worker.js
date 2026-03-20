// ── Janus-MD Cloudflare Worker ──
// Deploy options:
//   A) Cloudflare Pages: place as `_worker.js` in the dist output directory
//   B) Workers & Pages dashboard: paste as a standalone Worker script
//   C) Wrangler CLI: wrangler deploy

const AI_UA = /chatgpt-user|gptbot|oai-searchbot|claudebot|anthropic-ai|perplexitybot|ccbot|bytespider|google-extended|applebot-extended|meta-externalagent/i;
const STATIC_ASSET = /\.(css|js|png|jpg|jpeg|gif|svg|ico|webp|woff2?|ttf|eot|otf|map)$/i;

function withHeaders(sourceHeaders, overrides) {
  const headers = new Headers(sourceHeaders);
  Object.entries(overrides).forEach(([key, value]) => headers.set(key, value));
  return headers;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const ua = request.headers.get('user-agent') || '';
    const accept = request.headers.get('accept') || '';
    const isAI = AI_UA.test(ua) || accept.includes('text/markdown');

    if (!isAI && path !== '/' && !path.endsWith('/') && !path.includes('.')) {
      url.pathname = `${path}/`;
      return Response.redirect(url.toString(), 301);
    }

    if (STATIC_ASSET.test(path)) {
      return env.ASSETS.fetch(request);
    }

    if (/^\/(feed\.xml|sitemap\.xml|llms\.txt|robots\.txt)$/.test(path)) {
      return env.ASSETS.fetch(request);
    }

    if (path.endsWith('.md')) {
      const response = await env.ASSETS.fetch(request);
      if (response.ok) {
        return new Response(response.body, {
          status: response.status,
          headers: withHeaders(response.headers, {
            'Content-Type': 'text/markdown; charset=utf-8',
            'X-Content-Source': 'markdown',
            'X-Robots-Tag': 'noindex',
            'Cache-Control': 'public, max-age=3600',
            'Vary': 'Accept, User-Agent',
          }),
        });
      }
      return response;
    }

    if (isAI) {
      const slug = path.replace(/\/$/, '') || '/index';
      const markdownUrl = new URL(`${slug}.md`, url.origin);
      const response = await env.ASSETS.fetch(new Request(markdownUrl, request));

      if (response.ok) {
        return new Response(response.body, {
          status: 200,
          headers: withHeaders(response.headers, {
            'Content-Type': 'text/markdown; charset=utf-8',
            'X-Content-Source': 'markdown',
            'X-Robots-Tag': 'noindex',
            'Cache-Control': 'public, max-age=3600',
            'Vary': 'Accept, User-Agent',
          }),
        });
      }
    }

    return env.ASSETS.fetch(request);
  },
};
