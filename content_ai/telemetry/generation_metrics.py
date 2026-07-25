"""Future generation-metrics placeholders.

Inactive: no production callers. Safe to import.
Existing runtime telemetry remains in ``content_ai.telemetry``
(``AIExecutionTelemetry``).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GenerationMetricsPlaceholder:
    """Reserved shape for future analytics backends."""

    latency_ms: float | None = None
    token_usage: dict | None = None
    estimated_cost: float | None = None
    model: str = ''
    success: bool | None = None
    metadata: dict = field(default_factory=dict)


def build_generation_metrics(**fields) -> GenerationMetricsPlaceholder:
    """
    Construct a metrics placeholder.

    Does not persist, aggregate, or export. Reserved for future monitoring.
    """
    return GenerationMetricsPlaceholder(**fields)
