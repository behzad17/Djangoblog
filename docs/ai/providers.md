# Content AI Provider Abstraction

**Status:** Interface and mock only — no real AI vendors connected.  
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

## Layout

```
content_ai/providers/
    base.py         # BaseAIProvider interface
    mock.py         # MockProvider (tests / architecture only)
    registry.py     # get_provider(name)
    exceptions.py   # ProviderNotFound, ProviderConfigurationError, GenerationError
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

## Registry

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
5. Do not call the vendor from Blog, Ads, templates, or frontend code; go through `get_provider()`.

No real vendor is wired in this phase.
