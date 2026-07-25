"""Metric registry for discovery and execution (RFC-004)."""

from __future__ import annotations

from content_ai.evaluation.exceptions import RegistryError
from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.metrics import default_metrics
from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot


class MetricRegistry:
    """
    Register, discover, and execute evaluation metrics.

    Avoids hardcoded lists at call sites — register plugins instead.
    """

    def __init__(self):
        self._metrics: dict[str, EvaluationMetric] = {}

    def register(self, metric: EvaluationMetric) -> None:
        if metric is None or not getattr(metric, 'name', ''):
            raise RegistryError('Metric must define a non-empty name.')
        if metric.name in self._metrics:
            raise RegistryError(f'Duplicate metric registration: {metric.name!r}.')
        if metric.default_weight < 0:
            raise RegistryError(
                f'Invalid metric weight for {metric.name!r}: '
                f'{metric.default_weight!r}.'
            )
        self._metrics[metric.name] = metric

    def unregister(self, name: str) -> None:
        self._metrics.pop(name, None)

    def get(self, name: str) -> EvaluationMetric:
        try:
            return self._metrics[name]
        except KeyError as exc:
            raise RegistryError(f'Unknown metric: {name!r}.') from exc

    def list_metrics(self) -> list[str]:
        return sorted(self._metrics.keys())

    def execute(
        self,
        snapshot: EvaluationSnapshot,
        names: list[str] | None = None,
    ) -> list[MetricResult]:
        selected = names or self.list_metrics()
        results: list[MetricResult] = []
        for name in selected:
            metric = self.get(name)
            result = metric.evaluate(snapshot)
            result.validate()
            results.append(result)
        return results


def build_default_registry() -> MetricRegistry:
    registry = MetricRegistry()
    for metric in default_metrics():
        registry.register(metric)
    return registry
