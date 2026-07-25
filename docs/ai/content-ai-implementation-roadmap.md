# Content AI Implementation Roadmap

**Status:** Planning / delivery notes for the Django Content AI app.  
**Product programme:** [RFC-000](./RFC-000.md) · [ROADMAP.md](./ROADMAP.md) · [RFC_INDEX.md](./RFC_INDEX.md)  
**Contract:** See [api-contract.md](./api-contract.md).

AI features on peyvand.se are additive. Blog and Ads remain the owners of their data. n8n orchestrates workflows; Django validates, stores, and enforces Admin approval. AI never publishes automatically.

---

## Phase 1 — Content AI Foundation

- Define and freeze the Django ↔ n8n API contract.
- Agree authentication strategy (API Token) and standard JSON envelopes.
- Document job lifecycle and Admin approval rules.
- Ensure no change to existing production Blog / Ads behaviour.
- Add isolated `content_ai` Django app with `AIJob` execution tracking only (no providers, APIs, or generation).

**Outcome:** Shared contract, guardrails, and an isolated execution-tracking foundation. No public behaviour change.

---

## Phase 2 — AI Provider Integration

- Introduce a vendor-neutral provider interface (`BaseAIProvider`) and registry.
- Ship `MockProvider` (deterministic, no network) for architecture and tests.
- Add `OpenAIProvider` using the Responses API (selected via `CONTENT_AI_PROVIDER=openai`).
- Keep production default on `mock` until explicitly switched.
- Standardise provider → Django payload mapping when generation is introduced into Blog/Ads.
- Keep provider secrets in environment / credential stores.

**Outcome:** Application code depends on an interface. OpenAI is available as an optional provider; mock remains the safe default.

---

## Developer Sandbox

- Manual Content AI console at `/content-ai/sandbox/`
- Purpose: manual testing, prompt debugging, provider verification
- Access: authenticated users in `DEBUG`, or superusers only
- Uses the real pipeline (request → prompt → provider → `GenerationResult`)
- No Blog/Ads persistence, no public API, no n8n

**Outcome:** Developers can exercise providers safely without changing production workflows.

---

## Prompt Asset Management

- Prompt bodies live as versioned markdown assets under `content_ai/prompts/{post|ads}/v1.md`
- `PromptLoader` reads Git-managed files; `TemplateRenderer` injects request fields (`{{ title }}`, …)
- `PostPromptTemplate` / `AdPromptTemplate` load assets and render — Python no longer embeds large prompt strings
- Future `v2` / `v3` (and A/B selection) are file-based; no database, Admin UI, or runtime editing

**Outcome:** Prompts are reviewable assets in Git, ready for versioned iteration.

---

## Editorial Domain Layer

- `EditorialAIService` builds `PostGenerationRequest`, runs the generation pipeline, and returns an in-memory `EditorialDraft`
- `EditorialDraft` is a dataclass only — no Django model, no database writes, no Blog `Post` creation
- Shared entry point for:
  - Sandbox
  - Future API
  - Future n8n
  - Future Blog integration (persistence remains a later PR)

**Outcome:** Editorial generation is domain-shaped without coupling to Blog persistence.

---

## Internal AI Integration API

- Endpoint: `POST /api/internal/ai/editorial/draft/`
- Alias (compat): `POST /api/internal/content-ai/editorial/draft/`
- Auth: authenticated **staff** or **superuser** only — **not public**
- Request fields: `title`, `language`, `category`, `context`, `instructions` (maps to `PostGenerationRequest`)
- Invokes `EditorialAIService.generate_draft()` and returns an in-memory `EditorialDraft` JSON payload (`title`, `body`, `summary`, `language`, `metadata`, `telemetry`)
- Prompt strings and provider SDK objects are never returned
- Nothing is persisted (no Blog `Post`, no Ads, no DB writes)
- Integration point for future n8n / automation once they authenticate as staff/internal callers

**Outcome:** Secure internal HTTP surface for AI Blog Writer, without changing public site behaviour.

---

## Blog Draft Integration

- `BlogDraftPersistenceService.create_blog_draft(editorial_draft, author, category)` maps an `EditorialDraft` onto the existing Blog `Post` model
- AI creates **Draft** posts only (`status=0`)
- Slug generation is left to existing `Post.save()` behaviour
- Publishing remains a **manual editorial decision** (Admin / existing Blog workflow)
- Persistence layer itself does not add Admin UI, n8n, scheduling, or SEO generation

**Outcome:** First Blog write-path for AI content without changing public publishing behaviour.

---

## Editorial Draft Publisher

- `EditorialDraftPublisher.publish_to_blog(draft, *, author, category)` is the reusable bridge between the AI editorial domain and the Blog domain
- Delegates to `BlogDraftPersistenceService` so Blog creation rules stay centralized
- Despite the name, it **never publishes** — it only creates Blog drafts (`status=0`)
- Publishing remains a **manual editorial decision**
- No Admin UI, API changes, n8n, scheduling, or notifications in this layer

