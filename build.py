#!/usr/bin/env python3
"""Janus-MD Static Site Builder

Reads Markdown articles with YAML frontmatter from a (possibly nested)
articles directory and generates:

  - dist/<slug>/index.html      HTML for humans
  - dist/<slug>.md              Markdown for AI (verbatim copy)
  - dist/index.html             Article listing
  - dist/feed.xml               Atom 1.0 feed
  - dist/sitemap.xml            Search-engine sitemap
  - dist/llms.txt               AI agent discovery (llmstxt.org)
  - dist/robots.txt             Crawler directives

Custom Markdown features:
  - Task markers: [ ] [-] [x] [!] [~]  rendered as styled badges
  - Recursive article discovery (articles/2026/03/post.md → slug: 2026/03/post)
"""

import os
import re
import shutil
import tomllib
from html import escape as html_escape
from datetime import datetime, timezone
from pathlib import Path

import markdown
from markdown import Extension
from markdown.treeprocessors import Treeprocessor
import xml.etree.ElementTree as etree
import yaml
from jinja2 import Environment, FileSystemLoader

# ── Load config ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "janus.config.toml"

with open(CONFIG_FILE, "rb") as f:
    _cfg = tomllib.load(f)

SITE_URL         = os.environ.get("SITE_URL", _cfg["site"]["url"])
SITE_NAME        = _cfg["site"]["name"]
SITE_DESCRIPTION = _cfg["site"]["description"]
SITE_LANGUAGE    = _cfg["site"].get("language", "en")
SITE_AUTHOR      = _cfg["site"].get("author", "")

ARTICLES_DIR     = BASE_DIR / _cfg["build"]["articles_dir"]
TEMPLATES_DIR    = BASE_DIR / _cfg["build"]["templates_dir"]
STATIC_DIR       = BASE_DIR / _cfg["build"]["static_dir"]
DIST_DIR         = BASE_DIR / _cfg["build"]["dist_dir"]
FEED_MAX         = _cfg["feed"].get("max_entries", 20)
MD_EXTENSIONS    = _cfg["markdown"]["extensions"]


# ── Custom Markdown Extension: Task Status Markers ───────────────────────────
# Transforms [ ] [-] [x] [!] [~] at the start of list items or standalone text.
#
# Marker  Meaning      CSS class
# [ ]     未开始       task-todo
# [-]     进行中       task-wip
# [x]     已完成       task-done
# [!]     阻塞中       task-blocked
# [~]     延后/放弃    task-deferred

_TASK_PATTERN = re.compile(
    r"\[(?P<mark> |-|x|!|~)\]",
    re.IGNORECASE,
)
_MARK_MAP = {
    " ": ("task-todo",     "未开始"),
    "-": ("task-wip",      "进行中"),
    "x": ("task-done",     "已完成"),
    "!": ("task-blocked",  "阻塞中"),
    "~": ("task-deferred", "延后/放弃"),
}


class TaskStatusTreeprocessor(Treeprocessor):
    """Replace task markers with styled <span> badges.

    Uses an explicit iterative stack instead of recursion to avoid
    RecursionError on large documents.  Newly-inserted <span> nodes are
    tracked in `_seen` so they are never re-processed.
    """

    def run(self, root: etree.Element) -> None:
        # Collect all pre-existing elements via BFS first, then process.
        # This prevents infinite loops from walking nodes we just inserted.
        queue: list[etree.Element] = [root]
        elements: list[etree.Element] = []
        while queue:
            el = queue.pop(0)
            elements.append(el)
            queue.extend(list(el))

        for el in elements:
            self._process_element(el)

    def _process_element(self, el: etree.Element) -> None:
        """Inject span badges into el.text and each child.tail."""
        # --- el.text ---
        if el.text and "[" in el.text:
            before, span = self._make_span(el.text)
            if span is not None:
                el.text = before
                el.insert(0, span)

        # --- child.tail (must snapshot list to avoid mutation issues) ---
        for child in list(el):
            tail = child.tail
            if tail and "[" in tail:
                before, span = self._make_span(tail)
                if span is not None:
                    child.tail = before
                    parent_children = list(el)
                    pos = parent_children.index(child) + 1
                    el.insert(pos, span)

    def _make_span(self, text: str) -> tuple[str, "etree.Element | None"]:
        """Return (text_before_marker, span_element | None)."""
        m = _TASK_PATTERN.search(text)
        if not m:
            return text, None
        mark = m.group("mark").lower()
        css_cls, label = _MARK_MAP.get(mark, ("task-todo", "?"))
        before = text[: m.start()]
        after  = text[m.end() :]
        span = etree.Element("span")
        span.set("class", f"task-marker {css_cls}")
        span.set("title", label)
        span.text = f"[{m.group('mark')}]"
        span.tail = after if after else None
        return before, span


class TaskStatusExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(
            TaskStatusTreeprocessor(md), "task_status", 5
        )


# ── Frontmatter parser ────────────────────────────────────────────────────────

_FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (meta_dict, body_text)."""
    m = _FM_PATTERN.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]
    # Normalize date
    d = meta.get("date")
    if isinstance(d, datetime):
        meta["date"] = d.strftime("%Y-%m-%d")
    elif d is not None and not isinstance(d, str):
        meta["date"] = str(d)
    return meta, body


# ── Markdown converter ────────────────────────────────────────────────────────

def build_md_converter() -> markdown.Markdown:
    extensions = list(MD_EXTENSIONS) + [TaskStatusExtension()]
    return markdown.Markdown(
        extensions=extensions,
        extension_configs={
            "codehilite": {
                "css_class": "codehilite",
                "guess_lang": False,
                "use_pygments": True,
            },
            "toc": {
                "permalink": False,
            },
        },
    )


# ── Article loader (recursive) ────────────────────────────────────────────────

def slug_from_path(md_file: Path) -> str:
    """
    Derive a URL slug from the file path relative to ARTICLES_DIR.

    articles/hello-world.md            → hello-world
    articles/2026/03/my-post.md        → 2026/03/my-post
    """
    rel = md_file.relative_to(ARTICLES_DIR)
    parts = list(rel.parts)
    parts[-1] = Path(parts[-1]).stem   # strip .md
    return "/".join(parts)


def load_articles() -> list[dict]:
    """Recursively load all non-draft articles, sorted by date descending."""
    articles = []
    for md_file in sorted(ARTICLES_DIR.rglob("*.md")):
        raw = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        if meta.get("draft", False):
            continue
        slug = slug_from_path(md_file)
        md = build_md_converter()
        html_content = md.convert(body)
        articles.append(
            {
                "slug": slug,
                "meta": meta,
                "body": body,
                "raw": raw,
                "html": html_content,
                "source_file": md_file,
            }
        )
    articles.sort(key=lambda a: a["meta"].get("date", ""), reverse=True)
    return articles


# ── Discovery file generators ─────────────────────────────────────────────────

def generate_sitemap(articles: list[dict]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"  <url><loc>{SITE_URL}/</loc></url>",
    ]
    for a in articles:
        date = a["meta"].get("date", "")
        lastmod = f"<lastmod>{date}</lastmod>" if date else ""
        lines.append(f"  <url><loc>{SITE_URL}/{a['slug']}</loc>{lastmod}</url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def generate_atom_feed(articles: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = []
    for a in articles[:FEED_MAX]:
        title   = html_escape(a["meta"].get("title", a["slug"]))
        date    = a["meta"].get("date", "")
        updated = f"{date}T00:00:00Z" if date else now
        author  = html_escape(a["meta"].get("author", SITE_AUTHOR))
        summary = html_escape(a["meta"].get("description", ""))
        link    = f"{SITE_URL}/{a['slug']}"
        content = html_escape(a["html"])
        entries.append(f"""  <entry>
    <title>{title}</title>
    <link href="{link}" rel="alternate" type="text/html"/>
    <link href="{SITE_URL}/{a['slug']}.md" rel="alternate" type="text/markdown"/>
    <id>{link}</id>
    <updated>{updated}</updated>
    <author><name>{author}</name></author>
    <summary>{summary}</summary>
    <content type="html">{content}</content>
  </entry>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{html_escape(SITE_NAME)}</title>
  <subtitle>{html_escape(SITE_DESCRIPTION)}</subtitle>
  <link href="{SITE_URL}/" rel="alternate" type="text/html"/>
  <link href="{SITE_URL}/feed.xml" rel="self" type="application/atom+xml"/>
  <id>{SITE_URL}/</id>
  <updated>{now}</updated>
{chr(10).join(entries)}
</feed>
"""


def generate_llms_txt(articles: list[dict]) -> str:
    lines = [f"# {SITE_NAME}", "", f"> {SITE_DESCRIPTION}", "", "## Articles", ""]
    for a in articles:
        title = a["meta"].get("title", a["slug"])
        desc  = a["meta"].get("description", "")
        suffix = f": {desc}" if desc else ""
        lines.append(f"- [{title}](/{a['slug']}.md){suffix}")
    return "\n".join(lines) + "\n"


def generate_robots_txt() -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml

# AI agent content discovery — https://llmstxt.org/
# Llms-Txt: {SITE_URL}/llms.txt
"""


