#!/usr/bin/env python3
from __future__ import annotations

"""Janus-MD Static Site Builder.

Reads Markdown articles with YAML frontmatter from a recursive articles tree and
generates:

  - dist/<slug>/index.html      HTML for humans
  - dist/<slug>.md              Markdown for AI agents
  - dist/index.html             Article listing
  - dist/explorer/index.html    Optional internal article explorer
  - dist/feed.xml               Atom 1.0 feed
  - dist/sitemap.xml            Search-engine sitemap
  - dist/llms.txt               AI discovery file
  - dist/robots.txt             Crawler hints
"""

import hashlib
import json
import os
import posixpath
import re
import shutil
import tomllib
import xml.etree.ElementTree as etree
from datetime import date, datetime, timezone
from html import escape as html_escape
from pathlib import Path

import markdown
import pymdownx.emoji
import yaml
from jinja2 import Environment, FileSystemLoader
from markdown import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor


# ── Load configuration ──────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "janus.config.toml"

with open(CONFIG_FILE, "rb") as config_file:
    _cfg = tomllib.load(config_file)

SITE_URL = os.environ.get("SITE_URL", _cfg["site"]["url"]).rstrip("/")
SITE_NAME = _cfg["site"]["name"]
SITE_DESCRIPTION = _cfg["site"]["description"]
SITE_LANGUAGE = _cfg["site"].get("language", "en")
SITE_AUTHOR = _cfg["site"].get("author", "")
SITE_LOGO_LETTER = SITE_NAME[:1].upper() if SITE_NAME else "J"

ARTICLES_DIR = BASE_DIR / _cfg["build"]["articles_dir"]
TEMPLATES_DIR = BASE_DIR / _cfg["build"]["templates_dir"]
STATIC_DIR = BASE_DIR / _cfg["build"]["static_dir"]
DIST_DIR = BASE_DIR / _cfg["build"]["dist_dir"]
VERIFICATION_DIR = BASE_DIR / _cfg["build"].get("verification_dir", "verification")
PAGES_DIR = BASE_DIR / _cfg["build"].get("pages_dir", "pages")

FEED_MAX = _cfg["feed"].get("max_entries", 20)
MD_EXTENSIONS = _cfg["markdown"]["extensions"]

_theme_cfg = _cfg.get("theme", {})
THEME_CSS_PATH = _theme_cfg.get("theme_css", "")
CUSTOM_CSS_PATH = _theme_cfg.get("custom_css", "")

_explorer_cfg = _cfg.get("explorer", {})
EXPLORER_ENABLED = bool(_explorer_cfg.get("enabled", True))
EXPLORER_EXPOSE_IN_NAV = EXPLORER_ENABLED and bool(
    _explorer_cfg.get("expose_in_nav", True)
)

_task_cfg = _cfg.get("task_markers", {})
TASK_MARKER_STYLE = _task_cfg.get("style", "text")  # "text" | "emoji"

_index_cfg = _cfg.get("index", {})
INDEX_PAGINATE = bool(_index_cfg.get("paginate", False))
INDEX_PER_PAGE = int(_index_cfg.get("per_page", 50))

_article_cfg = _cfg.get("article", {})
ARTICLE_TOC_LINK = bool(_article_cfg.get("toc_link", False))

_features_cfg = _cfg.get("features", {})
FEATURE_TOC = bool(_features_cfg.get("toc", False))
FEATURE_RATING = bool(_features_cfg.get("rating", False))
FEATURE_LASTMOD = bool(_features_cfg.get("lastmod", False))
FEATURE_COVER = bool(_features_cfg.get("cover", False))
FEATURE_MATH = bool(_features_cfg.get("math", True))
FEATURE_MERMAID = bool(_features_cfg.get("mermaid", True))

_categories_cfg = _cfg.get("categories", {})
CATEGORIES_EXPOSE_IN_NAV = bool(_categories_cfg.get("expose_in_nav", False))

_tags_cfg = _cfg.get("tags", {})
TAGS_ENABLED = bool(_tags_cfg.get("enabled", False))


# ── Custom Markdown Extension: Task Status Markers ─────────────────────────

