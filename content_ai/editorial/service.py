"""Editorial domain service for in-memory AI draft generation."""

from __future__ import annotations

from content_ai.constants import AIGenerationTask
from content_ai.editorial.content_types import (
    body_pass_rules,
    get_profile,
    headline_lead_pass_rules,
    resolve_content_type,
    resolve_goal,
    resolve_style,
)
from content_ai.editorial.drafts import EditorialDraft
from content_ai.editorial.structured import parse_structured_draft
from content_ai.schemas.requests import PostGenerationRequest
from content_ai.schemas.responses import GenerationResult
from content_ai.services.generation import ContentGenerationService
from content_ai.telemetry import AIExecutionTelemetry, merge_telemetry


class EditorialAIService:
    """
    Domain orchestration for editorial content generation.

    Creates a ``PostGenerationRequest``, runs the generation pipeline in two
    passes (headline/lead, then body) using content-type templates, and maps
    results to an in-memory ``EditorialDraft``. Does not persist, parse
    Markdown, create slugs, or assign authors.
    """

    def __init__(self, generation_service=None):
        self._generation_service = (
            generation_service or ContentGenerationService()
        )

    def generate_draft(
        self,
        *,
        title='',
        source='',
        language='',
        category='',
        context='',
        instructions='',
        provider_name=None,
        content_type: str | None = None,
        goal: str | None = None,
        style: str | None = None,
    ) -> EditorialDraft:
        source_title = (title or '').strip()
        language = (language or '').strip() or 'fa'
        resolved_type = resolve_content_type(content_type)
        resolved_goal = resolve_goal(goal, content_type=resolved_type)
        resolved_style = resolve_style(style, content_type=resolved_type)
        profile = get_profile(resolved_type)
        head_rules = headline_lead_pass_rules(
            content_type=resolved_type,
            goal=resolved_goal,
            style=resolved_style,
        )
        body_rules = body_pass_rules(
            content_type=resolved_type,
            goal=resolved_goal,
            style=resolved_style,
        )

        head_result = self._generation_service.generate(
            AIGenerationTask.POST_GENERATION,
            PostGenerationRequest(
                title=source_title,
                source=source,
                language=language,
                category=category,
                context=context,
                instructions=self._pass_instructions(
                    head_rules,
                    instructions,
                    source_title=source_title,
                ),
            ),
            provider_name=provider_name,
        )
        head = parse_structured_draft(head_result.content, fallback_title='')
        persian_title = (head.get('title') or '').strip()
        lead = (head.get('lead') or '').strip()
        if not persian_title and lead:
            # Prefer first line of generated lead over echoing source title.
            persian_title = lead.split('\n', 1)[0].strip()[:160]

        body_result = self._generation_service.generate(
            AIGenerationTask.POST_GENERATION,
            PostGenerationRequest(
                title=persian_title or source_title,
                source=source,
                language=language,
                category=category,
                context=context,
                instructions=self._pass_instructions(
                    body_rules,
                    instructions,
                    source_title=source_title,
                    locked_title=persian_title,
                    locked_lead=lead,
                ),
            ),
            provider_name=provider_name,
        )
        return self._to_draft(
            source_title=source_title,
            language=language,
            category=category,
            persian_title=persian_title,
            lead=lead,
            head_result=head_result,
            body_result=body_result,
            content_type=resolved_type,
            goal=resolved_goal,
            style=resolved_style,
            template_id=profile.resolved_template_id(),
        )

    def _pass_instructions(
        self,
        pass_rules: str,
        user_instructions: str,
        *,
        source_title: str = '',
        locked_title: str = '',
        locked_lead: str = '',
    ) -> str:
        parts = [pass_rules.strip()]
        if source_title:
            parts.append(
                'Source title (for context only; do not copy as TITLE):\n'
                f'{source_title}'
            )
        if locked_title or locked_lead:
            parts.append(
                'Locked TITLE:\n'
                f'{locked_title}\n'
                'Locked LEAD:\n'
                f'{locked_lead}'
            )
        extra = (user_instructions or '').strip()
        if extra:
            parts.append(extra)
        return '\n\n'.join(parts)

    def _to_draft(
        self,
        *,
        source_title: str,
        language: str,
        category: str,
        persian_title: str,
        lead: str,
        head_result: GenerationResult,
        body_result: GenerationResult,
        content_type: str = 'news',
        goal: str = 'inform',
        style: str = 'journalistic',
        template_id: str = 'news.v1',
    ) -> EditorialDraft:
        body_text = (
            '' if body_result.content is None else str(body_result.content)
        )
        parsed = parse_structured_draft(
            body_text,
            fallback_title=persian_title,
        )
        title = persian_title or parsed['title'] or source_title
        final_lead = lead or parsed['lead']
        body = (parsed['body'] or '').strip()
        if not body and body_text:
            body = body_text.strip()

        metadata = dict(body_result.metadata or {})
        metadata.setdefault('provider', body_result.provider)
        metadata.setdefault('success', body_result.success)
        warnings = list(head_result.warnings or []) + list(
            body_result.warnings or []
        )
        metadata['warnings'] = warnings
        metadata['generation_passes'] = ['headline_lead', 'body']
        metadata['source_title'] = source_title
        metadata['content_type'] = content_type
        metadata['goal'] = goal
        metadata['writing_style'] = style
        metadata['template_id'] = template_id
        metadata['suggested_category'] = (
            parsed.get('suggested_category') or category or content_type
        )
        metadata['suggested_tags'] = list(parsed.get('suggested_tags') or [])

        # Merge workflow stages from both passes when present.
        stages: list[str] = []
        for result in (head_result, body_result):
            for stage in (result.metadata or {}).get('workflow_stages') or []:
                if stage not in stages:
                    stages.append(stage)
        if stages:
            metadata['workflow_stages'] = stages

        telemetry = self._merge_pass_telemetry(head_result, body_result)
        return EditorialDraft(
            title=title,
            lead=final_lead,
            body=body,
            summary=parsed.get('summary') or final_lead,
            language=language,
            metadata=metadata,
            telemetry=telemetry,
        )

    def _merge_pass_telemetry(
        self,
        head_result: GenerationResult,
        body_result: GenerationResult,
    ) -> AIExecutionTelemetry | None:
        head_tel = head_result.telemetry
        body_tel = body_result.telemetry
        if head_tel is None and body_tel is None:
            return None
        if head_tel is None:
            return body_tel
        if body_tel is None:
            return head_tel
        duration = None
        if head_tel.duration_ms is not None or body_tel.duration_ms is not None:
            duration = round(
                (head_tel.duration_ms or 0) + (body_tel.duration_ms or 0),
                3,
            )
        return merge_telemetry(
            body_tel,
            provider=body_tel.provider or head_tel.provider,
            started_at=head_tel.started_at or body_tel.started_at,
            finished_at=body_tel.finished_at or head_tel.finished_at,
            duration_ms=duration,
            success=bool(head_tel.success and body_tel.success),
            prompt_length=(
                (head_tel.prompt_length or 0) + (body_tel.prompt_length or 0)
            )
            or None,
            response_length=(
                (head_tel.response_length or 0)
                + (body_tel.response_length or 0)
            )
            or None,
        )
