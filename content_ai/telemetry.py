"""In-memory AI execution telemetry. No persistence or analytics backends."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from content_ai.schemas.responses import GenerationResult


@dataclass(frozen=True, slots=True)
class AIExecutionTelemetry:
    """Runtime metadata for a single Content AI execution."""

    provider: str = ''
    model: str = ''
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: float | None = None
    success: bool = True
    error_type: str | None = None
    prompt_length: int = 0
    response_length: int = 0
    token_usage: dict | None = None
    estimated_cost: float | None = None
    metadata: dict = field(default_factory=dict)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def merge_telemetry(
    existing: AIExecutionTelemetry | None,
    **updates,
) -> AIExecutionTelemetry:
    """Return a new telemetry object with ``updates`` applied."""
    base = existing or AIExecutionTelemetry()
    return replace(base, **updates)


def attach_telemetry(
    result: GenerationResult,
    telemetry: AIExecutionTelemetry,
) -> GenerationResult:
    """Return a copy of ``result`` with ``telemetry`` attached."""
    return replace(result, telemetry=telemetry)
