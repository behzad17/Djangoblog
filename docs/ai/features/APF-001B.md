# APF-001B — Editorial Featured Image Pipeline v1.0

**Status:** Implemented (workspace assist; prompt-first; Accept → Cloudinary)  
**Parent:** [APF-001](./APF-001.md)  
**Entry:** Editorial Workspace → Featured image panel

---

## Objective

Generate professional **16:9** featured images for Peyvand articles that are:

- professional, simple, clean, visually consistent
- easy to understand (including as thumbnails)
- suitable for news, guides, reports, and educational content

Editors stay in control. AI assists; never auto-publishes.

---

## Pipeline

```
Article (headline / lead / body + type / goal / category / tags)
  → Image Planner (INTERNAL ONLY)
  → Prompt Generator (+ Image Style)
  → Prompt Preview (editable)
  → Generate / Regenerate / Generate Again
  → Large preview
  → Accept → Cloudinary upload → Post.featured_image
```

Never from URL alone. Never from title alone.

---

## Image Planner (internal)

Determines main/secondary subject, environment, focus, camera, composition,
mood, lighting, complexity, style, and things to avoid.

**Not shown to editors** (stripped from API session payloads).

---

## Image styles

| Id | Label | Default |
|----|-------|---------|
| `editorial_photo` | Editorial Photo | ✓ |
| `editorial_illustration` | Editorial Illustration | |

---

## Editor controls

- Prepare prompt / Edit prompt / Restore Original
- Style selector (Change Style rebuilds prompt)
- Generate / Regenerate / Generate Again
- Accept Image → attaches to Blog draft featured image
- Regeneration never rewrites article, SEO, tags, category, or summary
- On failure: keep article + prompt; allow retry

---

## Implementation

| Layer | Path |
|-------|------|
| Planner | `content_ai/editorial/image/planner.py` |
| Style rules | `content_ai/editorial/image/style.py` |
| Prompt builder | `content_ai/editorial/image/prompt.py` |
| Attach / Cloudinary | `content_ai/editorial/image/attach.py` |
| Service | `content_ai/editorial/image/service.py` |
| Workspace | `prepare_featured_image_prompt`, `set_featured_image_style`, `generate_featured_image`, `restore_original_image_prompt`, `accept_featured_image` |
| API | `prepare_image_prompt`, `set_image_style`, `generate_image`, `regenerate_image`, `restore_original_image_prompt`, `accept_image` |

Config: `OPENAI_IMAGE_MODEL` (default `dall-e-3`), `OPENAI_IMAGE_SIZE` (default `1792x1024`).