_TASK_PATTERN = re.compile(r"\[(?P<mark> |-|x|!|~)\]", re.IGNORECASE)
_MARK_MAP = {
    " ": ("task-todo", "未开始"),
    "-": ("task-wip", "进行中"),
    "x": ("task-done", "已完成"),
    "!": ("task-blocked", "阻塞中"),
    "~": ("task-deferred", "延后/放弃"),
}
_EMOJI_MAP = {
    " ": "🔲",
    "-": "🔄",
    "x": "✅",
    "!": "🚫",
    "~": "⏸️",
}


class TaskStatusTreeprocessor(Treeprocessor):
    """Replace task markers with styled span badges."""

    def run(self, root: etree.Element) -> None:
        queue: list[etree.Element] = [root]
        elements: list[etree.Element] = []
        while queue:
            element = queue.pop(0)
            elements.append(element)
            queue.extend(list(element))

        for element in elements:
            self._process_element(element)

    def _process_element(self, element: etree.Element) -> None:
        if element.text and "[" in element.text:
            before, span = self._make_span(element.text)
            if span is not None:
                element.text = before
                element.insert(0, span)

        for child in list(element):
            tail = child.tail
            if tail and "[" in tail:
                before, span = self._make_span(tail)
                if span is not None:
                    child.tail = before
                    siblings = list(element)
                    insert_at = siblings.index(child) + 1
                    element.insert(insert_at, span)

    def _make_span(self, text: str) -> tuple[str, etree.Element | None]:
        match = _TASK_PATTERN.search(text)
        if not match:
            return text, None

        mark = match.group("mark").lower()
        css_class, label = _MARK_MAP.get(mark, ("task-todo", "?"))
        span = etree.Element("span")

        if TASK_MARKER_STYLE == "emoji":
            emoji_char = _EMOJI_MAP.get(mark, "🔲")
            span.set("class", "task-marker-emoji")
            span.set("title", label)
            span.text = emoji_char
        else:
            span.set("class", f"task-marker {css_class}")
            span.set("title", label)
            span.text = f"[{match.group('mark')}]"

        span.tail = text[match.end() :] or None
        return text[: match.start()], span


class TaskStatusExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(TaskStatusTreeprocessor(md), "task_status", 5)


# ── Custom Markdown Extension: Mermaid Diagrams ────────────────────────────

_MERMAID_FENCE_RE = re.compile(
    r"^(`{3,})\s*mermaid\s*$\n(.*?)^\1\s*$",
    re.MULTILINE | re.DOTALL,
)


class MermaidPreprocessor(Preprocessor):
    """Convert fenced mermaid code blocks to raw HTML before Markdown processing.

    This runs *before* codehilite / fenced_code, so mermaid blocks never get
    Pygments-highlighted.  The raw diagram source is wrapped in
    ``<pre class="mermaid">…</pre>`` which mermaid.js picks up on the client.
    """

    def run(self, lines: list[str]) -> list[str]:
        text = "\n".join(lines)
        text = _MERMAID_FENCE_RE.sub(self._replace, text)
        return text.split("\n")

    @staticmethod
    def _replace(match: re.Match) -> str:
        diagram = html_escape(match.group(2).strip())
        # Use Markdown's HTML block syntax — a blank-line-separated raw block
        return f'\n<pre class="mermaid">\n{diagram}\n</pre>\n'


class MermaidExtension(Extension):
    def extendMarkdown(self, md):
        # Priority 35 — higher than fenced_code (25) and codehilite (20)
        md.preprocessors.register(MermaidPreprocessor(md), "mermaid", 35)


# ── Custom Markdown Extension: Obsidian Wiki Links ─────────────────────────

_WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]")


class WikiLinkPreprocessor(Preprocessor):
    """Convert Obsidian [[path|title]] links to standard Markdown links.

    Paths are resolved relative to the current article's directory,
    matching Obsidian's behaviour.  Set ``article_dir`` before each
    ``md.convert()`` call.
    """

    def __init__(self, md):
        super().__init__(md)
        self.article_dir: str = ""  # e.g. "5g-technology" for slug "5g-technology/_toc"

    def run(self, lines: list[str]) -> list[str]:
        return [self._process_line(line) for line in lines]

    def _process_line(self, line: str) -> str:
        return _WIKILINK_PATTERN.sub(self._replace_match, line)

    def _replace_match(self, match: re.Match) -> str:
        path = match.group(1).strip()
        title = (match.group(2) or path).strip()
        # Remove .md suffix if present
        if path.endswith(".md"):
            path = path[:-3]
        # Resolve relative paths against current article directory
        if not path.startswith("/"):
            if self.article_dir:
                path = posixpath.normpath(f"{self.article_dir}/{path}")
            # else root-level article, path stays as-is
        # Build URL: ensure leading / and trailing /
        url = path if path.startswith("/") else f"/{path}"
        if not url.endswith("/"):
            url += "/"
        return f"[{title}]({url})"


class WikiLinkExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(WikiLinkPreprocessor(md), "wikilinks", 30)


# ── Metadata helpers ────────────────────────────────────────────────────────

_FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def normalize_date_like(value) -> str | None:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if value is None:
        return None
    return str(value)


def normalize_author_names(author_value) -> list[str]:
    if author_value is None:
        return []
    if isinstance(author_value, list):
        names = [str(name).strip() for name in author_value]
        return [name for name in names if name]

    text = str(author_value).strip()
    if not text:
        return []

    if " & " in text:
        parts = text.split(" & ")
    elif " and " in text:
        parts = text.split(" and ")
    else:
        parts = [text]

    names = [part.strip() for part in parts if part.strip()]
    return names or [text]


def normalize_tags(tags_value) -> list[str]:
    if tags_value is None:
        return []
    if isinstance(tags_value, list):
        tags = [str(tag).strip() for tag in tags_value]
        return [tag for tag in tags if tag]

    text = str(tags_value).strip()
    if not text:
        return []
    if "," in text:
        tags = [part.strip() for part in text.split(",")]
        return [tag for tag in tags if tag]
    return [text]


def normalize_faq_items(faq_value) -> list[dict]:
    if not isinstance(faq_value, list):
        return []

    faq_items: list[dict] = []
    for item in faq_value:
        if not isinstance(item, dict):
            continue
        question = str(item.get("q", "")).strip()
        answer = str(item.get("a", "")).strip()
        if question and answer:
            faq_items.append({"q": question, "a": answer})
    return faq_items


def normalize_rating(rating_value) -> str | None:
    """Convert numeric rating to star string: ⭐️ for full, ☆ for empty."""
    if rating_value is None:
        return None
    try:
        value = float(rating_value)
    except (TypeError, ValueError):
        return None
    if value < 0:
        value = 0
    if value > 5:
        value = 5
    full = int(value)
    empty = 5 - full
    return "⭐" * full + "☆" * empty


def normalize_metadata(meta: dict | None) -> dict:
    normalized = dict(meta or {})

    for key in ("date", "updated", "lastmod"):
        value = normalize_date_like(normalized.get(key))
        if value is None:
            normalized.pop(key, None)
        else:
            normalized[key] = value

    if normalized.get("date"):
        normalized["display_date"] = normalized["date"]
    else:
        normalized["display_date"] = None

    tags = normalize_tags(normalized.get("tags"))
    if tags:
        normalized["tags"] = tags
    else:
        normalized.pop("tags", None)

    faq_items = normalize_faq_items(normalized.get("faq"))
    if faq_items:
        normalized["faq"] = faq_items
    else:
        normalized.pop("faq", None)

    author_names = normalize_author_names(normalized.get("author"))
    if not author_names and SITE_AUTHOR:
        author_names = normalize_author_names(SITE_AUTHOR)
    if author_names:
        normalized["author_names"] = author_names
        normalized["author_display"] = ", ".join(author_names)

    # Rating stars
    if FEATURE_RATING and normalized.get("rating") is not None:
        normalized["rating_stars"] = normalize_rating(normalized["rating"])
    else:
        normalized.pop("rating_stars", None)

    # Category — use as-is from frontmatter (strip, lowercase)
    cat = normalized.get("category")
    if cat:
        normalized["category"] = str(cat).strip().lower()
    else:
        normalized.pop("category", None)

    return normalized


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = _FM_PATTERN.match(text)
    if not match:
        return normalize_metadata({}), text

    raw_yaml = match.group(1)
    meta = yaml.safe_load(raw_yaml) or {}
    body = text[match.end() :]
    return normalize_metadata(meta), body


