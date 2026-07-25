# Peyvand Knowledge Engine (RFC-002)

Architecture for editorial knowledge storage, selection, and (future) injection.

**Inactive in production.** Feature flags default to `False`. Existing AI
generation, OpenAI, and `PromptBuilder` behaviour are unchanged.

---

## Architecture

| Concern | Component | Status |
|---------|-----------|--------|
| Storage | `*.md` + `manifest.yaml` | Placeholder content |
| Parsing | `utils/parser.py` | Loads + validates |
| Selection | `selectors/` | Keyword placeholder → `[]` |
| Injection | `injectors/knowledge_injector.py` | No-op (returns prompt) |
| Integration | `integration.apply_knowledge_if_enabled` | Disabled unless all flags on |
| Prompt construction | `prompts/builders/PromptBuilder` | **Untouched** |

Knowledge (WHAT) stays independent from prompt behaviour modules (HOW).

---

## Manifest

`manifest.yaml` lists each module:

```yaml
migration:
  file: migration.md
  title: Migration
  tags:
    - migration
    - residence permit
  priority: 10
```

Validation checks: manifest present, markdown files exist, metadata shape,
duplicate tags across modules.

---

## Knowledge modules

Markdown placeholders under this directory. No large editorial content yet.

| File | Topic |
|------|--------|
| `authorities.md` | Swedish authorities |
| `migration.md` | Migration system |
| `healthcare.md` | Healthcare |
| `education.md` | Education |
| `taxation.md` | Taxes |
| `labour_market.md` | Employment |
| `glossary.md` | Swedish ↔ Persian terms |

---

## Parser

```python
from content_ai.knowledge import parse_knowledge_modules

modules = parse_knowledge_modules()
```

Returns `KnowledgeModule(name, title, file, tags, priority, content)`.

---

## Selectors

```python
from content_ai.knowledge import get_knowledge_selector

selector = get_knowledge_selector()  # keyword (default)
selected = selector.select(user_prompt, style='news', language='fa')
# → [] today
```

Future selector names (not implemented): embedding, hybrid, semantic.

---

## Injectors

```python
from content_ai.knowledge import KnowledgeInjector

KnowledgeInjector().inject(prompt, modules)  # returns prompt unchanged
```

---

## Configuration

In `content_ai/config/ai_engine.py`:

- `ENABLE_KNOWLEDGE_ENGINE = False`
- `ENABLE_RAG = False`
- `ENABLE_KNOWLEDGE_INJECTION = False`

Do not enable these in production until a migration RFC.

---

## Integration point (disabled)

`apply_knowledge_if_enabled(prompt, user_prompt=..., style=..., language=...)`
exists for a future PromptBuilder migration. With flags off it returns
`prompt` unchanged and is **not** called by production code today.

---

## Adding a knowledge module

1. Add `topic.md` (placeholder is fine).  
2. Register it in `manifest.yaml` with `file`, `title`, `tags`, `priority`.  
3. Ensure tags are unique across the manifest.  
4. Run Knowledge Engine tests.

---

## Future RAG roadmap (not implemented)

- Real keyword retrieval and ranking  
- Embeddings + vector database  
- Semantic / hybrid search  
- Country-specific and multi-language packs  
- Versioned knowledge and automatic prompt injection  

Only the architecture is prepared in this RFC.
