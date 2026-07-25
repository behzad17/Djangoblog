# Peyvand AI — Design Principles

**Parent:** [RFC-000](./RFC-000.md)

These principles govern how Peyvand AI is designed, reviewed, and evolved.

---

## Editorial philosophy

Peyvand serves the **Iranian community in Sweden**. Content must be:

- **Trustworthy** — grounded in verifiable Swedish systems and careful community knowledge  
- **Localised** — natural Persian, not literal translation  
- **Respectful** — practical, non-patronising, non-alarmist  
- **Editor-owned** — AI assists; humans decide what publishes  

Knowledge (WHAT we know) stays separate from prompts (HOW the model is asked to behave).

---

## Core principles

### 1. Human-in-the-loop

Editors retain approval, editing, and publish authority. AI never publishes automatically.

### 2. Modular design

Capabilities ship as replaceable modules (prompt engine, knowledge engine, providers, telemetry) with clear interfaces.

### 3. Separation of responsibilities

| Concern | Owns |
|---------|------|
| Application / Blog / Ads | Content persistence and publish rules |
| Prompt Engine | Behaviour modules and assembly |
| Knowledge Engine | Storage, selection, injection (when enabled) |
| Editorial Intelligence | Workflow, fact/SEO/source aids |
| AI Provider | Vendor adapters |
| Telemetry / Analytics | Observation and improvement signals |

### 4. Editorial transparency

Editors should understand what was used (prompt version, style, knowledge modules, model) when assistance is shown.

### 5. Explainability

Suggestions and retrieval results should be inspectable. Avoid opaque “black box only” workflows for editorial decisions.

### 6. Maintainability

Prefer small RFCs, clear folders, and documentation that matches the repository.

### 7. Testability

Architecture layers should be unit-testable without live vendor calls (mocks, fixtures, inactive flags).

### 8. Vendor independence

Application code depends on provider interfaces, not a single vendor SDK. Secrets stay in configuration.

### 9. Backward compatibility

New RFCs must not silently break production defaults. Feature flags and inactive foundations are preferred until migration RFCs.

### 10. Incremental evolution

Ship foundations inactive; enable behaviour deliberately; keep rollback paths.

---

## AI boundaries (reminder)

**SHOULD:** assist, suggest, retrieve, draft, explain, improve readability, structure output.  

**MUST NOT:** invent facts, fabricate quotes, auto-publish, replace review, override humans.

---

## Knowledge principles

- Factual, modular, version-controlled, editor-maintained  
- No prompts or model instructions inside knowledge documents  
- Sweden / Community / Peyvand domains remain independent  

See `content_ai/knowledge/README.md`.