def format_atom_timestamp(date_value: str | None, fallback: str | None = None) -> str:
    if date_value:
        return f"{date_value}T00:00:00Z"
    if fallback:
        return fallback
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Markdown conversion ─────────────────────────────────────────────────────


def build_markdown_converter() -> markdown.Markdown:
    extensions = list(MD_EXTENSIONS)
    for required_extension in (
        "pymdownx.emoji",
        "pymdownx.arithmatex",
        "pymdownx.mark",
    ):
        if required_extension not in extensions:
            extensions.append(required_extension)
    extensions.append(TaskStatusExtension())
    extensions.append(MermaidExtension())
    extensions.append(WikiLinkExtension())

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
            "pymdownx.emoji": {
                "emoji_generator": pymdownx.emoji.to_alt,
            },
            "pymdownx.arithmatex": {
                "generic": True,
            },
            "pymdownx.mark": {
                "smart_mark": False,
            },
        },
    )


# ── Article loading / tree building ─────────────────────────────────────────


def slug_from_path(md_file: Path) -> str:
    rel = md_file.relative_to(ARTICLES_DIR)
    parts = list(rel.parts)
    parts[-1] = Path(parts[-1]).stem
    return "/".join(parts)


_FIRST_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags and return plain text."""
    return re.sub(r"<[^>]+>", "", html).strip()


def load_articles() -> list[dict]:
    articles: list[dict] = []
    md = build_markdown_converter()
    for md_file in sorted(ARTICLES_DIR.rglob("*.md")):
        raw = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        if meta.get("draft", False):
            continue

        slug = slug_from_path(md_file)
        md.reset()
        # Set article directory context for wiki link resolution
        wikilink_prep = md.preprocessors["wikilinks"]
        slug_dir = posixpath.dirname(slug)
        wikilink_prep.article_dir = slug_dir
        html_content = md.convert(body)

        # Extract TOC HTML generated by python-markdown toc extension
        toc_html = getattr(md, "toc", "")

        # ── Title dedup: remove first <h1> if it matches frontmatter title ──
        title = meta.get("title", "")
        if title:
            first_h1 = _FIRST_H1_RE.search(html_content)
            if first_h1:
                h1_text = _strip_html_tags(first_h1.group(1))
                if h1_text == title:
                    html_content = (
                        html_content[: first_h1.start()]
                        + html_content[first_h1.end() :]
                    )
                    # Also remove the first <li> in TOC that corresponds to this h1
                    if toc_html:
                        toc_html = re.sub(
                            r"<li>\s*<a[^>]*>" + re.escape(title) + r"</a>\s*(?:<ul>)?",
                            lambda m: "<ul>" if m.group(0).endswith("<ul>") else "",
                            toc_html,
                            count=1,
                        )

        # ── Math / Mermaid on-demand detection ──
        # Priority: frontmatter > global config default > content detection
        article_math = meta.get("math")
        if article_math is not None:
            has_math = bool(article_math)
        elif FEATURE_MATH:
            has_math = "arithmatex" in html_content
        else:
            has_math = False

        article_mermaid = meta.get("mermaid")
        if article_mermaid is not None:
            has_mermaid = bool(article_mermaid)
        elif FEATURE_MERMAID:
            has_mermaid = 'class="mermaid"' in html_content
        else:
            has_mermaid = False

        # ── TOC enable: frontmatter toc > global FEATURE_TOC ──
        article_toc = meta.get("toc")
        if article_toc is not None:
            show_toc = bool(article_toc) and bool(toc_html)
        else:
            show_toc = FEATURE_TOC and bool(toc_html)

        articles.append(
            {
                "slug": slug,
                "html_path": f"/{slug}/",
                "markdown_path": f"/{slug}.md",
                "meta": meta,
                "body": body,
                "raw": raw,
                "html": html_content,
                "toc_html": toc_html if show_toc else "",
                "has_math": has_math,
                "has_mermaid": has_mermaid,
                "word_count": len(body.split()),
                "source_file": md_file,
            }
        )

    articles.sort(key=lambda article: article["meta"].get("date", ""), reverse=True)
    return articles


def build_explorer_tree(articles: list[dict]) -> dict:
    root: dict = {"name": "root", "children": []}

    for article in articles:
        parts = article["slug"].split("/")
        node = root
        for folder_name in parts[:-1]:
            child = next(
                (
                    candidate
                    for candidate in node["children"]
                    if candidate.get("name") == folder_name and "children" in candidate
                ),
                None,
            )
            if child is None:
                child = {"name": folder_name, "children": []}
                node["children"].append(child)
            node = child

        leaf_name = parts[-1]
        node["children"].append(
            {
                "name": leaf_name,
                "slug": article["slug"],
                "title": article["meta"].get("title", leaf_name),
                "date": article["meta"].get("date", ""),
            }
        )

    _resolve_folder_titles(root)
    return root


def _resolve_folder_titles(node: dict) -> None:
    """Derive folder display titles from _toc / _index children."""
    if "children" not in node:
        return
    for child in node["children"]:
        if "children" in child:
            # It's a folder — look for _toc or _index child to get title
            for leaf in child["children"]:
                if leaf.get("slug") and leaf.get("name") in ("_toc", "_index"):
                    title = leaf.get("title", "")
                    if title and title != leaf["name"]:
                        child["title"] = title
                    break
            _resolve_folder_titles(child)


# ── Structured data builders ────────────────────────────────────────────────


def build_article_schema(meta: dict, canonical_url: str, word_count: int) -> str:
    author_names = meta.get("author_names") or normalize_author_names(SITE_AUTHOR)
    if not author_names:
        author_schema: dict | list[dict] = {
            "@type": "Organization",
            "@id": f"{SITE_URL}/#organization",
            "name": SITE_NAME,
            "url": f"{SITE_URL}/",
        }
    elif len(author_names) == 1:
        author_schema = {"@type": "Person", "name": author_names[0]}
    else:
        author_schema = [{"@type": "Person", "name": name} for name in author_names]

    graph = [
        {
            "@type": "Article",
            "@id": f"{canonical_url}#article",
            "headline": meta.get("title", ""),
            "description": meta.get("description", ""),
            "url": canonical_url,
            "inLanguage": SITE_LANGUAGE,
            "datePublished": meta.get("date", ""),
            "dateModified": meta.get("updated") or meta.get("date", ""),
            "wordCount": word_count,
            "author": author_schema,
            "publisher": {
                "@type": "Organization",
                "@id": f"{SITE_URL}/#organization",
                "name": SITE_NAME,
                "url": f"{SITE_URL}/",
            },
            "isPartOf": {
                "@type": "WebSite",
                "@id": f"{SITE_URL}/#website",
                "name": SITE_NAME,
                "url": f"{SITE_URL}/",
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": canonical_url,
            },
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": f"{SITE_URL}/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": meta.get("title", ""),
                    "item": canonical_url,
                },
            ],
        },
    ]

    if meta.get("cover"):
        graph[0]["image"] = {
            "@type": "ImageObject",
            "url": meta["cover"],
        }

    faq_items = []
    for item in meta.get("faq", []):
        faq_items.append(
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["a"],
                },
            }
        )
    if faq_items:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": f"{canonical_url}#faq",
                "mainEntity": faq_items,
            }
        )

    return json.dumps(
        {"@context": "https://schema.org", "@graph": graph},
        ensure_ascii=False,
        indent=2,
    )


def build_index_schema(articles: list[dict]) -> str:
    graph = [
        {
            "@type": "WebSite",
            "@id": f"{SITE_URL}/#website",
            "url": f"{SITE_URL}/",
            "name": SITE_NAME,
            "description": SITE_DESCRIPTION,
            "inLanguage": SITE_LANGUAGE,
            "publisher": {
                "@id": f"{SITE_URL}/#organization",
            },
        },
        {
            "@type": "Organization",
            "@id": f"{SITE_URL}/#organization",
            "name": SITE_NAME,
            "url": f"{SITE_URL}/",
            "description": SITE_DESCRIPTION,
        },
        {
            "@type": "ItemList",
            "name": "Article index",
            "numberOfItems": len(articles),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "name": article["meta"].get("title", article["slug"]),
                    "description": article["meta"].get("description", ""),
                    "url": f"{SITE_URL}{article['html_path']}",
                }
                for index, article in enumerate(articles, start=1)
            ],
        },
    ]
    return json.dumps(
        {"@context": "https://schema.org", "@graph": graph},
        ensure_ascii=False,
        indent=2,
    )


# ── Discovery file generation ───────────────────────────────────────────────


def generate_sitemap(articles: list[dict]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"  <url><loc>{SITE_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
    ]
    for index, article in enumerate(articles):
        lastmod_value = article["meta"].get("updated") or article["meta"].get(
            "date", ""
        )
        lastmod = f"<lastmod>{lastmod_value}</lastmod>" if lastmod_value else ""
        priority = "0.9" if index == 0 else "0.8"
        lines.append(
            f"  <url><loc>{SITE_URL}{article['html_path']}</loc>"
            f"{lastmod}<changefreq>monthly</changefreq>"
            f"<priority>{priority}</priority></url>"
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def generate_atom_feed(articles: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    feed_updated = next(
        (
            format_atom_timestamp(article["meta"].get("date"))
            for article in articles
            if article["meta"].get("date")
        ),
        now,
    )

    entries = []
    for article in articles[:FEED_MAX]:
        title = html_escape(article["meta"].get("title", article["slug"]))
        updated = format_atom_timestamp(article["meta"].get("date"), now)
        author_names = (
            article["meta"].get("author_names")
            or normalize_author_names(SITE_AUTHOR)
            or [SITE_NAME]
        )
        author_xml = "\n".join(
            f"    <author><name>{html_escape(name)}</name></author>"
            for name in author_names
        )
        summary = html_escape(article["meta"].get("description", ""))
        link = f"{SITE_URL}{article['html_path']}"
        content_html = html_escape(article["html"])
        entries.append(
            f"""  <entry>
    <title>{title}</title>
    <link href="{link}" rel="alternate" type="text/html"/>
    <link href="{SITE_URL}{article["markdown_path"]}" rel="alternate" type="text/markdown"/>
    <id>{link}</id>
    <updated>{updated}</updated>
{author_xml}
    <summary>{summary}</summary>
    <content type="html">{content_html}</content>
  </entry>"""
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{html_escape(SITE_NAME)}</title>
  <subtitle>{html_escape(SITE_DESCRIPTION)}</subtitle>
  <link href="{SITE_URL}/" rel="alternate" type="text/html"/>
  <link href="{SITE_URL}/feed.xml" rel="self" type="application/atom+xml"/>
  <id>{SITE_URL}/</id>
  <updated>{feed_updated}</updated>
{chr(10).join(entries)}
</feed>
"""


