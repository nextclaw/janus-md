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
      my-post.md        → /2026/03/my-post/
  tutorials/
    getting-started.md  → /tutorials/getting-started/
```

## Emoji Support :rocket:

Janus-MD converts emoji shortcodes at build time — no JavaScript required:

- :white_check_mark: Build-time conversion — zero runtime cost
- :books: Extensive library — standard GitHub/Slack shortcodes
- :sparkles: Works everywhere — pure Unicode output

Examples: :heart: :fire: :tada: :warning: :bulb: :zap:

Full shortcode reference: [emoji-cheat-sheet](https://github.com/ikatyang/emoji-cheat-sheet)

## Math Rendering

Janus-MD supports LaTeX math via MathJax, loaded on-demand only when formulas are present.

Inline math: The energy-mass equivalence $E = mc^2$ is fundamental to physics.

Display math:

$$
\int_{-\infty}^{\infty} e^{-x^2} \, dx = \sqrt{\pi}
$$

The quadratic formula:

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

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
