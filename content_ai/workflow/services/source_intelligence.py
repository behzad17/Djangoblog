"""Source intelligence workflow stage (RFC-006 stub)."""

from __future__ import annotations

from content_ai.source import SourceInspector
from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class SourceIntelligenceService(WorkflowStageService):
    """
    Populate source metadata during research using SourceInspector.

    Soft-fails: never blocks generation. Does not fetch URLs.
    """

    name = 'source_intelligence'
    entry_state = WorkflowState.RESEARCHING
    success_state = WorkflowState.RESEARCHING

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.extension_data.setdefault('hooks', {})
        try:
            generation = context.extension_data.get('generation') or {}
            request = generation.get('request')
            title = context.article_metadata.get('title', '') or ''
            language = context.language or ''
            source = ''
            text = ''
            if request is not None:
                language = language or getattr(request, 'language', '') or ''
                source = getattr(request, 'source', '') or ''
                text = getattr(request, 'context', '') or ''
                if not text:
                    text = getattr(request, 'description', '') or ''

            url = ''
            if (source or '').strip().startswith(('http://', 'https://')):
                url = source.strip()
            elif source and not text:
                text = source

            # Combine title + body so SourceInspector's existing script heuristic
            # can see Persian/other markers in either field.
            inspect_text = '\n'.join(
                part for part in (title, text) if (part or '').strip()
            ).strip()

            record = SourceInspector().inspect(
                url=url,
                text=inspect_text,
                title=title,
                language=language,
            )
            context.extension_data['source_intelligence'] = {
                'status': 'completed',
                'source_id': record.source_id,
                'source_type': record.source_type,
                'detected_language': record.detected_language,
                'trust_score': record.trust_score,
                'title': record.title,
                'warnings': list(record.warnings),
            }
            if record.detected_language and not context.language:
                context.language = record.detected_language
            if record.source_id and record.source_id not in context.input_sources:
                context.input_sources.append(record.source_id)
            context.extension_data['hooks']['source_intelligence'] = 'completed'
        except Exception as exc:  # noqa: BLE001 — soft-fail intelligence
            context.add_warning(f'Source intelligence skipped: {exc}')
            context.extension_data['source_intelligence'] = {
                'status': 'failed_soft',
                'error': str(exc),
            }
            context.extension_data['hooks']['source_intelligence'] = 'failed_soft'
        return context
