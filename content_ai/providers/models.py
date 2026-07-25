"""Provider-independent model metadata and usage reporting (RFC-005)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Provider-independent model descriptor."""

    provider: str
    model: str
    context_window: int | None = None
    max_output: int | None = None
    supports_json: bool = False
    supports_streaming: bool = False
    supports_vision: bool = False
    supports_embeddings: bool = False
    release_date: str = ''
    status: str = 'available'
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UsageReport:
    """
    Provider-independent usage record.

    Evaluation Framework (RFC-004) may consume these later.
    """

    provider: str
    model: str = ''
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float | None = None
    estimated_cost: float | None = None
    request_id: str = ''
    timestamp: datetime = field(default_factory=utc_now)
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
