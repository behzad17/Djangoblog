"""AI Studio module catalogue (APF-002)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class StudioModule:
    id: str
    label: str
    description: str
    status: str = 'active'  # active | future
    rfc: str = ''


STUDIO_MODULES: tuple[StudioModule, ...] = (
    StudioModule(
        'prompt_lab',
        'Prompt Lab',
        'Preview and compare prompt assembly without changing production.',
        rfc='RFC-001',
    ),
    StudioModule(
        'knowledge_lab',
        'Knowledge Lab',
        'Browse knowledge packs and preview injection metadata.',
        rfc='RFC-002',
    ),
    StudioModule(
        'provider_lab',
        'Provider Lab',
        'Inspect providers, models, and capabilities.',
        rfc='RFC-005',
    ),
    StudioModule(
        'evaluation_lab',
        'Evaluation Lab',
        'Score outputs with the evaluation framework.',
        rfc='RFC-004',
    ),
    StudioModule(
        'workflow_inspector',
        'Workflow Inspector',
        'Visualise editorial workflow states and transitions.',
        rfc='RFC-003',
    ),
    StudioModule(
        'generation_history',
        'Generation History',
        'Local session history of Studio test generations.',
        rfc='APF-002',
    ),
    StudioModule(
        'system_health',
        'System Health',
        'Feature flags, environment mode, and health placeholders.',
        rfc='APF-002',
    ),
    StudioModule(
        'future_labs',
        'Future Labs',
        'Reserved: RAG preview, agents, benchmarking, streaming.',
        status='future',
        rfc='future',
    ),
)


def list_modules_for_ui() -> list[dict]:
    return [asdict(module) for module in STUDIO_MODULES]