# ── Main build ────────────────────────────────────────────────────────────────

def build():
    print(f"🔨 Building {SITE_NAME} …")
    print(f"   Articles : {ARTICLES_DIR}")
    print(f"   Output   : {DIST_DIR}")
    print()

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    articles = load_articles()
    print(f"📝 Found {len(articles)} article(s):")
    for a in articles:
        print(f"   • {a['slug']}  —  {a['meta'].get('title', '(no title)')}")
    print()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    # Expose site-wide variables to all templates
    env.globals.update(
        site_name=SITE_NAME,
        site_description=SITE_DESCRIPTION,
        site_url=SITE_URL,
        site_language=SITE_LANGUAGE,
        site_author=SITE_AUTHOR,
    )

    # ── Per-article outputs ───────────────────────────────────────────────────
    for a in articles:
        slug = a["slug"]

        # HTML: dist/<slug>/index.html  (supports nested slugs)
        html_dir = DIST_DIR / slug
        html_dir.mkdir(parents=True, exist_ok=True)
        tmpl = env.get_template("article.html")
        html = tmpl.render(meta=a["meta"], slug=slug, content=a["html"])
        (html_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"   ✅ {slug}/index.html")

        # Markdown: dist/<slug>.md
        md_path = DIST_DIR / f"{slug}.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(a["raw"], encoding="utf-8")
        print(f"   ✅ {slug}.md")

    print()

    # ── Global outputs ────────────────────────────────────────────────────────
    index_tmpl = env.get_template("index.html")
    (DIST_DIR / "index.html").write_text(
        index_tmpl.render(articles=articles), encoding="utf-8"
    )
    print("   ✅ index.html")

    (DIST_DIR / "sitemap.xml").write_text(generate_sitemap(articles), encoding="utf-8")
    print("   ✅ sitemap.xml")

    (DIST_DIR / "feed.xml").write_text(generate_atom_feed(articles), encoding="utf-8")
    print("   ✅ feed.xml")

    (DIST_DIR / "llms.txt").write_text(generate_llms_txt(articles), encoding="utf-8")
    print("   ✅ llms.txt")

    (DIST_DIR / "robots.txt").write_text(generate_robots_txt(), encoding="utf-8")
    print("   ✅ robots.txt")

    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, DIST_DIR / "assets")
        print("   ✅ assets/")

    print()
    print(f"🎉 Build complete! {len(articles)} article(s) → {DIST_DIR}")


if __name__ == "__main__":
    build()
