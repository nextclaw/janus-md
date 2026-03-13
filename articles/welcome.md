---
title: "Welcome to Janus-MD"
date: 2026-03-14
description: "A dual-state static site template — HTML for humans, Markdown for AI."
author: "Janus-MD"
tags: [intro, getting-started]
draft: false
---

# Welcome to Janus-MD

This is your first article. Delete it and start writing your own.

**Janus-MD** generates two versions of every article:

- `/<slug>/index.html` — rendered HTML for browsers
- `/<slug>.md` — raw Markdown for AI agents & tools

## Task Status Markers

Use these markers anywhere in your Markdown to track work:

- [ ] This task has **not started** yet
- [-] This task is **in progress**
- [x] This task is **done**
- [!] This task is **blocked**
- [~] This task is **deferred or abandoned**

They render as styled inline badges and are preserved verbatim in `.md` output.

## Nested Articles

Place articles in subdirectories for organized content:

```
articles/
  2026/
    03/
      my-post.md        → /2026/03/my-post
  tutorials/
    getting-started.md  → /tutorials/getting-started
```

## Code Highlighting

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("Janus"))
```

## Next Steps

- [x] Clone the template
- [-] Edit `janus.config.toml` with your site info
- [ ] Write your first article in `articles/`
- [ ] Push to GitHub and watch CI build your site
- [ ] Configure DNS and enjoy your dual-state site
