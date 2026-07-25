"""AI Studio session models (APF-002) — local, non-production."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Studio never operates as production write path.
STUDIO_ENVIRONMENTS = frozenset({'testing', 'experimental'})


@dataclass
class GenerationRecord:
    """One Studio test generation (session-local history)."""

    generation_id: str
    timestamp: datetime
    prompt_version: str = ''
    knowledge_version: str = ''
    provider: str = ''
    model: str = ''
    workflow_stage: str = ''
    input_text: str = ''
    output_text: str = ''
    assembled_prompt: str = ''
    evaluation_score: float | None = None
    evaluation: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None
    token_usage: dict[str, Any] | None = None
    estimated_cost: float | None = None
    warnings: list[str] = field(default_factory=list)
    explainability: dict[str, Any] = field(default_factory=dict)
    environment: str = 'testing'

    def to_dict(self) -> dict[str, Any]:
        return {
            'generation_id': self.generation_id,
            'timestamp': self.timestamp.isoformat(),
            'prompt_version': self.prompt_version,
            'knowledge_version': self.knowledge_version,
            'provider': self.provider,
            'model': self.model,
            'workflow_stage': self.workflow_stage,
            'input_text': self.input_text,
            'output_text': self.output_text,
            'assembled_prompt': self.assembled_prompt,
            'evaluation_score': self.evaluation_score,
            'evaluation': dict(self.evaluation),
            'latency_ms': self.latency_ms,
            'token_usage': dict(self.token_usage) if self.token_usage else None,
            'estimated_cost': self.estimated_cost,
            'warnings': list(self.warnings),
            'explainability': dict(self.explainability),
            'environment': self.environment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> GenerationRecord:
        data = data or {}
        raw_ts = data.get('timestamp')
        try:
            timestamp = (
                datetime.fromisoformat(raw_ts) if raw_ts else utc_now()
            )
        except ValueError:
            timestamp = utc_now()
        return cls(
            generation_id=data.get('generation_id') or str(uuid4()),
            timestamp=timestamp,
            prompt_version=data.get('prompt_version') or '',
            knowledge_version=data.get('knowledge_version') or '',
            provider=data.get('provider') or '',
            model=data.get('model') or '',
            workflow_stage=data.get('workflow_stage') or '',
            input_text=data.get('input_text') or '',
            output_text=data.get('output_text') or '',
            assembled_prompt=data.get('assembled_prompt') or '',
            evaluation_score=data.get('evaluation_score'),
            evaluation=dict(data.get('evaluation') or {}),
            latency_ms=data.get('latency_ms'),
            token_usage=data.get('token_usage'),
            estimated_cost=data.get('estimated_cost'),
            warnings=list(data.get('warnings') or []),
            explainability=dict(data.get('explainability') or {}),
            environment=data.get('environment') or 'testing',
        )


@dataclass
class StudioSession:
    """
    In-memory AI Studio session.

    Never persists to production prompt/knowledge stores.
    """

    session_id: str = field(default_factory=lambda: str(uuid4()))
    environment: str = 'testing'  # testing | experimental
    active_module: str = 'prompt_lab'
    history: list[GenerationRecord] = field(default_factory=list)
    last_comparison: dict[str, Any] = field(default_factory=dict)
    last_explanations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def set_environment(self, environment: str) -> None:
        if environment not in STUDIO_ENVIRONMENTS:
            raise ValueError(
                f'Studio environment must be one of {sorted(STUDIO_ENVIRONMENTS)}; '
                'production writes are never allowed.'
            )
        self.environment = environment
        self.touch()

    def push_generation(self, record: GenerationRecord) -> None:
        self.history.append(record)
        if len(self.history) > 30:
            self.history = self.history[-30:]
        self.touch()

    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        for item in self.history:
            if item.generation_id == generation_id:
                return item
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            'session_id': self.session_id,
            'environment': self.environment,
            'active_module': self.active_module,
            'history': [item.to_dict() for item in self.history],
            'last_comparison': dict(self.last_comparison),
            'last_explanations': list(self.last_explanations),
            'metadata': dict(self.metadata),
            'updated_at': self.updated_at.isoformat(),
            'writes_production': False,
            'auto_publish_allowed': False,
        }
