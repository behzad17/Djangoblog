# Peyvand AI Fact Checking Framework (RFC-007)

Passive, provider-independent fact-checking architecture.

**Assists editors. Editors decide.** Never auto-publishes. Never adjudicates
absolute truth. Feature flag: `ENABLE_FACT_CHECKING_FRAMEWORK = False`.

---

## Architecture

```
Text / Claims
    ↓
Extract Claims (stub)
    ↓
Identify Entities (stub)
    ↓
Retrieve Evidence (registry providers — default noop)
    ↓
Compare Evidence (stub)
    ↓
Calculate Confidence
    ↓
Apply Rules
    ↓
FactCheckReport → Editorial Review
```

| Module | Role |
|--------|------|
| `claims.py` | Claim model, types, verification statuses |
| `evidence.py` | Evidence model |
| `confidence.py` | High/Medium/Low/Unknown helpers |
| `registry.py` | Claim types, rules, providers, validators |
| `verifier.py` | Pipeline steps |
| `checker.py` | Facade: extract → verify → report |
| `report.py` | Machine-readable reports |
| `providers/`, `validators/`, `rules/` | Extension packages |

---

## Claim lifecycle

1. Create or extract `Claim`  
2. Attach `Evidence` (optional; usually empty in this RFC)  
3. `Verifier.verify` / `FactChecker.check_*`  
4. Inspect `FactCheckReport` (status, confidence, recommendation)  
5. Human editorial decision  

Statuses: `unverified`, `supported`, `partially_supported`, `conflicting`,
`insufficient_evidence`, `outdated`, `requires_editor_review`.

---

## Integration hooks (documented only)

- RFC-003 Workflow — `FACT_CHECK_PENDING` stage  
- RFC-004 Evaluation — fact-accuracy metric  
- RFC-005 Providers — model-assisted extraction later  
- RFC-006 Source Intelligence — real evidence providers  
- RFC-008 SEO — claim-aware titles (future)  
- RFC-009 / 010 — feedback & memory  

---

## Example

```python
from content_ai.fact_check import FactChecker

report = FactChecker().check_text(
    'Migrationsverket announced a change.\\n\\nAnother claim here.'
)
print(report.to_dict())
```

---

## Future (not implemented)

Automatic NLP extraction, knowledge graphs, government APIs, contradiction
detection, hallucination scoring, analytics dashboards.
