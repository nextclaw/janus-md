# Janus-MD

> **双态静态网站模板** — 对人类返回 HTML，对 AI 返回 Markdown。

[![Build & Publish](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/nextclaw/janus-md/actions/workflows/build-and-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Janus-MD** 是一个开箱即用的静态站点生成器模板，自动为同一篇文章生成两种形态：

- `/<slug>/index.html` → 渲染好的 HTML，供浏览器与传统爬虫使用
- `/<slug>.md` → 原始 Markdown，供 AI agent、RAG pipeline 与 MCP 工具使用

内容协商由网关层（Nginx 或 Cloudflare Worker）透明处理——**内容无需任何改动**。

---

## ✨ 功能特性

- ✅ **双态输出** — 从单一 Markdown 源同时生成 HTML + Markdown
- ✅ **任务状态标记** — `[ ]` `[-]` `[x]` `[!]` `[~]` 渲染为样式化徽标
- ✅ **多层目录** — `articles/2026/03/post.md` → URL `/2026/03/post`
- ✅ **AI 发现层** — `llms.txt`、`sitemap.xml`、`robots.txt`
- ✅ **Atom RSS 订阅** — `feed.xml`
- ✅ **CI/CD** — GitHub Actions → `sites` 分支（生产服务器无需 Python）
- ✅ **网关配置** — 内置 Nginx（VPS）和 Cloudflare Worker 两套方案
- ✅ **明/暗双主题** — 跟随系统偏好，用户可手动切换
- ✅ **SEO** — Open Graph、JSON-LD 结构化数据、meta description
- ✅ **兼容 Obsidian** — frontmatter 格式与 Obsidian 默认格式一致

---

## 🚀 快速开始

### 使用模板（推荐）

1. 点击 GitHub 上的 **[Use this template](https://github.com/nextclaw/janus-md/generate)**
2. 创建你的新仓库
3. 按照 **[docs/TEMPLATE-SETUP.md](docs/TEMPLATE-SETUP.md)** 完成 5 步初始配置

### 直接克隆

```bash
git clone https://github.com/nextclaw/janus-md.git my-site
cd my-site

# 编辑站点配置
nano janus.config.toml

# 构建
uv run build.py

# 本地预览
cd dist && python3 -m http.server 8080
```

详细步骤请参阅 **[docs/QUICKSTART.md](docs/QUICKSTART.md)**（英文）。

---

## 📁 项目结构

```
janus-md/
├── articles/           ← 在这里写作（支持子目录）
├── templates/          ← Jinja2 HTML 模板
├── static/             ← CSS、JS、图片
├── deploy/
│   ├── nginx.conf              ← VPS 网关配置
│   └── cloudflare-worker.js   ← 边缘网关配置
├── .github/workflows/
│   └── build-and-publish.yml  ← CI/CD：main → 构建 → sites 分支
├── docs/                       ← 英文文档目录
├── build.py            ← SSG 构建引擎（单文件，无框架依赖）
├── janus.config.toml   ← 站点配置
└── pyproject.toml      ← Python 依赖（uv 管理）
```

---

## ✍️ 文章写法

### Frontmatter 格式

```yaml
---
title: "文章标题"
date: 2026-03-14
description: "一句话描述（用于 OG / Atom / llms.txt）"
author: "作者名"
tags: [标签1, 标签2]
draft: false
cover: /assets/img/cover.jpg   # 可选，OG 封面图
---
```

### 任务状态标记

在文章任意位置使用以下标记，构建时自动渲染为样式化徽标：

| 语法 | 含义     | 徽标颜色 |
|------|----------|---------|
| `[ ]` | 未开始  | 灰色 |
| `[-]` | 进行中  | 蓝色 |
| `[x]` | 已完成  | 绿色 |
| `[!]` | 阻塞中  | 红色 |
| `[~]` | 延后/放弃 | 琥珀色（带删除线）|

示例：

```markdown
- [x] 设计方案已确定
- [-] 功能开发中
- [ ] 测试尚未开始
- [!] 上线被 DNS 问题阻塞
- [~] 该功能已决定放弃
```

---

## 🏗️ 架构简介

```
Markdown 源文件
     ↓ build.py (SSG)
   dist/
    ├── <slug>/index.html   ← HTML（浏览器）
    └── <slug>.md           ← Markdown（AI）
     ↓ git push → sites 分支
   网关层（Nginx / Cloudflare Worker）
    ├── 人类请求  → index.html
    └── AI 请求   → .md
```

**内容协商双信号**：
- User-Agent 匹配 AI bot 列表（GPTBot、ClaudeBot 等）
- 或 HTTP 请求头 `Accept: text/markdown`

任意一个满足即返回 Markdown，二者都不满足则返回 HTML。

---

## 📄 文档

| 文档 | 说明 |
|------|------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | 5 分钟本地上手（英文） |
| [docs/TEMPLATE-SETUP.md](docs/TEMPLATE-SETUP.md) | "Use this template" 后的配置流程（英文） |
| [docs/DEPLOY.md](docs/DEPLOY.md) | 三种部署方案（英文） |
| [docs/DESIGN.md](docs/DESIGN.md) | 架构设计与技术决策（英文） |

English documentation: [README.md](README.md)

---

## 🛠 环境要求

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/)（自动管理 Python 依赖，无需手动 `pip install`）

---

## 📦 部署方案

| 方案 | 说明 |
|------|------|
| Cloudflare Pages + Worker | 推荐新手，零服务器运维 |
| VPS + Nginx | 完全自托管，成本最低 |
| Cloudflare Pages 直连 CI | 无中间分支，部署最快 |

详见 [docs/DEPLOY.md](docs/DEPLOY.md)。

---

## 📜 开源协议

MIT — 详见 [LICENSE](LICENSE)。
