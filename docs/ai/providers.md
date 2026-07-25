# Content AI Provider Abstraction

**Status:** Interface, mock, and orchestration only — no real AI vendors connected.  
**Related:** [API contract](./api-contract.md) · [Roadmap](./roadmap.md)

---

## Why provider independence matters

peyvand.se must never hard-depend on OpenAI, Gemini, Claude, or any single vendor.

- Application and service code call a **stable interface**, not a vendor SDK.
- Providers can be swapped via configuration (`CONTENT_AI_PROVIDER`) without rewriting Blog, Ads, or orchestration code.
- Secrets and HTTP clients stay out of Django until a future, dedicated provider PR.
- Tests use a deterministic **mock** provider with no network calls.

Content AI still owns **no business content**. Blog owns posts. Ads owns advertisements. Providers only produce text payloads that future layers may map into those apps under Admin approval.

---

## Generation pipeline

All future AI generation goes through one orchestration service:

```python
from content_ai.constants import AIGenerationTask
from content_ai.services import ContentGenerationService

result = ContentGenerationService().generate(
    AIGenerationTask.POST_GENERATION,
    {'topic': '...'},
)
```

`ContentGenerationService.generate(task, payload)`:

1. Resolves the configured provider via the registry.
2. Maps `task` to a provider method.
3. Calls the provider with `payload` as keyword arguments.
4. Returns the provider result unchanged.

It performs **no** validation, persistence, Blog/Ads writes, networking, or business rules.

Do **not** add separate `PostGenerationService` / `AdGenerationService` classes. Extend `AIGenerationTask` and the task→method map instead.

---

## Provider registry

```python
from content_ai.providers import get_provider

provider = get_provider()          # uses settings.CONTENT_AI_PROVIDER
provider = get_provider('mock')    # explicit name
```

| Setting | Current value |
|---|---|
| `CONTENT_AI_PROVIDER` | `"mock"` |

Supported today: **`mock`** only.

Unknown names raise `ProviderNotFound`. Missing / empty configuration raises `ProviderConfigurationError`.

The generation service always uses `get_provider()` (settings-driven). Callers should not import vendor modules directly.

---

## Task-based generation

Tasks live in `content_ai.constants.AIGenerationTask` (easily extendable):

| Task | Provider method |
|---|---|
| `POST_GENERATION` | `generate_post` |
| `AD_GENERATION` | `generate_ad` |
| `REWRITE` | `rewrite` |
| `SUMMARY` | `summarize` |
| `TRANSLATION` | `translate` |
| `SEO` | reserved — not wired to a provider method yet |

Unsupported tasks raise `GenerationError`.

---

## Layout

```
content_ai/providers/
    base.py         # BaseAIProvider interface
    mock.py         # MockProvider (tests / architecture only)
    registry.py     # get_provider(name)
    exceptions.py   # ProviderNotFound, ProviderConfigurationError, GenerationError

content_ai/services/
    generation.py   # ContentGenerationService (orchestration only)
```

---

## Interface

`BaseAIProvider` defines:

| Method | Purpose |
|---|---|
| `generate_post(...)` | Produce blog-post oriented text |
| `generate_ad(...)` | Produce advertisement oriented text |
| `rewrite(...)` | Rewrite existing text |
| `summarize(...)` | Summarize text |
| `translate(...)` | Translate text |

The base class raises `NotImplementedError` for each method. Concrete providers override what they support.

---

## Mock provider

`MockProvider` returns deterministic fake data (e.g. `"Mock AI response"`).

- No HTTP
- No API keys
- No SDKs
- Intended for tests and architectural wiring only

---

## How future providers will plug in

1. Add `content_ai/providers/<vendor>.py` implementing `BaseAIProvider`.
2. Register the class in `registry._PROVIDERS` under a short name (e.g. `"openai"`).
3. Point `CONTENT_AI_PROVIDER` at that name in the environment / settings when ready.
4. Keep vendor secrets in environment / credential stores — never hardcode them.
5. Call generation only through `ContentGenerationService` (or `get_provider()` inside Content AI). Never from Blog, Ads, templates, or frontend code.

No real vendor is wired in this phase.
