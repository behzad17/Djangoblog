# Django ↔ n8n API Contract

**Status:** Documentation only — no endpoints implemented yet.  
**Scope:** Official contract between **peyvand.se** (Django) and **peyvand-n8n**.  
**Rule:** Existing Blog and Ads applications remain the owners of their data. AI features are additive and must not change current production behaviour.

---

## Overall architecture

```
┌─────────────────┐         HTTPS + API Token         ┌──────────────────┐
│   peyvand-n8n   │ ─────────────────────────────────► │   peyvand.se     │
│  (orchestration)│ ◄───────────────────────────────── │   (Django)       │
└────────┬────────┘         JSON request/response      └────────┬─────────┘
         │                                                       │
         │ calls external AI providers                           │ owns DB
         ▼                                                       ▼
┌─────────────────┐                                      ┌──────────────────┐
│  AI providers   │                                      │ Blog / Ads / …   │
│  (LLM, etc.)    │                                      │ (existing apps)  │
└─────────────────┘                                      └──────────────────┘
```

- **Django** is the system of record. It validates input, stores data, enforces permissions, and exposes controlled APIs.
- **n8n** is an orchestration layer only. It triggers workflows, calls AI providers, and posts results back to Django.
- **n8n never accesses the database directly.** All reads and writes go through Django APIs.
- **AI never publishes automatically.** Generated Blog Posts and Advertisements enter a draft / pending state and require Admin approval before becoming public.

---

## Responsibilities of Django

| Responsibility | Description |
|---|---|
| Authentication | Validate API tokens for n8n callers |
| Authorisation | Restrict AI endpoints to trusted automation clients |
| Validation | Reject malformed or incomplete payloads |
| Persistence | Create and update draft content in Blog / Ads (via future AI-aware services) |
| Lifecycle | Track job status (queued → processing → completed / failed) |
| Approval | Keep Admin as the only path to publish AI-generated content |
| Audit | Record source metadata (workflow id, provider, timestamps) where planned |
| Errors | Return structured error responses; never expose internal secrets |

Django does **not** call AI providers directly in this architecture. Provider calls are owned by n8n.

---

## Responsibilities of n8n

| Responsibility | Description |
|---|---|
| Orchestration | Schedule and run Content AI workflows |
| Provider calls | Call external AI / RSS / tooling services |
| Payload shaping | Map provider output into the Django API contract |
| Job signalling | Create jobs, report progress, and submit final drafts |
| Retries | Retry transient provider failures according to workflow policy |
| Secrets | Hold provider API keys in n8n credentials (not in Django source) |

n8n must **not**:

- Connect to the Django database
- Bypass Admin approval
- Publish Blog Posts or Advertisements
- Modify existing public APIs used by the website

---

## Authentication strategy (documentation only)

Planned authentication for Django ↔ n8n traffic:

| Item | Planned approach |
|---|---|
| Mechanism | API Token (Bearer or custom header — final header name decided at implementation) |
| Transport | HTTPS only |
| Token storage | Django settings / environment variable; n8n credentials store |
| Rotation | Tokens rotatable without code changes |
| Scope | Machine-to-machine only; not end-user session auth |

Example (illustrative — not implemented):

```http
Authorization: Bearer <PEYVAND_N8N_API_TOKEN>
Content-Type: application/json
```

Unauthenticated or invalid tokens must receive `401 Unauthorized`. Missing permission for a route must receive `403 Forbidden`.

---

## Standard request/response format

All planned AI integration endpoints use JSON.

### Success envelope

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "request_id": "uuid-or-opaque-id",
    "timestamp": "2026-07-25T12:00:00Z"
  }
}
```

### Error envelope

```json
{
  "ok": false,
  "error": {
    "code": "validation_error",
    "message": "Human-readable summary",
    "details": {}
  },
  "meta": {
    "request_id": "uuid-or-opaque-id",
    "timestamp": "2026-07-25T12:00:00Z"
  }
}
```

### Conventions

- Timestamps: ISO 8601 UTC (`Z` suffix).
- IDs: opaque integers or UUIDs as assigned by Django.
- Partial updates: only documented fields may be sent; unknown fields should be rejected or ignored per endpoint policy (decided at implementation).
- Idempotency: mutating calls may accept an optional `Idempotency-Key` header (planned) to avoid duplicate drafts on retries.

---

## Planned endpoints (documentation only)

> These routes are **not implemented**. Paths and payloads may be refined before the first implementation PR. Existing public site APIs remain unchanged.

Base path (planned): `/api/ai/`

### Jobs

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/ai/jobs/` | Create a Content AI job |
| `GET` | `/api/ai/jobs/{id}/` | Fetch job status and result summary |
| `POST` | `/api/ai/jobs/{id}/complete/` | Submit successful job output |
| `POST` | `/api/ai/jobs/{id}/fail/` | Mark job failed with error details |

#### Create job — example request

