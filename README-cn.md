# Janus-MD

> 双态静态网站模板：对人类返回 HTML，对 AI 返回 Markdown。

[![Build & Publish](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Janus-MD 会为同一篇文章生成两种输出：

- `/<slug>/index.html`：浏览器和传统爬虫使用的 HTML
- `/<slug>.md`：AI agent、RAG pipeline、MCP 工具可直接读取的 Markdown

模板默认的人类 canonical URL 风格是 `/<slug>/`，机器侧保持 `/<slug>.md`。

## 功能特性

**核心**
- 单一 Markdown 源同时生成 HTML + Markdown
- 递归扫描 `articles/**`，支持多级 slug
- 标题去重 — 当正文 `<h1>` 与 frontmatter title 一致时自动移除
- 缓存破坏 — CSS/JS 资源 URL 自动带 SHA-256 内容哈希

**内容增强**（通过 `[features]` 配置开启）
- TOC 侧边栏 — 右侧固定，滚动高亮 + 移动端抽屉
- 封面图 — 英雄横幅风格的 frontmatter 封面渲染
- 评分星级 — 数字评分（0–5）→ ⭐/☆ 显示
- lastmod 优先 — 显示日期优先使用 `lastmod` 而非 `date`
- Math/Mermaid 按需加载 — 模板驱动的 CDN 加载，三级优先级（frontmatter > config > 内容检测）

**内容组织**（可选开启）
- Category 导航 — 从 frontmatter 自动收集，暴露到导航栏 + 生成 `/category/<slug>/` 列表页
- Tags 标签系统 — `/tags/` 标签云 + `/tags/<tag>/` 文章列表页
- Mermaid 图表 — 自定义预处理器在 codehilite 之前转换围栏块（无暗色背景冲突）

**内置功能**
- `pymdownx.emoji` 构建期 Emoji 转换
- `pymdownx.arithmatex` MathJax 数学公式
- `pymdownx.mark` 高亮语法 `==text==`
- Obsidian `[[wiki 链接]]` 支持
- 任务状态标记 `[ ]` `[-]` `[x]` `[!]` `[~]`
- Explorer 分栏浏览器
- 首页分页
- 静态页面注入（`pages/` 目录）
- Atom feed、sitemap、`llms.txt`、`robots.txt`
- JSON-LD 结构化数据
- Nginx / Cloudflare Worker 网关配置
- GitHub Actions → `sites` 分支自动部署
- 无需 npm / vendor bootstrap

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

## 项目结构

```text
janus-md/
├── articles/            # Markdown 文章（支持子目录递归）
├── templates/
│   ├── base.html        # 基础布局（header/footer/主题切换）
│   ├── index.html       # 首页文章列表
│   ├── article.html     # 文章页（封面/TOC/评分/标签）
│   ├── explorer.html    # Explorer 分栏浏览器
│   ├── category.html    # Category 文章列表页
│   ├── tags.html        # 标签云首页
│   └── tag.html         # 单标签文章列表页
├── static/
│   ├── css/             # style.css + codehilite.css + theme.css + custom.css
│   └── js/              # main.js + explorer.js
├── pages/               #【可选】静态页面，构建时注入 dist/
├── deploy/              # Nginx + Cloudflare Worker 配置
├── verification/        # 根级验证文件
├── build.py             # 核心构建脚本（单文件 ~1120 行）
├── janus.config.toml    # 站点配置
└── pyproject.toml       # Python 依赖声明
```

## 配置

```toml
[features]
toc = false              # 文章 TOC 侧边栏
rating = false           # 评分星级显示
lastmod = false          # 优先使用 lastmod 日期
cover = false            # 英雄封面图
math = true              # MathJax 按需加载（向后兼容）
mermaid = true           # Mermaid 按需加载

[categories]
expose_in_nav = false    # 在导航栏显示所有 category

[tags]
enabled = false          # 启用 /tags/ 和 /tags/<tag>/ 页面
```

所有新功能默认**关闭**（math/mermaid 除外），确保现有 fork 零影响。

## Frontmatter 示例

```yaml
---
title: "文章标题"
date: 2026-03-20
lastmod: 2026-04-01       # [features.lastmod] 优先使用
description: "一句话摘要"
author:
  - "作者"
tags: [tag1, tag2]
category: "guide"          # [categories] 自动收集用于导航和列表页
rating: 4                  # [features.rating] 显示为 ⭐⭐⭐⭐☆
cover: /assets/img/hero.jpg  # [features.cover] 英雄封面图
toc: true                  # 覆盖全局 [features.toc]
math: true                 # 覆盖全局 [features.math]
mermaid: false             # 覆盖全局 [features.mermaid]
draft: false
faq:
  - q: "问题？"
    a: "答案。"
---
```

## 补充说明

- Explorer 可以生成但不暴露在导航栏
- `verification/` 中的验证文件会被复制到站点根目录
- `pages/` 中的静态页面会覆盖同名已生成文件（最后执行）
- slash canonicalization 和 AI 协商逻辑应只由一层网关负责
- Mermaid 块在 codehilite 之前预处理 — 不会出现 Pygments 干扰

English version: [README.md](README.md)
