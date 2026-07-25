# Peyvand AI — Product Roadmap

**Parent:** [RFC-000](./RFC-000.md)  
**Companion:** [content-ai-implementation-roadmap.md](./content-ai-implementation-roadmap.md) (Django delivery history)

This document is the **product** roadmap for Peyvand AI RFCs. It does not schedule calendar dates; it defines phase order and dependencies.

---

## Phase 1 — Foundation ✓

| RFC | Title | Status |
|-----|--------|--------|
| [RFC-001](./RFC_INDEX.md#rfc-001--prompt-engine) | Prompt Engine | Done (inactive architecture) |
| [RFC-002](./RFC_INDEX.md#rfc-002--knowledge-engine) | Knowledge Engine | Done (inactive) |
| [RFC-002.5](./RFC_INDEX.md#rfc-0025--editorial-knowledge-base) | Editorial Knowledge Base | Done (passive content) |

**Outcome:** Prompt and knowledge foundations exist without changing production generation behaviour.

---

## Phase 2 — Editorial Platform

| RFC | Title | Intent |
|-----|--------|--------|
| RFC-003 | Editorial Workflow | Done (inactive architecture) |
| RFC-004 | Prompt Evaluation | Done (inactive architecture) |
| RFC-005 | AI Provider Abstraction | Deepen multi-provider readiness (beyond current registry) |

**Depends on:** Phase 1  
**Outcome:** Safer editorial loops and evaluation before expanding intelligence features.

---

## Phase 3 — Editorial Intelligence

| RFC | Title | Intent |
|-----|--------|--------|
| RFC-006 | Source Intelligence | Source discovery / citation aids |
| RFC-007 | Fact Checking | Claim verification workflows |
| RFC-008 | SEO Intelligence | Title/structure recommendations |

**Depends on:** Phase 2 (workflow + evaluation), Knowledge Base  
**Outcome:** Higher trust and discoverability with humans still approving.

---

## Phase 4 — Learning

| RFC | Title | Intent |
|-----|--------|--------|
| RFC-009 | Feedback Learning | Learn from editor ratings and edits |
| RFC-010 | Editorial Memory | Persist editorial preferences / prior decisions |

**Depends on:** Phase 2–3 telemetry and feedback surfaces  
**Outcome:** Continuous improvement without silent behaviour drift.

---

## Phase 5 — Advanced AI

| RFC | Title | Intent |
|-----|--------|--------|
| RFC-011 | AI Editorial Agents | Multi-step agent workflows under human control |
| RFC-012 | Analytics | Product analytics for quality, cost, utilisation |
| RFC-013 | Continuous Improvement | Closed-loop optimisation with governance |

**Depends on:** Phases 1–4  
**Outcome:** Advanced assistance with full governance and rollback discipline.

---

## Future milestones (capability checklist)

Prepared for across phases — implement only via dedicated RFCs:

- [ ] Prompt versioning in production path  
- [ ] Knowledge retrieval (RAG) enabled behind flags  
- [ ] Embedding / semantic / hybrid search  
- [ ] Vector database integration  
- [ ] Structured JSON output  
- [ ] Editorial memory  
- [ ] Learning from human feedback  
- [ ] Multiple AI providers in active use  
- [ ] AI agents with human approval gates  
- [ ] Analytics dashboards  
- [ ] Knowledge ranking  
- [ ] A/B prompt testing  
- [ ] Continuous optimisation loops  

---

## Dependency map (summary)

```
RFC-000 (vision)
   │
   ├─► RFC-001 Prompt Engine ──┐
   ├─► RFC-002 Knowledge Engine ┼─► RFC-002.5 Knowledge Base
   │                            │
   │                            ▼
   │                     RFC-003 Workflow
   │                            │
   │              ┌─────────────┼─────────────┐
   │              ▼             ▼             ▼
   │         RFC-004 Eval   RFC-005 Providers  │
   │              │             │             │
   │              └──────┬──────┘             │
   │                     ▼                    │
   │              RFC-006 / 007 / 008         │
   │                     │                    │
   │                     ▼                    │
   │              RFC-009 / 010               │
   │                     │                    │
   │                     ▼                    │
   │              RFC-011 / 012 / 013         │
```

Full catalogue: [RFC_INDEX.md](./RFC_INDEX.md).
