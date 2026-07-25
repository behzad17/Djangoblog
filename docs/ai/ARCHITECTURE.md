# Peyvand AI — Platform Architecture

**Parent:** [RFC-000](./RFC-000.md)  
**Status:** Target architecture (layers may be inactive until their enabling RFC)

---

## Layer stack

```
Application
    ↓
Prompt Engine
    ↓
Knowledge Engine
    ↓
Editorial Intelligence
    ↓
AI Provider
    ↓
Telemetry
    ↓
Analytics
```

Each layer evolves independently. Lower layers must not encode Blog/Ads business rules.

---

## Layer responsibilities

### Application

Django apps (Blog, Ads, Admin assistant, internal APIs). Owns persistence, permissions, and publish workflows. Consumes AI results as suggestions only.

### Prompt Engine (RFC-001)

Versioned behaviour modules (`identity`, `audience`, `writing`, styles), `PromptBuilder`, `PromptValidator`, config flags.  
**Today:** production generation assembles prompts via `PromptBuilder`; task assets (`prompts/post`, `prompts/ads`) supply the user-prompt section only.

### Knowledge Engine (RFC-002 + RFC-002.5)

Manifest, parsers, selectors, injectors, and the Editorial Knowledge Base (`sweden/`, `community/`, `peyvand/`).  
**Today:** passive — `ENABLE_KNOWLEDGE_ENGINE` / `ENABLE_RAG` / `ENABLE_KNOWLEDGE_INJECTION` are `False`.

### Editorial Intelligence (Phase 3+)

Workflow, source intelligence, fact checking, SEO aids, review checklists. Builds on prompt + knowledge without owning vendor SDKs.

### AI Provider

Vendor-neutral interface (`BaseAIProvider`), registry, mock + OpenAI Responses adapters. Application code must not hard-depend on one vendor.  
See [providers.md](./providers.md).

### Telemetry

Execution metadata (latency, tokens, success/failure, prompt length). Engine stubs exist for prompt-version tracking; production uses `AIExecutionTelemetry`.

### Analytics (Phase 5)

Aggregated quality, cost, utilisation, and improvement signals. Not a production analytics product yet.

---

## Data & control flow (target)

1. Editor request enters Application.  
2. Prompt Engine assembles behavioural prompt (version + style + user input).  
3. Knowledge Engine (when enabled) selects modules and injects context.  
4. Editorial Intelligence may add checks or structured constraints.  
5. AI Provider executes the model call.  
6. Telemetry records the run; Analytics consumes aggregates later.  
7. Application returns a **draft suggestion**; humans edit and publish.

---

## Repository map (current foundations)

| Area | Path |
|------|------|
| Prompt modules / builder | `content_ai/prompts/v1/`, `builders/`, `validators/` |
| Production prompt assets | `content_ai/prompts/post/`, `ads/` |
| Knowledge base | `content_ai/knowledge/{sweden,community,peyvand,templates}/` |
| Knowledge engine | `content_ai/knowledge/{selectors,injectors,utils}/` |
| AI config flags | `content_ai/config/ai_engine.py` |
| Providers | `content_ai/providers/` |
| Telemetry | `content_ai/telemetry/` |

---

## Invariants

- AI never auto-publishes.  
- Knowledge documents contain no prompt instructions.  
- Feature flags default to safe/off for new engines.  
- RFCs follow governance in [RFC-000](./RFC-000.md).
