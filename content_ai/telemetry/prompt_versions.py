"""Future prompt-version telemetry placeholders.

Inactive: no production callers. Safe to import.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class PromptVersionRecord:
    """Placeholder record for prompt version / style usage."""

    prompt_version: str = ''
    style: str = ''
    timestamp: datetime | None = None


def record_prompt_version(
    prompt_version: str,
    style: str,
    timestamp: datetime | None = None,
) -> PromptVersionRecord:
    """
    Build an in-memory prompt-version record.

    Does not persist or emit metrics. Reserved for future monitoring.
    """
    return PromptVersionRecord(
        prompt_version=prompt_version,
        style=style,
        timestamp=timestamp or datetime.now(timezone.utc),
    )