```json
{
  "type": "blog_draft",
  "source": {
    "workflow_id": "n8n-workflow-id",
    "trigger": "manual"
  },
  "input": {
    "topic": "Example topic",
    "language": "sv",
    "notes": "Optional editorial guidance"
  }
}
```

#### Job status — example response `data`

```json
{
  "id": "…",
  "type": "blog_draft",
  "status": "processing",
  "created_at": "2026-07-25T12:00:00Z",
  "updated_at": "2026-07-25T12:01:00Z",
  "result_ref": null
}
```

### Blog drafts

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/ai/blog/drafts/` | Create a Blog Post draft from AI output |
| `GET` | `/api/ai/blog/drafts/{id}/` | Read draft metadata (automation use) |

AI-created Blog Posts must remain unpublished until Admin approval (aligned with existing draft / status practices in Blog).

### Advertisement drafts

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/ai/ads/drafts/` | Create an Advertisement draft from AI output |
| `GET` | `/api/ai/ads/drafts/{id}/` | Read draft metadata (automation use) |

AI-created Advertisements must remain unapproved / inactive until Admin approval (aligned with existing Ads approval flags).

### Health

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/ai/health/` | Liveness check for n8n monitoring |

---

## Job lifecycle

```
  ┌─────────┐     ┌────────────┐     ┌───────────┐     ┌────────────┐
  │ queued  │ ──► │ processing │ ──► │ completed │ ──► │ approved*  │
  └─────────┘     └─────┬──────┘     └───────────┘     └────────────┘
                        │
                        ▼
                   ┌─────────┐
                   │ failed  │
                   └─────────┘
```

\* `approved` is an **editorial** state after Admin review of the resulting Blog Post or Advertisement. Completing a job only stores a draft; it does not publish.

| Status | Meaning |
|---|---|
| `queued` | Job accepted by Django; waiting for n8n / provider work |
| `processing` | n8n is actively working the job |
| `completed` | Draft payload accepted and stored; awaiting Admin |
| `failed` | Terminal failure; details in error payload |
| `cancelled` | Optional future status if cancellation is supported |

Transitions:

1. n8n creates a job (`queued`).
2. n8n marks or Django observes `processing` when work starts.
3. On success, n8n calls complete with draft content → `completed` + draft entity.
4. On failure, n8n calls fail → `failed`.
5. Admin approves or rejects the draft in Django Admin (outside the job API).

---

## Error handling

| HTTP | `error.code` (examples) | When |
|---|---|---|
| `400` | `validation_error` | Invalid JSON or field constraints |
| `401` | `unauthorized` | Missing / invalid API token |
| `403` | `forbidden` | Token valid but not allowed for this action |
| `404` | `not_found` | Unknown job or draft id |
| `409` | `conflict` | Illegal status transition or duplicate idempotency key conflict |
| `422` | `unprocessable` | Semantically invalid but well-formed payload |
| `429` | `rate_limited` | Optional future rate limiting |
| `500` | `internal_error` | Unexpected server error |

Rules:

- Do not leak stack traces, secrets, or database details in API responses.
- Failed jobs should include a stable `code` plus a short `message` for n8n logging.
- n8n should treat `5xx` and selected `429` responses as retryable; `4xx` (except `429`) as non-retryable unless the workflow policy says otherwise.

---

## Admin approval flow

AI assists with **content generation only**. Publishing remains a human decision.

### Blog Post

1. n8n completes a `blog_draft` job with title, body, excerpt, and optional metadata.
2. Django stores a **draft** Blog Post (unpublished).
3. Admin reviews the draft in Django Admin (or existing editorial tools).
4. Admin publishes only after explicit approval.
5. Until approval, the post must not appear in public listings.

### Advertisement

1. n8n completes an `ad_draft` job with ad fields and optional metadata.
2. Django stores an Advertisement that is **not approved** / not publicly visible.
3. Admin reviews content and any URLs under existing Ads approval rules.
4. Admin approves only after explicit review.
5. Until approval, the ad must not be shown publicly.

### Non-negotiable constraints

- AI never auto-publishes Blog Posts or Advertisements.
- n8n cannot flip publish / approval flags via a privileged shortcut.
- Blog and Ads remain owners of their data models and visibility rules.
- Existing production behaviour for human-created content must remain unchanged.

---

## Future endpoints (Backlog)

Documented for planning only — not part of the initial contract surface:

| Area | Idea |
|---|---|
| RSS | Ingest normalised RSS items for editorial review |
| Categories | Suggest Blog category from draft text |
| Translation | Request SV ↔ EN draft variants |
| Image assist | Attach suggested featured-image metadata (still Admin-gated) |
| Webhooks | Optional Django → n8n callbacks on Admin approve / reject |
| Batch jobs | Create multiple drafts from one workflow run |
| Analytics | Read-only generation metrics for operators |

Any backlog endpoint requires its own implementation PR and must continue to respect Admin approval and existing Blog / Ads ownership.

---

## Related documents

- [AI Roadmap](./roadmap.md)
- Project [README](../../README.md) — AI Integration overview
