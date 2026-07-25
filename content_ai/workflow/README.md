# Peyvand AI Editorial Workflow (RFC-003)

Orchestration layer for the AI-assisted editorial lifecycle.

**Inactive in production.** Does not call PromptBuilder, Knowledge RAG, OpenAI,
or Blog publishing. Existing `EditorialAIService` / publisher paths are unchanged.

---

## Lifecycle (conceptual)

```
IDEA
 → RESEARCH
 → KNOWLEDGE RETRIEVAL (hook)
 → AI DRAFT
 → FACT CHECK (future / placeholder)
 → EDITORIAL REVIEW
 → REVISION
 → SEO OPTIMISATION (future hook)
 → READY FOR APPROVAL
 → APPROVED
 → PUBLISHED (prepare only)
 → ARCHIVED
```

---

## Workflow states

| State | Meaning |
|-------|---------|
| `idea` | Initial request |
| `researching` | Research inputs prepared |
| `drafting` | Draft stage active / complete |
| `fact_check_pending` | Placeholder for RFC-007 |
| `reviewing` | Editorial review |
| `revision_required` | Needs another draft/review pass |
| `ready_for_approval` | Awaiting approval |
| `approved` | Human-approved suggestion |
| `published` | Publish *prepared* (no auto-publish) |
| `archived` | Closed |
| `failed` / `cancelled` | Terminal error / abort |

Allowed transitions live in `states.ALLOWED_TRANSITIONS`.

---

## WorkflowContext

Shared object every stage receives and updates. Stages never call each other.

Tracks: state, article metadata, language, audience, prompt/knowledge versions,
sources, draft, warnings/errors/notes, token usage, cost, timing, provider/model,
stage logs, and `extension_data` for future RFCs.

---

## Services

| Service | Responsibility |
|---------|----------------|
| `ResearchService` | Prepare research inputs |
| `DraftService` | Stub draft only (no live generation) |
| `FactCheckPlaceholderService` | Pass-through for RFC-007 |
| `ReviewService` | Feedback placeholder |
| `RevisionService` | Route back toward drafting |
| `ApprovalService` | Record approval flag |
| `PublishingService` | Prepare publish metadata only |
| `ArchiveService` | Mark archived |

Common interface: `WorkflowStageService.run(context) -> context`.

---

## Orchestrator

`WorkflowOrchestrator`:

- Registers stages (rejects duplicates)
- Validates transitions
- Runs stages with structured logging
- Captures failures → `FAILED` when allowed
- Validates incomplete configuration

---

## Extension hooks (`context.extension_data['hooks']`)

Documented placeholders for:

- RFC-004 Prompt Evaluation  
- RFC-005 AI Providers  
- RFC-006 Source Intelligence  
- RFC-007 Fact Checking  
- RFC-008 SEO Intelligence  
- RFC-009 Feedback Learning  
- RFC-010 Editorial Memory  
- RFC-011 AI Agents  

---

## Example (architecture only)

```python
from content_ai.workflow import (
    WorkflowOrchestrator,
    WorkflowState,
    create_initial_context,
)

orch = WorkflowOrchestrator()
orch.validate_configuration()
ctx = create_initial_context(title='Housing update', language='fa')
ctx = orch.run_stage(ctx, 'research')
ctx = orch.transition(ctx, WorkflowState.DRAFTING)  # after research→drafting path
```

Prefer orchestrator-driven transitions via stage `success_state` in happy paths.

---

## Production safety

- No automatic publishing  
- No OpenAI / Prompt Engine / Knowledge Engine wiring in this RFC  
- Feature flag: `ENABLE_EDITORIAL_WORKFLOW = False` in `config/ai_engine.py`
