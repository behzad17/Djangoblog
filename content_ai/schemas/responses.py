"""Canonical Content AI response schemas.

Providers must return ``GenerationResult`` so callers never see vendor formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from content_ai.telemetry import AIExecutionTelemetry


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Internal canonical generation response."""

    success: bool
    content: object
    metadata: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    provider: str = ''
    telemetry: AIExecutionTelemetry | None = None
