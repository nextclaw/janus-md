/**
 * Markdown Emoji Shortcodes → Unicode (DOM post-processor)
 * - Replaces :shortcode: using a provided emoji map and optional aliases
 * - Skips code/pre/kbd/script/style, MathJax output (MJX-*), and .math-block by default
 */

/**
 * Normalize various emoji mapping formats to a flat {":name:": "😊", "name": "😊"} map.
 * Supports:
 * 1) {":smile:": { unicode: "1f604", unicode_alt?: "1f604" }, ...}
 * 2) {"smile": "😄", ...}
 * 3) [{shortcode:"smile", emoji:"😄"}, ...]
 * @param {any} data
 * @returns {Record<string,string>}
 */
export function normalizeEmojiData(data){
  const out = Object.create(null);
  if (!data) return out;
  if (Array.isArray(data)){
    for (const it of data){
      if (it && typeof it.shortcode === 'string' && typeof it.emoji === 'string'){
        addMapping(out, it.shortcode, it.emoji);
      }
    }
    return out;
  }
  if (data && typeof data === 'object'){
    const values = Object.values(data);
    const looksObject = values.length && typeof values[0] === 'object' && values[0] !== null && ('unicode' in values[0] || 'unicode_alt' in values[0]);
    if (looksObject){
      for (const [k, v] of Object.entries(data)){
        if (!v) continue;
        const raw = v.unicode_alt || v.unicode;
        if (typeof raw === 'string') addMapping(out, k, unicodeSeqToChar(raw));
      }
      return out;
    }
    for (const [k, v] of Object.entries(data)){
      if (typeof v === 'string') addMapping(out, k, v);
    }
  }
  return out;
}

/**
 * Normalize alias mapping to a flat {":alias:": ":canonical:"} object.
 * Accepts {":a:": ":b:"} or [{alias:":a:", to:":b:"}]
 * @param {any} data
 * @returns {Record<string,string>}
 */
export function normalizeAliases(data){
  const out = Object.create(null);
  if (!data) return out;
  if (Array.isArray(data)){
    for (const it of data){
      if (it && typeof it.alias === 'string' && typeof it.to === 'string')
        addAliasMapping(out, it.alias, it.to);
    }
    return out;
  }
  if (data && typeof data === 'object'){
    for (const [k, v] of Object.entries(data)) if (typeof v === 'string') addAliasMapping(out, k, v);
  }
  return out;
}

/**
 * Apply emoji shortcodes replacement on a DOM subtree.
 * @param {ParentNode} root - container element whose descendant text nodes will be scanned
 * @param {Object} options
 * @param {Record<string,string>} options.emojiMap - mapping of shortcode to emoji (supports keys with/without colons)
 * @param {Record<string,string>} [options.aliases] - alias mapping {":a:": ":b:"}
 * @param {boolean} [options.skipMath=true] - skip MathJax output and .math-block
 * @param {string[]} [options.skipSelectors] - extra CSS selectors to skip (elements matching any of these are skipped)
 */
export function applyEmojiShortcodes(root, {emojiMap, aliases = {}, skipMath = true, skipSelectors = []} = {}){
  if (!root || !emojiMap) return;
  const SKIP_TAGS = new Set(['CODE','PRE','KBD','SCRIPT','STYLE']);
  const extraSkips = Array.isArray(skipSelectors) ? skipSelectors : [];
  const re = /(:[+\-\w]+:)/gi;
  const testRe = /(:[+\-\w]+:)/i;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) => {
      let p = node.parentElement;
      while (p){
        if (SKIP_TAGS.has(p.tagName)) return NodeFilter.FILTER_REJECT;
        if (skipMath && ((p.classList && p.classList.contains('math-block')) || /^MJX-/.test(p.tagName))) return NodeFilter.FILTER_REJECT;
        if (shouldSkipBySelector(p, extraSkips)) return NodeFilter.FILTER_REJECT;
        p = p.parentElement;
      }
      return testRe.test(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
    }
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const n of nodes){
    n.nodeValue = n.nodeValue.replace(re, (m) => {
      const key = ensureColon(m);
      const canonical = aliases[key] || aliases[key.slice(1,-1)] || m;
      const ckey = ensureColon(canonical);
      return emojiMap[ckey] || emojiMap[ckey.slice(1,-1)] || emojiMap[m] || emojiMap[m.slice(1,-1)] || m;
    });
  }
}

// Packaged defaults (async import of JSON, works in modern bundlers/browsers)
export async function loadDefaultEmojiData(){
  // Try JSON import assertion (modern browsers/bundlers), fallback to fetch
  try{ const mod = await import('./data/emoji-unicodes.json', { assert: { type: 'json' } }); return mod.default; }catch{}
  try{ const url = new URL('./data/emoji-unicodes.json', import.meta.url); const r = await fetch(url); if (r.ok) return await r.json(); }catch{}
  return {};
}
export async function loadDefaultAliasesData(){
  try{ const mod = await import('./data/emoji-aliases.json', { assert: { type: 'json' } }); return mod.default; }catch{}
  try{ const url = new URL('./data/emoji-aliases.json', import.meta.url); const r = await fetch(url); if (r.ok) return await r.json(); }catch{}
  return {};
}
export async function loadDefaultEmojiMap(){
  const data = await loadDefaultEmojiData();
  return normalizeEmojiData(data);
}

// helpers
function shouldSkipBySelector(el, selectors){
  if (!selectors.length) return false;
  try { return el.matches(selectors.join(',')); } catch { return false; }
}

function addMapping(map, key, value){
  const withColon = key.startsWith(':') && key.endsWith(':') ? key : `:${key}:`;
  const noColon = withColon.slice(1, -1);
  map[withColon] = value;
  map[noColon] = value;
}

function unicodeSeqToChar(seq){
  return seq.split('-').map(h => String.fromCodePoint(parseInt(h, 16))).join('');
}

function addAliasMapping(map, alias, target){
  const ak = ensureColon(alias);
  const tv = ensureColon(target);
  map[ak] = tv;
  map[ak.slice(1,-1)] = tv;
}

function ensureColon(s){
  if (!s) return s;
  const hasStart = s[0] === ':';
  const hasEnd = s[s.length-1] === ':';
  if (hasStart && hasEnd) return s;
  return `:${String(s).replace(/^:+|:+$/g,'')}:`;
}
