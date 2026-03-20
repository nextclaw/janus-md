# Janus-MD

> 双态静态网站模板：对人类返回 HTML，对 AI 返回 Markdown。

[![Build & Publish](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Janus-MD 会为同一篇文章生成两种输出：

- `/<slug>/index.html`：浏览器和传统爬虫使用的 HTML
- `/<slug>.md`：AI agent、RAG pipeline、MCP 工具可直接读取的 Markdown

模板默认的人类 canonical URL 风格是 `/<slug>/`，机器侧保持 `/<slug>.md`。

## 功能特性

- 单一 Markdown 源同时生成 HTML + Markdown
- 递归扫描 `articles/**`，支持多级 slug
- 内置 `pymdownx.emoji`，构建期把 `:rocket:` 之类短码转成 Unicode emoji
- 内置 `pymdownx.arithmatex`，运行时按需加载 MathJax
- 任务状态标记 `[ ]` `[-]` `[x]` `[!]` `[~]`
- 可配置的内部 Explorer 页面
- `feed.xml`、`sitemap.xml`、`llms.txt`、`robots.txt`
- 内置 Nginx 和 Cloudflare Worker 网关样例
- GitHub Actions -> `sites` 分支的发布流
- 不再需要 npm / vendor bootstrap

## 快速开始

```bash
git clone https://github.com/nextclaw/janus-md.git my-site
cd my-site
uv run -- python build.py
cd dist && python3 -m http.server 8080
```

详细文档：

- [docs/QUICKSTART.md](docs/QUICKSTART.md)
- [docs/TEMPLATE-SETUP.md](docs/TEMPLATE-SETUP.md)
- [docs/DEPLOY.md](docs/DEPLOY.md)
- [docs/DESIGN.md](docs/DESIGN.md)
- [docs/production-validation-sop.md](docs/production-validation-sop.md)

## 项目结构

```text
janus-md/
├── articles/
├── templates/
├── static/
├── deploy/
├── docs/
├── verification/
├── build.py
├── janus.config.toml
└── pyproject.toml
```

## Frontmatter 示例

```yaml
---
title: "文章标题"
date: 2026-03-20
updated: 2026-03-21
description: "一句话摘要"
author:
  - "作者"
  - "编辑"
tags: [tag1, tag2]
faq:
  - q: "问题？"
    a: "答案。"
draft: false
cover: /assets/img/cover.jpg
---
```

## 补充说明

- Explorer 可以生成但不暴露在导航里
- 放在 `verification/` 的验证文件会原样复制到站点根目录
- slash canonicalization 和 AI 协商逻辑应只由一层网关负责，不要在 Cloudflare 和 Nginx 重复实现

English version: [README.md](README.md)
