# Peyvand AI Engine — Prompt Architecture (RFC-001)

Architecture-only foundation for Prompt Engineering, Knowledge Management,
Behaviour modules, Versioning, Telemetry placeholders, and Configuration.

**This package is inactive in production.** Existing generation continues to
use `content_ai/prompts/post/`, `content_ai/prompts/ads/`, `PromptLoader`,
`TemplateRenderer`, and the OpenAI provider unchanged.

---

## Architecture overview

| Layer | Responsibility | Location |
|-------|----------------|----------|
| AI Behaviour | How the model should act | `prompts/vN/system/` |
| Styles / tone | News, analysis, educational, friendly | `prompts/vN/styles/` |
| Prompt construction | Assemble modules into one string | `prompts/builders/` |
| Validation | Versions, styles, files, order | `prompts/validators/` |
| Knowledge | What the model may know (separate) | `content_ai/knowledge/` |
| Telemetry (future) | Version/style + generation metrics stubs | `content_ai/telemetry/` |
| Configuration | Defaults, supported sets, feature flags | `content_ai/config/` |

**Behaviour ≠ Knowledge.** Prompt modules define behaviour; knowledge markdown
defines domain facts. Knowledge is **not** auto-injected in this phase.

---

## Folder responsibilities

```
content_ai/prompts/
  v1/system/          identity, audience, writing, output_schema
  v1/styles/          news, analysis, educational, friendly
  builders/           PromptBuilder
  validators/         PromptValidator
  post/, ads/, …      EXISTING production templates (untouched)

content_ai/knowledge/ authorities, glossary, migration, healthcare, …
content_ai/config/    ai_engine.py defaults and flags
content_ai/telemetry/ prompt_versions.py, generation_metrics.py (stubs)
                      + existing AIExecutionTelemetry in __init__.py
```

---

## Prompt Builder

```python
from content_ai.prompts.builders import PromptBuilder

prompt = PromptBuilder().build(
    version='v1',
    style='news',
    user_prompt='...',
)
```

Assembly order:

1. Identity  
2. Audience  
3. Writing Rules  
4. Style  
5. Output Schema  
6. User Prompt  

Default version: `v1`. Default style: `news`.

---

## Prompt Validator

`PromptValidator` checks:

- supported version / style
- required module files on disk
- non-empty modules
- required section headers and order in the assembled string
- no automatic `## Knowledge` injection

Unknown versions/styles and missing files raise clear exceptions under
`content_ai.prompts.builders.exceptions`.

---

## Prompt versioning

```
prompts/v1/
prompts/v2/   # add later — register in config, drop in modules
prompts/v3/
```

1. Add `content_ai/prompts/v2/system/` and `styles/` mirrors of v1.  
2. Append `'v2'` to `SUPPORTED_PROMPT_VERSIONS` in `config/ai_engine.py`.  
3. Call `PromptBuilder().build(version='v2', ...)`.

No changes to builder code are required beyond config registration and files.

---

## Knowledge layer

Placeholder markdown only. Future RAG / retrieval pipelines may load these
modules; `FEATURE_FLAGS['inject_knowledge_into_prompts']` remains `False`.

---

## Telemetry

| Module | Role |
|--------|------|
| `telemetry/__init__.py` | Existing production `AIExecutionTelemetry` (unchanged API) |
| `telemetry/prompt_versions.py` | Placeholder records for version/style usage |
| `telemetry/generation_metrics.py` | Placeholder for latency/tokens/cost/model |

Do not treat engine telemetry stubs as production analytics.

---

## Configuration

`content_ai/config/ai_engine.py`:

- `DEFAULT_PROMPT_VERSION`, `SUPPORTED_PROMPT_VERSIONS`
- `DEFAULT_STYLE`, `SUPPORTED_STYLES`
- `SYSTEM_MODULE_ORDER`
- `FEATURE_FLAGS`, `FUTURE_AI_PROVIDERS`

---

## Adding a new style

1. Add `prompts/v1/styles/<name>.md` (and other versions as needed).  
2. Append `<name>` to `SUPPORTED_STYLES`.  
3. Build with `style='<name>'`.

---

## Adding a knowledge module

1. Add `content_ai/knowledge/<topic>.md`.  
2. Document it here.  
3. Do **not** wire into `PromptBuilder` until retrieval design is ready.

---

## Future roadmap (not implemented)

- Knowledge retrieval (RAG) and retrieval pipelines  
- Structured JSON output  
- Multi-language packs  
- Multiple AI providers and prompt A/B experiments  
- Editorial workflows, human review, approval  
- AI agent architecture and richer analytics  

This foundation exists so those capabilities can land without rewriting
production generation when migration begins.