**Outcome:** A stable AI → Blog draft bridge without changing public behaviour.

---

## AI-assisted Editorial Workflow

- Staff editors can use **✨ Generate with AI** on the Blog Post Admin (add or Draft edit only)
- Admin modal collects title, category, language, context, and instructions
- Action-based assistant: **Generate** / **Regenerate** are live; future actions are visible placeholders
- **Human-in-the-loop:** AI proposes; editors **Use Draft** into the Admin form; Save Draft remains manual
- Temporary version history keeps the last **three** previews for the open modal session only
- Cancel / close clears history; nothing is persisted server-side
- No auto-save, auto-publish, scheduling, background jobs, or n8n

**Outcome:** AI Editorial Assistant inside Admin without changing public publishing behaviour.

---

## AI Editorial Assistant

- Extensible **action registry** (`content_ai/assistant/actions.py`) drives the modal
- v1 enabled actions: `generate`, `regenerate`
- Future placeholders (disabled, “Coming soon”): Rewrite, Shorter, Longer, Translate, SEO Optimize, Social Post
- Modal UX: fields → Generate → Preview (title / summary / body / collapsible telemetry) → Use Draft | Cancel
- Temporary version history (last 3) is modal-session only
- Use Draft populates Admin fields only; the existing Save Draft button persists
- Published posts never show the assistant; Blog add/change permissions are reused

**Outcome:** Editors stay in control with an extensible assistant shell for future AI editing actions.

---

## AI Feedback Loop

- `AIGenerationFeedback` stores structured human evaluation for AI previews
- Ratings: Excellent / Good / Needs Improvement / Rejected
- Extendable reason codes (too long, wrong tone, hallucination, …)
- Editorial Assistant records feedback on **Use Draft** (`accepted=True`), **Regenerate** (`regenerated=True`), and **Reject**
- Closing the modal without those actions does **not** create feedback
- `FeedbackService` validates and persists; Admin is read-only for review/filtering
- No automatic prompt optimisation, dashboards, A/B engines, or aggregation in this phase

**Outcome:** Human evaluation data ready for future prompt analytics and version metrics.

---

## Editorial Experience Polish

- Loading UX: spinner + rotating status copy while Generate/Regenerate runs; actions disabled
- Keyboard: Esc closes, Ctrl/Cmd+Enter generates, ←/→ switch versions, focus trap in the modal
- Version cards show time / Current / Accepted badges
- Preview renders lightweight markdown (headings, lists, tables, code) with scrollable body
- Copy title / summary / body / all
- Optional word-level diff vs previous version after regenerate
- Telemetry collapsed by default with provider, model, duration, tokens, estimated cost
- Accessibility: ARIA labels, live status, high-contrast focus styles

**Outcome:** Production-feel editor UX without changing AI or Blog behaviour.

---

## Phase 3 — Blog Draft Generation

- `EditorialDraftPublisher` + `BlogDraftPersistenceService` map `EditorialDraft` → Blog `Post` as Draft only.
- Admin **Generate with AI** modal assists editors with preview, regenerate, temporary version history, and extensible action placeholders before Use Draft / Save Draft.
- Publishing remains Admin / editorial approval via existing Blog workflow.
- Existing Blog public APIs and templates remain unchanged.

**Outcome:** AI-assisted Blog drafts with mandatory Admin gate.

---

## Phase 4 — Advertisement Draft Generation

- n8n produces Advertisement drafts via the planned AI Ads draft endpoints.
- Django stores ads as unapproved / not publicly visible.
- Admin reviews under existing Ads approval practices.
- Existing Ads public behaviour remains unchanged.

**Outcome:** AI-assisted Ad drafts with mandatory Admin gate.

---

## Phase 5 — RSS Automation

- Optional RSS ingest workflows in n8n.
- Normalised items submitted to Django for editorial review (not auto-publish).
- Deduplication and source attribution as design goals.

**Outcome:** Assisted content intake from feeds, still Admin-controlled.

---

## Phase 6 — Workflow Optimisation

- Reduce duplicate work and improve idempotency.
- Optional webhooks (Admin approve / reject → n8n).
- Monitoring, rate limits, and operator metrics.
- Refine backlog endpoints from the API contract as needed.

**Outcome:** Stable, observable automation without weakening approval or data ownership.

---

## Principles (all phases)

1. n8n never accesses the database directly.
2. All communication goes through Django APIs.
3. Django validates and stores all data.
4. Blog and Ads applications remain unchanged in behaviour for existing users.
5. AI never publishes automatically — Admin approval is required for every AI-generated Blog Post and Advertisement.