def generate_llms_txt(articles: list[dict]) -> str:
    lines = [
        f"# {SITE_NAME}",
        "",
        f"> {SITE_DESCRIPTION}",
        "",
        "## Articles",
        "",
    ]
    for article in articles:
        title = article["meta"].get("title", article["slug"])
        description = article["meta"].get("description", "")
        suffix = f": {description}" if description else ""
        lines.append(f"- [{title}]({article['markdown_path']}){suffix}")
    return "\n".join(lines) + "\n"


def generate_robots_txt() -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
Llms-Txt: {SITE_URL}/llms.txt
"""


def copy_verification_files() -> None:
    if not VERIFICATION_DIR.exists() or not VERIFICATION_DIR.is_dir():
        return

    for verification_file in sorted(VERIFICATION_DIR.iterdir()):
        if not verification_file.is_file() or verification_file.name.startswith("."):
            continue
        shutil.copy2(verification_file, DIST_DIR / verification_file.name)
        print(f"   ✅ {verification_file.name}")


def copy_pages() -> None:
    if not PAGES_DIR.exists() or not PAGES_DIR.is_dir():
        return

    shutil.copytree(PAGES_DIR, DIST_DIR, dirs_exist_ok=True)
    print(f"   ✅ {PAGES_DIR.name}/ -> ./")


# ── Main build ──────────────────────────────────────────────────────────────


def build():
    print(f"🔨 Building {SITE_NAME}...")
    print(f"   Articles: {ARTICLES_DIR}")
    print(f"   Output:   {DIST_DIR}")
    print()

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    articles = load_articles()
    print(f"📝 Found {len(articles)} article(s):")
    for article in articles:
        print(f"   • {article['slug']} — {article['meta'].get('title', '(no title)')}")
    print()

    # ── Collect categories and tags ──────────────────────────────────────
    category_map: dict[str, list[dict]] = {}
    tag_map: dict[str, list[dict]] = {}
    for article in articles:
        cat = article["meta"].get("category")
        if cat:
            category_map.setdefault(cat, []).append(article)
        for tag in article["meta"].get("tags", []):
            tag_map.setdefault(tag, []).append(article)

    # Category display names: capitalize, sort alphabetically
    nav_categories = sorted(
        [
            {"slug": cat, "name": cat.title(), "count": len(arts)}
            for cat, arts in category_map.items()
        ],
        key=lambda c: c["slug"],
    )

    # Tag stats for tag cloud
    all_tags = sorted(
        [
            {"slug": tag, "name": tag, "count": len(arts)}
            for tag, arts in tag_map.items()
        ],
        key=lambda t: (-t["count"], t["slug"]),
    )

    if nav_categories:
        print(f"📂 Categories: {', '.join(c['slug'] for c in nav_categories)}")
    if all_tags:
        print(f"🏷️  Tags: {len(all_tags)} unique tag(s)")
    if nav_categories or all_tags:
        print()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )

    theme_css_exists = bool(THEME_CSS_PATH) and (BASE_DIR / THEME_CSS_PATH).is_file()
    custom_css_exists = bool(CUSTOM_CSS_PATH) and (BASE_DIR / CUSTOM_CSS_PATH).is_file()

    # Build content-hash for cache-busting static assets
    def _asset_hash(rel_path: str) -> str:
        full = STATIC_DIR / rel_path
        if full.is_file():
            digest = hashlib.sha256(full.read_bytes()).hexdigest()[:8]
            return f"?v={digest}"
        return ""

    asset_hash = {
        "style": _asset_hash("css/style.css"),
        "codehilite": _asset_hash("css/codehilite.css"),
        "theme": _asset_hash("css/theme.css"),
        "custom": _asset_hash("css/custom.css"),
        "main_js": _asset_hash("js/main.js"),
    }

    env.globals.update(
        site_name=SITE_NAME,
        site_description=SITE_DESCRIPTION,
        site_url=SITE_URL,
        site_language=SITE_LANGUAGE,
        site_author=SITE_AUTHOR,
        site_logo_letter=SITE_LOGO_LETTER,
        explorer_enabled=EXPLORER_ENABLED,
        explorer_expose_in_nav=EXPLORER_EXPOSE_IN_NAV,
        theme_css_exists=theme_css_exists,
        custom_css_exists=custom_css_exists,
        asset_hash=asset_hash,
        nav_categories=nav_categories if CATEGORIES_EXPOSE_IN_NAV else [],
        feature_cover=FEATURE_COVER,
        feature_rating=FEATURE_RATING,
        feature_lastmod=FEATURE_LASTMOD,
        tags_enabled=TAGS_ENABLED,
    )

    article_template = env.get_template("article.html")
    for article in articles:
        slug = article["slug"]
        html_dir = DIST_DIR / slug
        html_dir.mkdir(parents=True, exist_ok=True)
        canonical_url = f"{SITE_URL}{article['html_path']}"

        # Resolve _toc link for this article
        toc_url = None
        if ARTICLE_TOC_LINK:
            slug_dir = posixpath.dirname(slug)
            slug_basename = posixpath.basename(slug)
            if slug_dir and slug_basename != "_toc":
                toc_file = ARTICLES_DIR / slug_dir / "_toc.md"
                if toc_file.is_file():
                    toc_url = f"/{slug_dir}/_toc/"

        html = article_template.render(
            meta=article["meta"],
            slug=slug,
            content=article["html"],
            canonical_url=canonical_url,
            structured_data_json=build_article_schema(
                article["meta"],
                canonical_url,
                article["word_count"],
            ),
            word_count=article["word_count"],
            toc_url=toc_url,
            toc_html=article["toc_html"],
            has_mermaid=article["has_mermaid"],
            has_math=article["has_math"],
        )
        (html_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"   ✅ {slug}/index.html")

        markdown_path = DIST_DIR / f"{slug}.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(article["raw"], encoding="utf-8")
        print(f"   ✅ {slug}.md")

    print()

    index_template = env.get_template("index.html")
    if INDEX_PAGINATE and len(articles) > INDEX_PER_PAGE:
        total_pages = (len(articles) + INDEX_PER_PAGE - 1) // INDEX_PER_PAGE
        for page_num in range(1, total_pages + 1):
            start = (page_num - 1) * INDEX_PER_PAGE
            end = start + INDEX_PER_PAGE
            page_articles = articles[start:end]

            prev_url = None
            next_url = None
            if page_num > 1:
                prev_url = "/" if page_num == 2 else f"/page/{page_num - 1}/"
            if page_num < total_pages:
                next_url = f"/page/{page_num + 1}/"

            if page_num == 1:
                canonical_url = f"{SITE_URL}/"
                out_path = DIST_DIR / "index.html"
            else:
                canonical_url = f"{SITE_URL}/page/{page_num}/"
                page_dir = DIST_DIR / "page" / str(page_num)
                page_dir.mkdir(parents=True, exist_ok=True)
                out_path = page_dir / "index.html"

            index_html = index_template.render(
                articles=page_articles,
                canonical_url=canonical_url,
                structured_data_json=build_index_schema(articles),
                page_num=page_num,
                total_pages=total_pages,
                prev_url=prev_url,
                next_url=next_url,
            )
            out_path.write_text(index_html, encoding="utf-8")
            label = "index.html" if page_num == 1 else f"page/{page_num}/index.html"
            print(f"   ✅ {label}")
    else:
        index_html = index_template.render(
            articles=articles,
            canonical_url=f"{SITE_URL}/",
            structured_data_json=build_index_schema(articles),
            page_num=1,
            total_pages=1,
            prev_url=None,
            next_url=None,
        )
        (DIST_DIR / "index.html").write_text(index_html, encoding="utf-8")
        print("   ✅ index.html")

    # ── Category pages ──────────────────────────────────────────────────
    if category_map:
        category_template = env.get_template("category.html")
        for cat_slug, cat_articles in category_map.items():
            cat_dir = DIST_DIR / "category" / cat_slug
            cat_dir.mkdir(parents=True, exist_ok=True)
            cat_html = category_template.render(
                category_name=cat_slug.title(),
                category_slug=cat_slug,
                articles=cat_articles,
                canonical_url=f"{SITE_URL}/category/{cat_slug}/",
            )
            (cat_dir / "index.html").write_text(cat_html, encoding="utf-8")
            print(
                f"   ✅ category/{cat_slug}/index.html ({len(cat_articles)} articles)"
            )

    # ── Tag pages ───────────────────────────────────────────────────────
    if TAGS_ENABLED and tag_map:
        tags_index_template = env.get_template("tags.html")
        tag_detail_template = env.get_template("tag.html")

        tags_dir = DIST_DIR / "tags"
        tags_dir.mkdir(parents=True, exist_ok=True)
        tags_html = tags_index_template.render(
            all_tags=all_tags,
            canonical_url=f"{SITE_URL}/tags/",
        )
        (tags_dir / "index.html").write_text(tags_html, encoding="utf-8")
        print(f"   ✅ tags/index.html ({len(all_tags)} tags)")

        for tag_slug, tag_articles in tag_map.items():
            tag_dir = tags_dir / tag_slug
            tag_dir.mkdir(parents=True, exist_ok=True)
            tag_html = tag_detail_template.render(
                tag_name=tag_slug,
                articles=tag_articles,
                canonical_url=f"{SITE_URL}/tags/{tag_slug}/",
            )
            (tag_dir / "index.html").write_text(tag_html, encoding="utf-8")
        print(f"   ✅ tags/<tag>/index.html ({len(tag_map)} tag pages)")

    if EXPLORER_ENABLED:
        explorer_template = env.get_template("explorer.html")
        explorer_dir = DIST_DIR / "explorer"
        explorer_dir.mkdir(parents=True, exist_ok=True)
        explorer_html = explorer_template.render(
            explorer_tree=build_explorer_tree(articles),
            canonical_url=f"{SITE_URL}/explorer/",
        )
        (explorer_dir / "index.html").write_text(explorer_html, encoding="utf-8")
        print("   ✅ explorer/index.html")

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

    copy_verification_files()
    copy_pages()

    print()
    print(f"🎉 Build complete! {len(articles)} article(s) → {DIST_DIR}")


if __name__ == "__main__":
    build()
