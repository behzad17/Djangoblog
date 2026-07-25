# Content AI Provider Abstraction

**Status:** Interface, mock, OpenAI Responses provider, schemas, prompts, and orchestration.  
**Related:** [API contract](./api-contract.md) · [Product roadmap](./ROADMAP.md) · [Implementation roadmap](./content-ai-implementation-roadmap.md)

---

## Why provider independence matters

peyvand.se must never hard-depend on OpenAI, Gemini, Claude, or any single vendor.

- Application and service code call a **stable interface**, not a vendor SDK.
- Providers can be swapped via configuration (`CONTENT_AI_PROVIDER`) without rewriting Blog, Ads, or orchestration code.
- Secrets and HTTP clients stay out of Django until a future, dedicated provider PR.
- Tests use a deterministic **mock** provider with no network calls.
- Callers use **canonical schemas**; providers receive **prompt strings** and return `GenerationResult` — never vendor-specific shapes.
- **Prompt wording belongs to Peyvand**, not to the vendor adapter.

Content AI still owns **no business content**. Blog owns posts. Ads owns advertisements. Providers only produce `GenerationResult` payloads that future layers may map into those apps under Admin approval.

---

## Canonical request schemas

Defined in `content_ai/schemas/requests.py` as frozen dataclasses:

| Schema | Purpose |
|---|---|
| `PostGenerationRequest` | Blog-post generation inputs (`title`, `source`, `language`, `category`, `context`, `instructions`) |
| `AdGenerationRequest` | Advertisement generation inputs (`business_name`, `category`, `language`, `city`, `description`, `target_audience`, `instructions`) |

Callers build these objects and pass them into the pipeline. No validation is applied at this layer.

---

## Canonical response schema

Defined in `content_ai/schemas/responses.py`:

| Schema | Fields |
|---|---|
| `GenerationResult` | `success`, `content`, `metadata`, `warnings`, `provider`, `telemetry` (optional) |

Every provider method must return `GenerationResult`. The rest of the application must not depend on raw vendor JSON or SDK objects.

---

## Execution telemetry

`content_ai/telemetry.py` defines in-memory `AIExecutionTelemetry`:

| Field | Purpose |
|---|---|
| `provider` / `model` | Which adapter and model ran |
| `started_at` / `finished_at` / `duration_ms` | Timing (filled by `ContentGenerationService`) |
| `success` / `error_type` | Outcome |
| `prompt_length` / `response_length` | Size hints |
| `token_usage` / `estimated_cost` | Optional vendor usage (plain dicts/numbers only) |
| `metadata` | Extra non-vendor-specific notes |

`GenerationResult.telemetry` may be `None`. Providers may pre-populate fields (mock/OpenAI); the generation service measures duration and attaches the final object.

Telemetry is **not persisted**. Future logging / DB / analytics backends are separate PRs.

---

## Prompt layer

Prompt construction is separate from providers.

```
content_ai/prompts/
    base.py       # BasePromptTemplate.build(request) → str
    post.py       # PostPromptTemplate
    ads.py        # AdPromptTemplate
    registry.py   # get_prompt_template(task)
```

### Templates

Each template exposes `build(request)` and returns a **plain string**. Current post/ad templates are deterministic placeholders (system line, task, request fields). They are not production-optimised wording.

Providers must **never** know how prompts are written. They only consume the resulting string.

### Registry

`get_prompt_template(task)` maps `AIGenerationTask` → template:

| Task | Template |
|---|---|
| `POST_GENERATION` | `PostPromptTemplate` |
| `AD_GENERATION` | `AdPromptTemplate` |

Unregistered tasks raise `GenerationError`. Extend by adding a template module and registering it.

### Future prompt versioning

Prompt text will evolve independently of providers. Future work may track `prompt_version` on `AIJob` and select template variants without changing vendor adapters. Versioning is not implemented in this phase.

---

## Generation pipeline

All future AI generation goes through one orchestration service:

```python
from content_ai.constants import AIGenerationTask
from content_ai.schemas import PostGenerationRequest
from content_ai.services import ContentGenerationService

result = ContentGenerationService().generate(
    AIGenerationTask.POST_GENERATION,
    PostGenerationRequest(title='…', language='sv'),
)
# result is GenerationResult
```

`ContentGenerationService.generate(task, request)`:

1. Resolves the task asset template for `task` (user-prompt section).
2. Assembles the final prompt via `PromptBuilder` (behaviour modules + user prompt).
3. Resolves the configured provider via the registry.
4. Calls the provider method with the **prompt string**.
5. Returns `GenerationResult` unchanged.

Flow:

```
Request → Task User Prompt → PromptBuilder → Provider → GenerationResult
```

It performs **no** validation, persistence, Blog/Ads writes, networking, or business rules.

Do **not** add separate `PostGenerationService` / `AdGenerationService` classes. Extend `AIGenerationTask`, the prompt registry, and the task→method map instead.

---

