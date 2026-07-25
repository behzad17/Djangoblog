"""Editorial workflow orchestrator (RFC-003)."""

from __future__ import annotations

import logging
import time
from typing import Iterable

from content_ai.workflow.context import StageLogEntry, WorkflowContext, utc_now
from content_ai.workflow.exceptions import (
    ContextError,
    StageExecutionError,
    TransitionError,
    WorkflowValidationError,
)
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.services import (
    ApprovalService,
    ArchiveService,
    DraftService,
    EvaluationHookService,
    FactCheckPlaceholderService,
    KnowledgeService,
    PublishingService,
    ResearchService,
    ReviewService,
    RevisionService,
    SourceIntelligenceService,
)
from content_ai.workflow.states import (
    ALLOWED_TRANSITIONS,
    WorkflowState,
    can_transition,
)

logger = logging.getLogger(__name__)


# Production generation sequence including intelligence hooks.
PRODUCTION_GENERATION_STAGES: tuple[str, ...] = (
    'research',
    'source_intelligence',
    'knowledge',
    'drafting',
    'evaluation',
)


class WorkflowOrchestrator:
    """
    Execute registered workflow stages and manage state transitions.

    Does not hardcode editorial business rules beyond transition validation.
    Does not publish Blog posts. Production generation runs via ``execute()``.
    """

    def __init__(self, stages: Iterable[WorkflowStageService] | None = None):
        self._stages: dict[str, WorkflowStageService] = {}
        if stages is None:
            stages = default_stages()
        for stage in stages:
            self.register_stage(stage)

    def register_stage(self, stage: WorkflowStageService) -> None:
        if not stage.name:
            raise WorkflowValidationError(
                f'Stage {type(stage).__name__} is missing a name.'
            )
        if stage.name in self._stages:
            raise WorkflowValidationError(
                f'Duplicate stage registration: {stage.name!r}.'
            )
        self._stages[stage.name] = stage

    def get_stage(self, name: str) -> WorkflowStageService:
        try:
            return self._stages[name]
        except KeyError as exc:
            raise WorkflowValidationError(
                f'Unknown workflow stage: {name!r}.'
            ) from exc

    def list_stages(self) -> list[str]:
        return list(self._stages.keys())

    def transition(
        self,
        context: WorkflowContext,
        target: WorkflowState,
    ) -> WorkflowContext:
        if context is None:
            raise ContextError('WorkflowContext is required.')
        context.validate_present()
        if not can_transition(context.state, target):
            raise TransitionError(
                f'Invalid transition {context.state.value!r} → {target.value!r}.'
            )
        context.state = target
        context.touch()
        logger.info(
            'Workflow transitioned to %s',
            target.value,
        )
        return context

    def run_stage(
        self,
        context: WorkflowContext,
        stage_name: str,
        *,
        transition_to: WorkflowState | None = None,
    ) -> WorkflowContext:
        """
        Run a stage, record logs, optionally transition on success.

        On failure, context moves to FAILED when a transition is legal.
        """
        if context is None:
            raise ContextError('WorkflowContext is required.')
        context.validate_present()
        stage = self.get_stage(stage_name)

        started = utc_now()
        started_perf = time.perf_counter()
        status = 'success'
        warnings: list[str] = []
        errors: list[str] = []

        try:
            context = stage.run(context)
            if transition_to is not None:
                context = self.transition(context, transition_to)
            elif stage.success_state is not None:
                # Move into the stage's success state when currently at entry.
                if (
                    stage.entry_state is not None
                    and context.state == stage.entry_state
                    and can_transition(context.state, stage.success_state)
                ):
                    context = self.transition(context, stage.success_state)
                elif (
                    stage.success_state != context.state
                    and can_transition(context.state, stage.success_state)
                ):
                    context = self.transition(context, stage.success_state)
        except TransitionError:
            raise
        except WorkflowValidationError:
            raise
        except ContextError:
            raise
        except Exception as exc:
            status = 'failed'
            errors.append(str(exc))
            context.add_error(f'{stage_name}: {exc}')
            if can_transition(context.state, WorkflowState.FAILED):
                context.state = WorkflowState.FAILED
                context.touch()
            logger.exception(
                'Workflow stage failed: stage=%s state=%s',
                stage_name,
                context.state.value,
            )
            raise StageExecutionError(
                f'Stage {stage_name!r} failed: {exc}'
            ) from exc
        finally:
            finished = utc_now()
            duration_ms = round((time.perf_counter() - started_perf) * 1000, 3)
            context.execution_time_ms = (
                (context.execution_time_ms or 0) + duration_ms
            )
            context.record_stage(
                StageLogEntry(
                    stage_name=stage_name,
                    status=status,
                    started_at=started,
                    finished_at=finished,
                    duration_ms=duration_ms,
                    warnings=list(warnings) + list(context.warnings[-1:]),
                    errors=errors,
                    prompt_version=context.prompt_version,
                    knowledge_version=context.knowledge_version,
                    provider=context.provider,
                    model=context.model,
                    token_usage=context.token_usage,
                    estimated_cost=context.estimated_cost,
                )
            )
            logger.info(
                'Workflow stage finished: stage=%s status=%s duration_ms=%s '
                'prompt_version=%s knowledge_version=%s provider=%s model=%s',
                stage_name,
                status,
                duration_ms,
                context.prompt_version,
                context.knowledge_version,
                context.provider,
                context.model,
            )

        return context

    def execute(
        self,
        context: WorkflowContext,
        stage_names: Iterable[str] | None = None,
    ) -> WorkflowContext:
        """
        Run stages in order through ``run_stage``.

        Default sequence is the production generation path:
        ``research`` (preparation) then ``drafting`` (prompt assembly +
        provider generation). Does not run approval or publishing.
        """
        names = (
            list(stage_names)
            if stage_names is not None
            else list(PRODUCTION_GENERATION_STAGES)
        )
        if not names:
            raise WorkflowValidationError(
                'execute() requires at least one stage name.'
            )
        for stage_name in names:
            context = self.run_stage(context, stage_name)
        return context

    def validate_configuration(self) -> None:
        if not self._stages:
            raise WorkflowValidationError(
                'Incomplete workflow configuration: no stages registered.'
            )
        required = {
            'research',
            'drafting',
            'review',
            'approval',
            'publishing',
            'archive',
        }
        missing = sorted(required - set(self._stages))
        if missing:
            raise WorkflowValidationError(
                'Incomplete workflow configuration; missing stages: '
                + ', '.join(missing)
            )

    def allowed_targets(self, state: WorkflowState) -> frozenset[WorkflowState]:
        return ALLOWED_TRANSITIONS.get(state, frozenset())


def default_stages() -> list[WorkflowStageService]:
    """Default stage set including production intelligence hooks."""
    return [
        ResearchService(),
        SourceIntelligenceService(),
        KnowledgeService(),
        DraftService(),
        EvaluationHookService(),
        FactCheckPlaceholderService(),
        ReviewService(),
        RevisionService(),
        ApprovalService(),
        PublishingService(),
        ArchiveService(),
    ]


def create_initial_context(
    *,
    title: str,
    language: str = '',
    audience: str = '',
    prompt_version: str = '',
    knowledge_version: str = '',
    **metadata,
) -> WorkflowContext:
    """Build a WorkflowContext in IDEA state with required metadata."""
    if not (title or '').strip():
        raise ContextError('article metadata title is required.')
    article_metadata = {'title': title.strip(), **metadata}
    return WorkflowContext(
        state=WorkflowState.IDEA,
        article_metadata=article_metadata,
        language=language,
        audience=audience,
        prompt_version=prompt_version,
        knowledge_version=knowledge_version,
    )
