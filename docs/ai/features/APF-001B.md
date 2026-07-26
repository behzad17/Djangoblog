# APF-001B — Editorial Featured Image Generator

**Status:** Implemented (workspace assist; prompt-first)  
**Parent:** [APF-001](./APF-001.md)  
**Entry:** Editorial Workspace → Featured image panel

---

## Objective

Generate a professional **16:9** featured image for articles drafted in the Editorial Workspace.

Goal: communicate the article’s main idea clearly for a news / educational site — **not** artistic spectacle.

---

## Input

Prompt is built from:

- Persian headline, lead, full article body
- Content type, editorial goal, category, tags
- Publisher (optional)

Never from the source URL alone.

---

## Editor flow

1. **Prepare prompt** — show editable image prompt + short explanation  
2. Editor may edit the prompt  
3. **Generate** / **Regenerate** — image only (article unchanged)  
4. **Use Previous Prompt** — restore prior prompt text  

---

## Implementation

| Layer | Path |
|-------|------|
| Style rules | `content_ai/editorial/image/style.py` |
| Prompt builder | `content_ai/editorial/image/prompt.py` |
| Service | `content_ai/editorial/image/service.py` |
| Provider | `BaseAIProvider.generate_image`; OpenAI Images + Mock |
| Workspace | `WorkspaceService.prepare_featured_image_prompt` / `generate_featured_image` / `use_previous_image_prompt` |
| API | `prepare_image_prompt`, `generate_image`, `regenerate_image`, `use_previous_image_prompt` |

Config: `OPENAI_IMAGE_MODEL` (default `dall-e-3`), `OPENAI_IMAGE_SIZE` (default `1792x1024`).

---

## Out of scope (v1)

- Auto-upload to Cloudinary / `Post.featured_image` on Save Draft  
- Auto-generate image without editor review of the prompt  
