"""Reporting architecture for evaluation aggregates (RFC-004)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from content_ai.evaluation.exceptions import ReportError
from content_ai.evaluation.snapshot import EvaluationSnapshot, validate_snapshot


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Structured report payload (no dashboard UI)."""

    title: str
    summary: dict[str, float | str | None] = field(default_factory=dict)
    rankings: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class ReportBuilder:
    """
    Prepare evaluation reports from snapshots.

    Examples: average score/cost/latency, best prompt/provider, etc.
    Does not render dashboards.
    """

    def build(self, snapshots: Iterable[EvaluationSnapshot]) -> EvaluationReport:
        items = list(snapshots or [])
        if not items:
            raise ReportError('Cannot build a report from zero snapshots.')

        for snap in items:
            validate_snapshot(snap)

        scores = [
            (sum(s.scores.values()) / len(s.scores)) if s.scores else 0.0
            for s in items
        ]
        costs = [s.estimated_cost for s in items if s.estimated_cost is not None]
        latencies = [s.latency_ms for s in items if s.latency_ms is not None]
        tokens = []
        for s in items:
            if s.token_usage and s.token_usage.get('total_tokens') is not None:
                tokens.append(float(s.token_usage['total_tokens']))

        def avg(values: list[float]) -> float | None:
            if not values:
                return None
            return round(sum(values) / len(values), 6)

        best_prompt = self._best_by(items, 'prompt_version')
        best_provider = self._best_by(items, 'provider')
        best_knowledge = self._best_by(items, 'knowledge_version')
        highest_readability = self._best_metric(items, 'readability')
        highest_consistency = self._best_metric(items, 'consistency')
        lowest_cost = self._extreme_attr(
            items, 'estimated_cost', reverse=False
        )
        fastest = self._extreme_attr(items, 'latency_ms', reverse=False)
        worst_prompt = self._worst_by(items, 'prompt_version')

        return EvaluationReport(
            title='Evaluation summary',
            summary={
                'average_score': avg(scores),
                'average_cost': avg(costs) if costs else None,
                'average_latency_ms': avg(latencies) if latencies else None,
                'average_token_usage': avg(tokens) if tokens else None,
                'snapshot_count': len(items),
            },
            rankings={
                'best_prompt': [best_prompt] if best_prompt else [],
                'best_provider': [best_provider] if best_provider else [],
                'best_knowledge_version': (
                    [best_knowledge] if best_knowledge else []
                ),
                'highest_readability': (
                    [highest_readability] if highest_readability else []
                ),
                'highest_consistency': (
                    [highest_consistency] if highest_consistency else []
                ),
                'lowest_cost': [lowest_cost] if lowest_cost else [],
                'fastest_provider': [fastest] if fastest else [],
                'worst_performing_prompt': (
                    [worst_prompt] if worst_prompt else []
                ),
            },
            metadata={'passive': True},
        )

    def _mean_score(self, snap: EvaluationSnapshot) -> float:
        if not snap.scores:
            return 0.0
        return sum(snap.scores.values()) / len(snap.scores)

    def _best_by(self, items: list[EvaluationSnapshot], attr: str) -> str:
        buckets: dict[str, list[float]] = {}
        for snap in items:
            key = getattr(snap, attr, '') or 'unknown'
            buckets.setdefault(key, []).append(self._mean_score(snap))
        ranked = sorted(
            buckets.items(),
            key=lambda kv: sum(kv[1]) / len(kv[1]),
            reverse=True,
        )
        return ranked[0][0] if ranked else ''

    def _worst_by(self, items: list[EvaluationSnapshot], attr: str) -> str:
        buckets: dict[str, list[float]] = {}
        for snap in items:
            key = getattr(snap, attr, '') or 'unknown'
            buckets.setdefault(key, []).append(self._mean_score(snap))
        ranked = sorted(
            buckets.items(),
            key=lambda kv: sum(kv[1]) / len(kv[1]),
        )
        return ranked[0][0] if ranked else ''

    def _best_metric(
        self,
        items: list[EvaluationSnapshot],
        metric: str,
    ) -> str:
        best_id = ''
        best_score = -1.0
        for snap in items:
            score = (snap.scores or {}).get(metric)
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_id = snap.generation_id
        return best_id

    def _extreme_attr(
        self,
        items: list[EvaluationSnapshot],
        attr: str,
        *,
        reverse: bool,
    ) -> str:
        candidates = [
            (getattr(s, attr), s)
            for s in items
            if getattr(s, attr) is not None
        ]
        if not candidates:
            return ''
        candidates.sort(key=lambda pair: pair[0], reverse=reverse)
        winner = candidates[0][1]
        if attr == 'latency_ms':
            return winner.provider or winner.generation_id
        if attr == 'estimated_cost':
            return winner.generation_id
        return winner.generation_id