## Provider registry

```python
from content_ai.providers import get_provider

provider = get_provider()          # uses settings.CONTENT_AI_PROVIDER
provider = get_provider('mock')    # explicit name
provider = get_provider('openai')  # OpenAI Responses API
```

| Setting | Default | Purpose |
|---|---|---|
| `CONTENT_AI_PROVIDER` | `"mock"` | Active provider name |
| `OPENAI_API_KEY` | `""` | Required when provider is `openai` |
| `OPENAI_MODEL` | `""` | Required when provider is `openai` (set via env; not hardcoded) |
| `OPENAI_TIMEOUT` | `60` | Optional request timeout (seconds) |

Supported today: **`mock`**, **`openai`**.

Production stays on **`mock`** unless `CONTENT_AI_PROVIDER` is explicitly set to `openai`.

Unknown names raise `ProviderNotFound`. Missing / empty `CONTENT_AI_PROVIDER` raises `ProviderConfigurationError`. Missing OpenAI key/model when constructing `OpenAIProvider` raises `ProviderConfigurationError`.

The generation service always uses `get_provider()` (settings-driven). Callers should not import vendor modules directly.

### Switching providers

| Mode | Settings |
|---|---|
| Safe default (no network) | `CONTENT_AI_PROVIDER=mock` |
| OpenAI | `CONTENT_AI_PROVIDER=openai` plus `OPENAI_API_KEY` and `OPENAI_MODEL` |

Never commit API keys. Use environment / Heroku config vars.

---

## OpenAI provider

`content_ai/providers/openai.py` implements `OpenAIProvider` using the official OpenAI Python SDK **Responses API** (`client.responses.create`). Chat Completions are not used.

- Accepts a prompt string from the prompt layer
- Returns `GenerationResult` only (never raw SDK objects)
- Maps SDK / network failures to `GenerationError`
- Supports `generate_post(prompt)` and `generate_ad(prompt)` via a shared private helper

---

## Task-based generation

Tasks live in `content_ai.constants.AIGenerationTask` (easily extendable):

| Task | Prompt template | Provider method | Typical request |
|---|---|---|---|
| `POST_GENERATION` | `PostPromptTemplate` | `generate_post` | `PostGenerationRequest` |
| `AD_GENERATION` | `AdPromptTemplate` | `generate_ad` | `AdGenerationRequest` |
| `REWRITE` | not registered yet | `rewrite` | — |
| `SUMMARY` | not registered yet | `summarize` | — |
| `TRANSLATION` | not registered yet | `translate` | — |
| `SEO` | reserved | — | — |

Tasks without a registered prompt template raise `GenerationError`.

---

## Layout

```
content_ai/providers/
    base.py         # BaseAIProvider interface
    mock.py         # MockProvider (tests / architecture only)
    openai.py       # OpenAIProvider (Responses API)
    registry.py     # get_provider(name)
    exceptions.py   # ProviderNotFound, ProviderConfigurationError, GenerationError

content_ai/schemas/
    requests.py     # PostGenerationRequest, AdGenerationRequest
    responses.py    # GenerationResult

content_ai/prompts/
    base.py         # BasePromptTemplate
    post.py         # PostPromptTemplate
    ads.py          # AdPromptTemplate
    registry.py     # get_prompt_template(task)

content_ai/services/
    generation.py   # ContentGenerationService (orchestration only)
```

---

## Interface

`BaseAIProvider` defines:

| Method | Purpose |
|---|---|
| `generate_post(prompt)` | Produce blog-post oriented text from a prompt string |
| `generate_ad(prompt)` | Produce advertisement oriented text from a prompt string |
| `rewrite(prompt)` | Rewrite from a prompt string |
| `summarize(prompt)` | Summarize from a prompt string |
| `translate(prompt)` | Translate from a prompt string |

The base class raises `NotImplementedError` for each method. Concrete providers override what they support and always return `GenerationResult`.

---

## Mock provider

`MockProvider` accepts a prompt string and returns deterministic `GenerationResult` values (`content="Mock AI response"`). The prompt is echoed in `metadata["prompt"]` for tests.

- No HTTP
- No API keys
- No SDKs
- No raw dictionaries as the public return type
- Intended for tests and architectural wiring only

---

## How future providers will plug in

1. Add `content_ai/providers/<vendor>.py` implementing `BaseAIProvider`.
2. Accept a **prompt string**; map internally to the vendor SDK if needed.
3. Normalize vendor output into `GenerationResult` before returning.
4. Do **not** embed Peyvand prompt wording in the vendor adapter — use the prompt layer.
5. Register the class in `registry._PROVIDERS` under a short name (e.g. `"openai"`).
6. Point `CONTENT_AI_PROVIDER` at that name when ready.
7. Keep vendor secrets in environment / credential stores — never hardcode them.
8. Call generation only through `ContentGenerationService`. Never from Blog, Ads, templates, or frontend code.

No real vendor is wired in this phase.
