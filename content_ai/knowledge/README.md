# Peyvand Editorial Knowledge Base

RFC-002 infrastructure + RFC-002.5 editorial content.

**Passive in production.** Feature flags remain `False`. No PromptBuilder,
OpenAI, or generation changes. No automatic knowledge injection.

---

## Architecture overview

Knowledge is organised into three independent domains:

| Domain | Path | Responsibility |
|--------|------|----------------|
| **Sweden** | `sweden/` | Official/system Swedish knowledge (authorities, services, terminology) |
| **Community** | `community/` | Curated Iranian-in-Sweden lived-experience knowledge |
| **Peyvand** | `peyvand/` | Peyvand editorial intelligence (style, glossary, workflow) |

Cross-cutting:

| Path | Role |
|------|------|
| `templates/` | Reusable document templates |
| `manifest.yaml` | Index of all knowledge modules |
| `utils/parser.py` | Load + validate (engine) |
| `selectors/` / `injectors/` | Inactive RAG placeholders (RFC-002) |

Knowledge must stay independent from prompts: no AI instructions, no model-specific behaviour inside these files.

---

## Folder responsibilities

### `sweden/`

Authorities as separate documents, plus topic overviews:

- `authorities/` — Skatteverket, Migrationsverket, Försäkringskassan, …
- `migration/`, `healthcare/`, `education/`, `taxation/`, `labour_market/`
- `housing/`, `digital_services/`, `laws/`, `public_services/`, `terminology/`

### `community/`

- `iranian_life_in_sweden/`, `newcomer_guide/`, `cultural_notes/`
- `common_questions/`, `swedish_customs/`, `practical_guides/`
- `common_mistakes/`, `frequently_confused_terms/`, `FAQ/`

### `peyvand/`

- `editorial_style/style_guide.md` — official handbook
- `terminology/glossary.md` — official terminology standard
- `editorial_guidelines/`, `seo/`, `categories/`, `moderation/`
- `publishing/`, `tone_of_voice/`, `quality_rules/`, `content_templates/`

---

## Templates

Under `templates/`:

authority, concept, guide, process, faq, glossary_entry, comparison,
editorial_policy, knowledge_document.

Use these when adding new knowledge so structure stays consistent.

---

## Metadata

Every knowledge markdown file uses YAML front matter:

- title, category, tags
- country, language, target_audience, difficulty
- last_updated, references, status, author, version

The manifest lists `file`, `title`, `tags`, `priority`, `domain`, `category`.

---

## Glossary structure

`peyvand/terminology/glossary.md` entries include:

Swedish term · Persian term · alternative wording · definition ·
editorial recommendation · example usage · related concepts · references

---

## Editorial Style Guide

`peyvand/editorial_style/style_guide.md` is Peyvand’s official handbook
(writing, typography, numbers/dates/currency, headlines, leads, SEO,
forbidden/preferred wording).

---

## How to add knowledge

1. Choose domain (`sweden` / `community` / `peyvand`).  
2. Copy a template from `templates/`.  
3. Fill front matter + body (facts only; no prompt text).  
4. Register the file in `manifest.yaml` with unique module key and tags.  
5. Run `content_ai.tests.test_knowledge_engine` / editorial KB tests.

---

## Future RAG integration

When enabled in a later RFC, selectors may rank these modules and injectors
may append them to prompts. Until then, knowledge stays editorial-only and
version-controlled in git.
