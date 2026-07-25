# Peyvand AI Evaluation Framework (RFC-004)

Passive, provider-independent evaluation of AI **outputs**.

Does **not** generate content. Does **not** modify Prompt Engine, Knowledge
Engine, Workflow, or AI Providers. Existing human feedback models/services in
this package remain unchanged.

Feature flag: `ENABLE_AI_EVALUATION_FRAMEWORK = False`.

---

## Architecture

```
EvaluationSnapshot
        ↓
MetricRegistry → Metrics (readability, structure, …)
        ↓
Scoring (MetricResult → AggregateScore)
        ↓
Evaluator
        ↓
ComparisonEngine / ReportBuilder
```

| Module | Role |
|--------|------|
| `snapshot.py` | Immutable generation record |
| `metrics/` | Pluggable heuristic metrics |
| `scoring/` | Weights + aggregates |
| `registry.py` | Register / discover / execute metrics |
| `evaluator.py` | Run full evaluation |
| `comparison.py` | Compare snapshots by dimension |
| `report.py` | Summary report architecture |
| `reports/`, `comparisons/` | Reserved storage dirs (empty) |

Human feedback (existing): `models.py`, `services.py`, `constants.py`.

---

## Metric lifecycle

1. Implement `EvaluationMetric.evaluate(snapshot) -> MetricResult`  
2. `registry.register(metric)`  
3. `Evaluator(registry).evaluate(snapshot)`  
4. Optional: `ComparisonEngine` / `ReportBuilder`

Initial metrics: readability, structure, completeness, localisation,
consistency, citations, output_length.

Future (not implemented): fact accuracy, SEO, edit distance, hallucination, …

---

## Scoring

Each metric returns score, weight, confidence, warnings, explanation.

Aggregates: overall, weighted, normalised, confidence.

---

## Extension hooks (documented only)

- RFC-003 Workflow — snapshot per stage  
- RFC-005 Providers — provider benchmarking  
- RFC-006–008 — source / fact / SEO metrics  
- RFC-009–011 — feedback, memory, agents  

---

## Example

```python
from content_ai.evaluation.snapshot import create_snapshot
from content_ai.evaluation.evaluator import Evaluator

snap = create_snapshot(
    output_text='...',
    provider='openai',
    prompt_version='v1',
    language='fa',
)
result = Evaluator().evaluate(snap)
print(result.aggregate.weighted_score)
```
