"""Workspace service — compose existing AI layers (APF-001)."""

from __future__ import annotations

import logging
import time

from content_ai.editorial.content_types import (
    PROMPT_ENGINE_VERSION,
    classify_content,
    detect_editorial_goal,
    detect_writing_style,
    get_profile,
    resolve_content_type,
    resolve_goal,
    resolve_style,
)
from content_ai.editorial.article_length import (
    ARTICLE_LENGTH_LABELS,
    resolve_article_length,
)
from content_ai.editorial.category_recommender import (
    list_blog_categories_for_ui,
    recommend_category,
)
from content_ai.editorial.service import EditorialAIService
from content_ai.editorial.image import FeaturedImageService
from content_ai.editorial.image.style import (
    DEFAULT_IMAGE_STYLE,
    IMAGE_STYLE_LABELS,
    resolve_image_style,
)
from content_ai.editorial.image.attach import (
    FeaturedImageAttachError,
    attach_featured_image_to_post,
    upload_featured_image_asset,
)
from content_ai.evaluation.evaluator import Evaluator
from content_ai.evaluation.snapshot import create_snapshot
from content_ai.fact_check import FactChecker
from content_ai.providers.exceptions import GenerationError
from content_ai.source import SourceInspector
from content_ai.workflow import WorkflowOrchestrator, WorkflowState
from content_ai.workspace.actions import get_action, list_actions_for_ui
from content_ai.workspace.integrity import (
    SOURCE_NOT_READY_MESSAGE,
    SourceIntegrityError,
    assert_generation_integrity,
    build_source_binding,
)
from content_ai.workspace.session import ArticleSections, WorkspaceSession

logger = logging.getLogger(__name__)


def _split_draft_body(body: str) -> tuple[str, str]:
    """Best-effort lead = first paragraph; rest = body."""
    text = (body or '').strip()
    if not text:
        return '', ''
    parts = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not parts:
        return '', text
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], '\n\n'.join(parts[1:])


class WorkspaceService:
    """
    Orchestrates the AI Editorial Workspace by composing existing packages.

    Does not auto-publish. Explicit staff Publish action may publish a linked draft.
    """

    def __init__(
        self,
        editorial: EditorialAIService | None = None,
        source_inspector: SourceInspector | None = None,
        fact_checker: FactChecker | None = None,
        evaluator: Evaluator | None = None,
        workflow: WorkflowOrchestrator | None = None,
        featured_image: FeaturedImageService | None = None,
    ):
        self.editorial = editorial or EditorialAIService()
        self.source_inspector = source_inspector or SourceInspector()
        self.fact_checker = fact_checker or FactChecker()
        self.evaluator = evaluator or Evaluator()
        self.workflow = workflow or WorkflowOrchestrator()
        self.featured_image = featured_image or FeaturedImageService()

    def new_session(
        self,
        *,
        language: str = 'fa',
        audience: str = 'iranian-community-sweden',
    ) -> WorkspaceSession:
        return WorkspaceSession(language=language, audience=audience)

    def ingest_source(
        self,
        session: WorkspaceSession,
        *,
        url: str = '',
        text: str = '',
        title: str = '',
        publisher: str = '',
    ) -> dict:
        previous_url = (session.source_url or '').strip()
        previous_material = (session.source_material or '').strip()
        incoming_url = (url or '').strip()
        incoming_text = (text or '').strip()

        record = self.source_inspector.inspect(
            url=incoming_url,
            text=incoming_text,
            title=title,
            publisher=publisher,
            language=session.language,
            fetch=True,
        )
        new_url = (record.url or incoming_url or '').strip()
        new_text = (record.raw_text or incoming_text or '').strip()
        url_changed = bool(previous_url and new_url and previous_url != new_url)
        # A new URL or cleared text must never keep a previous article draft.
        if url_changed or (previous_material and not new_text) or (
            previous_material and new_text and previous_material != new_text
        ):
            session.sections = ArticleSections()
            session.history = []
            session.metadata.pop('generation', None)
            session.metadata.pop('blog_draft', None)
            session.metadata.pop('publish_success', None)
            logger.info(
                'workspace_ingest cleared_stale_draft session_id=%s '
                'previous_url=%r new_url=%r previous_chars=%s new_chars=%s',
                session.session_id,
                previous_url,
                new_url,
                len(previous_material),
                len(new_text),
            )

        session.source_url = new_url
        session.source_material = new_text
        session.research_notes = self._research_notes(record)
        session.workflow_state = WorkflowState.RESEARCHING
        retrieval = (
            (record.metadata or {}).get('retrieval')
            or ('manual_paste' if new_text else 'url_only_no_fetch')
        )
        publication_date = ''
        if record.publication_date is not None:
            publication_date = record.publication_date.isoformat()
        session.metadata['source'] = {
            'source_id': record.source_id,
            'title': record.title,
            'publisher': record.publisher,
            'url': record.url,
            'publication_date': publication_date,
            'detected_language': record.detected_language,
            'detected_country': record.detected_country,
            'source_type': record.source_type,
            'trust_score': record.trust_score,
            'freshness': record.freshness,
            'classification': record.classification,
            'warnings': list(record.warnings),
            'retrieval': retrieval,
            'extraction': dict((record.metadata or {}).get('extraction') or {}),
        }
        session.metadata['source_binding'] = build_source_binding(
            session_id=session.session_id,
            source_url=session.source_url,
            source_text=session.source_material,
            retrieval=retrieval,
        )
        session.mark_pipeline('source_imported', 'metadata_extracted')
        self._classify_session(
            session,
            title=record.title or title,
            text=session.source_material,
            url=session.source_url,
            publisher=publisher or record.publisher,
        )
        if retrieval == 'url_fetch':
            session.last_explanations = [
                (
                    f'Fetched and extracted article from {session.source_url} '
                    f'({len(session.source_material)} characters).'
                ),
                *list(session.last_explanations or []),
            ]
        session.touch()
        logger.info(
            'workspace_ingest session_id=%s source_url=%r source_chars=%s '
            'retrieval=%s warnings=%s',
            session.session_id,
            session.source_url,
            len(session.source_material),
            retrieval,
            list(record.warnings),
        )
        return session.metadata['source']

    def _classify_session(
        self,
        session: WorkspaceSession,
        *,
        title: str = '',
        text: str = '',
        url: str = '',
        publisher: str = '',
    ) -> None:
        classification = classify_content(
            title=title,
            text=text,
            url=url,
            publisher=publisher,
            metadata=session.metadata.get('source') or {},
        )
        goal = detect_editorial_goal(
            content_type=classification.content_type,
            title=title,
            text=text,
        )
        style = detect_writing_style(
            content_type=classification.content_type,
            title=title,
            text=text,
        )
        session.content_type = classification.content_type
        session.content_type_confidence = classification.confidence
        session.goal = goal.goal
        session.goal_confidence = goal.confidence
        session.writing_style = style.style
        session.writing_style_confidence = style.confidence
        profile = get_profile(session.resolved_content_type())
        session.template_id = profile.resolved_template_id()
        session.metadata['classification'] = {
            **classification.to_dict(),
            'goal': goal.to_dict(),
            'style': style.to_dict(),
            'template_id': session.template_id,
            'prompt_version': PROMPT_ENGINE_VERSION,
            'lead_label': profile.lead_label,
            'override_content_type': session.content_type_override or None,
            'override_goal': session.goal_override or None,
            'override_style': session.writing_style_override or None,
        }
        session.mark_pipeline(
            'content_classified',
            'goal_detected',
            'style_detected',
        )
        session.last_explanations = [
            (
                f'Detected content type: {profile.label} '
                f'(confidence {int(round(classification.confidence * 100))}%).'
            ),
            (
                f'Detected editorial goal: {session.resolved_goal()} '
                f'(confidence {int(round(goal.confidence * 100))}%).'
            ),
            (
                f'Detected writing style: {session.resolved_writing_style()} '
                f'(confidence {int(round(style.confidence * 100))}%).'
            ),
            f'Prompt template: {session.template_id}.',
            f'Prompt version: {PROMPT_ENGINE_VERSION}.',
            *(classification.reasons[:2]),
            *(goal.reasons[:1]),
            *(style.reasons[:1]),
            'Editors can override type, goal, and style before generating.',
        ]
        self._recommend_category(
            session,
            headline=title or session.sections.headline,
            body=text or session.source_material,
            publisher=publisher
            or (session.metadata.get('source') or {}).get('publisher')
            or '',
        )

    def _recommend_category(
        self,
        session: WorkspaceSession,
        *,
        headline: str = '',
        body: str = '',
        publisher: str = '',
        apply_to_section: bool = True,
    ) -> None:
        source_meta = session.metadata.get('source') or {}
        recommendation = recommend_category(
            headline=headline or session.sections.headline,
            source_title=source_meta.get('title') or '',
            body=body or session.source_material or session.sections.body,
            content_type=session.resolved_content_type(),
            goal=session.resolved_goal(),
            style=session.resolved_writing_style(),
            publisher=publisher or source_meta.get('publisher') or '',
        )
        session.metadata['category_recommendation'] = recommendation.to_dict()
        if apply_to_section and recommendation.selected:
            # Always propose; auto-select fills empty or updates when confident.
            if recommendation.auto_selected or not (session.sections.category or '').strip():
                session.sections.category = recommendation.selected.name
        explanations = list(session.last_explanations or [])
        explanations.extend(recommendation.reasons[:3])
        explanations.append(recommendation.message)
        session.last_explanations = explanations

    def set_classification(
        self,
        session: WorkspaceSession,
        *,
        content_type: str | None = None,
        goal: str | None = None,
        writing_style: str | None = None,
        article_length: str | None = None,
    ) -> WorkspaceSession:
        """Apply editor overrides for content type, goal, style, and/or length."""
        if content_type is not None:
            session.content_type_override = resolve_content_type(content_type)
        if goal is not None:
            session.goal_override = resolve_goal(
                goal,
                content_type=session.resolved_content_type(),
            )
        if writing_style is not None:
            session.writing_style_override = resolve_style(
                writing_style,
                content_type=session.resolved_content_type(),
            )
        if article_length is not None:
            session.article_length = resolve_article_length(article_length)
        profile = get_profile(session.resolved_content_type())
        session.template_id = profile.resolved_template_id()
        # When type changes without an explicit style override, refresh
        # detected style toward the new type default while preserving
        # any prior detection metadata.
        if content_type is not None and not session.writing_style_override:
            refreshed = detect_writing_style(
                content_type=session.resolved_content_type(),
                title=(session.metadata.get('source') or {}).get('title') or '',
                text=session.source_material,
            )
            session.writing_style = refreshed.style
            session.writing_style_confidence = refreshed.confidence
        classification = dict(session.metadata.get('classification') or {})
        style_meta = dict(classification.get('style') or {})
        classification.update(
            {
                'content_type': session.resolved_content_type(),
                'confidence': (
                    1.0
                    if session.content_type_override
                    else session.content_type_confidence
                ),
                'reasons': (
                    ['Editor override selected this content type.']
                    if session.content_type_override
                    else classification.get('reasons', [])
                ),
                'goal': {
                    'goal': session.resolved_goal(),
                    'confidence': (
                        1.0
                        if session.goal_override
                        else session.goal_confidence
                    ),
                    'reasons': (
                        ['Editor override selected this editorial goal.']
                        if session.goal_override
                        else (classification.get('goal') or {}).get(
                            'reasons', []
                        )
                    ),
                },
                'style': {
                    'style': session.resolved_writing_style(),
                    'confidence': (
                        1.0
                        if session.writing_style_override
                        else session.writing_style_confidence
                    ),
                    'reasons': (
                        ['Editor override selected this writing style.']
                        if session.writing_style_override
                        else style_meta.get('reasons', [])
                    ),
                },
                'template_id': session.template_id,
                'prompt_version': PROMPT_ENGINE_VERSION,
                'lead_label': profile.lead_label,
                'override_content_type': session.content_type_override or None,
                'override_goal': session.goal_override or None,
                'override_style': session.writing_style_override or None,
            }
        )
        session.metadata['classification'] = classification
        session.mark_pipeline(
            'content_classified',
            'goal_detected',
            'style_detected',
        )
        session.last_explanations = [
            f'Using content type: {profile.label}.',
            f'Using editorial goal: {session.resolved_goal()}.',
            f'Using writing style: {session.resolved_writing_style()}.',
            f'Prompt template: {session.template_id}.',
            f'Prompt version: {PROMPT_ENGINE_VERSION}.',
            'Change any field and regenerate to apply a new template.',
        ]
        session.touch()
        return session

    def assistant_actions(self, session: WorkspaceSession) -> list[dict]:
        return list_actions_for_ui(session.resolved_content_type())

    def _research_notes(self, record) -> str:
        publication = (
            record.publication_date.isoformat()
            if record.publication_date is not None
            else 'unknown'
        )
        retrieval = (record.metadata or {}).get('retrieval') or 'manual'
        lines = [
            f'Source: {record.title or "(untitled)"}',
            f'URL: {record.url or "—"}',
            f'Publisher: {record.publisher or "unknown"}',
            f'Publication date: {publication}',
            f'Type: {record.source_type}',
            f'Language: {record.detected_language or "unknown"}',
            f'Country: {record.detected_country or "unknown"}',
            f'Retrieval: {retrieval}',
            f'Extracted characters: {len((record.raw_text or "").strip())}',
            'Entities: (manual review — auto NER not implemented)',
            'Topics: (manual review)',
            'Possible missing information: verify dates, agency names, numbers.',
        ]
        return '\n'.join(lines)

    def generate_draft(
        self,
        session: WorkspaceSession,
        *,
        title: str = '',
        category: str = '',
        instructions: str = '',
        provider_name: str | None = None,
        article_length: str | None = None,
    ) -> WorkspaceSession:
        assert_generation_integrity(session)
        if article_length is not None:
            session.article_length = resolve_article_length(article_length)
        if not session.content_type and not session.content_type_override:
            self._classify_session(
                session,
                title=title or session.sections.headline,
                text=session.source_material,
                url=session.source_url,
            )
        working_title = title or session.sections.headline or 'Untitled draft'
        content_type = session.resolved_content_type()
        goal = session.resolved_goal()
        writing_style = session.resolved_writing_style()
        length = session.resolved_article_length()
        profile = get_profile(content_type)
        session.template_id = profile.resolved_template_id()
        # Generation context is ONLY current imported source text.
        # Never append research notes as substitute article body.
        context = (session.source_material or '').strip()
        if not context:
            raise SourceIntegrityError(SOURCE_NOT_READY_MESSAGE)
        draft = self.editorial.generate_draft(
            title=working_title,
            language=session.language,
            category=category or session.sections.category,
            context=context,
            instructions=instructions,
            provider_name=provider_name,
            content_type=content_type,
            goal=goal,
            style=writing_style,
            article_length=length,
        )
        lead = (draft.lead or '').strip()
        body = (draft.body or '').strip()
        if not lead and not body:
            lead, body = _split_draft_body(draft.body)
        elif not lead:
            lead, remainder = _split_draft_body(body)
            if remainder:
                body = remainder
        session.sections = ArticleSections(
            headline=draft.title or working_title,
            lead=lead,
            body=body or draft.body,
            summary=draft.summary or '',
            category=category or session.sections.category,
            tags=list(
                draft.metadata.get('suggested_tags') or session.sections.tags
            ),
            excerpt=(draft.summary or lead)[:300],
        )
        self._recommend_category(
            session,
            headline=session.sections.headline,
            body='\n\n'.join(
                part
                for part in (
                    session.source_material,
                    session.sections.lead,
                    session.sections.body,
                )
                if part
            ),
            publisher=(session.metadata.get('source') or {}).get('publisher')
            or '',
        )
        session.workflow_state = WorkflowState.DRAFTING
        session.mark_pipeline('draft_generated')
        category_rec = session.metadata.get('category_recommendation') or {}
        selected_cat = (category_rec.get('selected') or {}).get('name') or session.sections.category
        session.last_explanations = [
            f'Draft generated with template {session.template_id}.',
            f'Content type: {profile.label}; goal: {goal}; '
            f'style: {writing_style}.',
            f'Article length: {ARTICLE_LENGTH_LABELS.get(length, length)}.',
            f'Prompt version: {PROMPT_ENGINE_VERSION}.',
            f'{profile.lead_label} and body follow the content-type structure.',
            f'Category recommendation: {selected_cat or "—"}.',
            category_rec.get('message') or '',
            'Sections are independently editable; regenerate one section at a time.',
        ]
        session.last_explanations = [
            item for item in session.last_explanations if item
        ]
        from dataclasses import asdict

        session.push_history('Full draft', session.last_explanations[0])
        if draft.telemetry:
            telemetry = asdict(draft.telemetry)
            for key in ('started_at', 'finished_at'):
                value = telemetry.get(key)
                if value is not None and hasattr(value, 'isoformat'):
                    telemetry[key] = value.isoformat()
            session.metadata['last_telemetry'] = telemetry
        else:
            session.metadata['last_telemetry'] = {}
        session.metadata['generation'] = {
            'content_type': content_type,
            'goal': goal,
            'writing_style': writing_style,
            'article_length': length,
            'template_id': session.template_id,
            'prompt_version': PROMPT_ENGINE_VERSION,
            'session_id': session.session_id,
            'source_url': session.source_url,
            'source_binding': dict(
                (session.metadata or {}).get('source_binding') or {}
            ),
        }
        # Auto-build featured image prompt from the new article (editors
        # review optionally — they never write prompts from scratch).
        draft_explanations = list(session.last_explanations)
        try:
            self.prepare_featured_image_prompt(
                session,
                reset_generated_image=True,
            )
            session.last_explanations = draft_explanations + [
                'Featured image prompt prepared automatically — '
                'Generate Image when ready.',
            ]
        except ValueError:
            # Incomplete sections; Prepare Prompt remains available in UI.
            session.last_explanations = draft_explanations
        session.touch()
        return session

    def regenerate_section(
        self,
        session: WorkspaceSession,
        section: str,
        *,
        instructions: str = '',
        provider_name: str | None = None,
    ) -> WorkspaceSession:
        allowed = {
            'headline', 'lead', 'body', 'summary', 'excerpt', 'category', 'tags',
        }
        if section not in allowed:
            raise ValueError(f'Unknown section: {section!r}')
        hint = instructions or f'Regenerate only the {section} section.'
        # Compose a focused prompt through existing editorial service.
        focused = self.editorial.generate_draft(
            title=session.sections.headline or 'Draft',
            language=session.language,
            category=session.sections.category,
            context=session.sections.body or session.source_material,
            instructions=hint,
            provider_name=provider_name,
            content_type=session.resolved_content_type(),
            goal=session.resolved_goal(),
            style=session.resolved_writing_style(),
            article_length=session.resolved_article_length(),
        )
        explanation = f'{section} regenerated independently.'
        if section == 'headline':
            parsed = None
            try:
                from content_ai.editorial.structured import parse_structured_draft

                parsed = parse_structured_draft(focused.body, fallback_title='')
            except Exception:  # noqa: BLE001
                parsed = None
            session.sections.headline = (
                (parsed or {}).get('title')
                or focused.title
                or focused.body.strip().split('\n')[0]
            )
        elif section == 'lead':
            lead = focused.lead
            if not lead:
                lead, _ = _split_draft_body(focused.body)
            session.sections.lead = lead or focused.body
        elif section == 'body':
            body = focused.body
            if focused.lead and body == focused.lead:
                _, body = _split_draft_body(focused.body)
            session.sections.body = body or focused.body
        elif section == 'summary':
            session.sections.summary = focused.summary or focused.body[:400]
        elif section == 'excerpt':
            session.sections.excerpt = (focused.summary or focused.body)[:300]
        elif section == 'category':
            session.sections.category = (
                focused.metadata.get('suggested_category')
                or focused.metadata.get('category')
                or session.sections.category
            )
        session.last_explanations = [
            explanation,
            'Other sections were left unchanged.',
        ]
        session.push_history(f'Regenerate {section}', explanation)
        session.workflow_state = WorkflowState.REVISION_REQUIRED
        session.touch()
        return session

    def run_assistant_action(
        self,
        session: WorkspaceSession,
        action_id: str,
        *,
        provider_name: str | None = None,
    ) -> WorkspaceSession:
        action = get_action(action_id)
        if action is None:
            raise ValueError(f'Unknown action: {action_id!r}')
        if not action.implemented:
            session.last_explanations = [
                f'Action {action.label!r} is reserved for a future release.',
            ]
            session.touch()
            return session
        return self.regenerate_section(
            session,
            action.target_section if action.target_section in {
                'headline', 'lead', 'body', 'summary', 'excerpt',
            } else 'body',
            instructions=f'{action.label}. {action.description}'.strip(),
            provider_name=provider_name,
        )

    def fact_check(self, session: WorkspaceSession) -> dict:
        text = '\n\n'.join(
            part
            for part in (
                session.sections.headline,
                session.sections.lead,
                session.sections.body,
            )
            if part
        )
        if not text.strip():
            return {
                'claims': [],
                'summary': {'claim_count': 0, 'auto_publish_allowed': False},
                'metadata': {'note': 'No article text to check.'},
            }
        report = self.fact_checker.check_text(text)
        payload = report.to_dict()
        session.metadata['fact_check'] = payload
        session.mark_pipeline('fact_checked')
        if session.pipeline.get('seo_ready') and session.pipeline.get(
            'draft_generated'
        ):
            session.mark_pipeline('ready_for_publication')
        session.last_explanations = [
            'Fact check used RFC-007 FactChecker (stub evidence / editor review).',
        ]
        session.touch()
        return payload

    def evaluate(self, session: WorkspaceSession) -> dict:
        output = '\n\n'.join(
            part
            for part in (
                session.sections.headline,
                session.sections.lead,
                session.sections.body,
                session.sections.summary,
            )
            if part
        )
        snap = create_snapshot(
            output_text=output,
            input_text=session.source_material,
            language=session.language,
            workflow_stage=session.workflow_state.value,
            provider='workspace',
        )
        result = self.evaluator.evaluate(snap)
        payload = {
            'scores': dict(result.snapshot.scores),
            'overall': result.aggregate.overall_score,
            'weighted': result.aggregate.weighted_score,
            'confidence': result.aggregate.confidence_score,
            'warnings': list(result.aggregate.warnings),
        }
        session.metadata['evaluation'] = payload
        session.last_explanations = [
            'Evaluation used RFC-004 Evaluator heuristics.',
        ]
        session.touch()
        return payload

    def seo_placeholders(self, session: WorkspaceSession) -> dict:
        headline = session.sections.headline or ''
        summary = session.sections.summary or session.sections.excerpt or ''
        payload = {
            'seo_title': headline[:60],
            'meta_description': summary[:155],
            'slug': '',
            'keywords': list(session.sections.tags),
            'suggested_internal_links': [],
            'suggested_external_links': [],
            'opengraph_title': headline,
            'opengraph_description': summary[:200],
            'image_prompt': '',
            'schema_placeholders': {},
            'note': 'SEO panel is placeholder architecture only.',
        }
        session.metadata['seo'] = payload
        # Prefer an already-prepared featured image prompt when present.
        featured = session.metadata.get('featured_image') or {}
        if featured.get('prompt'):
            payload['image_prompt'] = featured.get('prompt') or ''
            session.metadata['seo'] = payload
        session.mark_pipeline('seo_ready')
        if session.pipeline.get('fact_checked') and session.pipeline.get(
            'draft_generated'
        ):
            session.mark_pipeline('ready_for_publication')
        session.touch()
        return payload

    def _featured_image_state(self, session: WorkspaceSession) -> dict:
        return dict(session.metadata.get('featured_image') or {})

    def _public_featured_image_state(self, state: dict) -> dict:
        """Strip internal planner fields before returning to editors."""
        public = dict(state or {})
        public.pop('planner', None)
        meta = dict(public.get('metadata') or {})
        meta.pop('planner', None)
        public['metadata'] = meta
        return public

    def prepare_featured_image_prompt(
        self,
        session: WorkspaceSession,
        *,
        image_style: str | None = None,
        reset_generated_image: bool = False,
    ) -> dict:
        """
        Plan (internal) then build an editable image prompt.

        Never builds from URL or title alone. Does not call the image provider.
        Called automatically after article generation; editors may optionally edit.
        """
        sections = session.sections
        if not (
            (sections.headline or '').strip()
            or (sections.lead or '').strip()
            or (sections.body or '').strip()
        ):
            raise ValueError(
                'Generate an article first, then prepare a featured image prompt.'
            )
        if not (sections.lead or '').strip() and not (sections.body or '').strip():
            raise ValueError(
                'Need a lead or body before preparing an image prompt '
                '(title alone is not enough).'
            )
        previous = self._featured_image_state(session)
        style = resolve_image_style(
            image_style
            if image_style is not None
            else previous.get('image_style')
        )
        publisher = (session.metadata.get('source') or {}).get('publisher') or ''
        brief = self.featured_image.prepare_brief(
            headline=sections.headline,
            lead=sections.lead,
            body=sections.body or sections.summary,
            content_type=session.resolved_content_type(),
            goal=session.resolved_goal(),
            category=sections.category,
            tags=list(sections.tags or []),
            publisher=publisher,
            image_style=style,
        )
        keep_image = not reset_generated_image
        state = {
            'prompt': brief.prompt,
            'original_prompt': brief.prompt,
            'previous_prompt': previous.get('previous_prompt')
            or previous.get('prompt')
            or '',
            'explanation': brief.explanation,
            'image_url': (previous.get('image_url') or '') if keep_image else '',
            'revised_prompt': (
                (previous.get('revised_prompt') or '') if keep_image else ''
            ),
            'provider': (previous.get('provider') or '') if keep_image else '',
            'aspect_ratio': brief.aspect_ratio,
            'image_style': style,
            'image_style_label': IMAGE_STYLE_LABELS.get(style, style),
            'status': 'prompt_ready',
            'accepted': bool(previous.get('accepted')) if keep_image else False,
            'cloudinary_public_id': (
                (previous.get('cloudinary_public_id') or '') if keep_image else ''
            ),
            'error': '',
            'auto_prepared': True,
            # Internal only — stripped from API responses.
            'planner': brief.plan_dict(),
            'metadata': {
                **dict(previous.get('metadata') or {}),
                'planner': brief.plan_dict(),
            },
        }
        session.metadata['featured_image'] = state
        seo = dict(session.metadata.get('seo') or {})
        if seo:
            seo['image_prompt'] = brief.prompt
            session.metadata['seo'] = seo
        session.last_explanations = [
            'Featured image prompt prepared automatically from the Persian article.',
            f'Style: {IMAGE_STYLE_LABELS.get(style, style)} (default Editorial Photo).',
            'Edit the prompt only if needed. Regeneration does not '
            'rewrite the article, SEO, tags, category, or summary.',
            brief.explanation,
        ]
        session.touch()
        return self._public_featured_image_state(state)

    def set_featured_image_style(
        self,
        session: WorkspaceSession,
        *,
        image_style: str,
        rebuild_prompt: bool = True,
    ) -> dict:
        """Change Editorial Photo / Illustration and optionally rebuild prompt."""
        style = resolve_image_style(image_style)
        current = self._featured_image_state(session)
        current['image_style'] = style
        current['image_style_label'] = IMAGE_STYLE_LABELS.get(style, style)
        session.metadata['featured_image'] = current
        if rebuild_prompt and (
            (session.sections.lead or '').strip()
            or (session.sections.body or '').strip()
        ):
            return self.prepare_featured_image_prompt(
                session,
                image_style=style,
            )
        session.touch()
        return self._public_featured_image_state(current)

    def generate_featured_image(
        self,
        session: WorkspaceSession,
        *,
        prompt: str | None = None,
        image_style: str | None = None,
        provider_name: str | None = None,
        regenerate: bool = False,
    ) -> dict:
        """
        Generate a featured image from the (editable) prompt.

        Regeneration updates the image only — never regenerates the article,
        SEO, tags, category, or summary. On failure, keep article + prompt.
        """
        current = self._featured_image_state(session)
        style = resolve_image_style(
            image_style if image_style is not None else current.get('image_style')
        )
        cleaned = (
            prompt if prompt is not None else current.get('prompt') or ''
        ).strip()
        if not cleaned:
            self.prepare_featured_image_prompt(session, image_style=style)
            current = self._featured_image_state(session)
            cleaned = (current.get('prompt') or '').strip()
        if not cleaned:
            raise ValueError('Image prompt is empty.')

        previous_prompt = (current.get('previous_prompt') or '').strip()
        if regenerate:
            prior_current = (current.get('prompt') or '').strip()
            if prior_current:
                previous_prompt = prior_current

        wall_started = time.monotonic()
        try:
            outcome = self.featured_image.generate(
                cleaned,
                previous_prompt=previous_prompt,
                original_prompt=current.get('original_prompt') or cleaned,
                explanation=current.get('explanation') or '',
                image_style=style,
                provider_name=provider_name,
            )
        except Exception as exc:  # noqa: BLE001
            # Keep article + prompt + previous image; surface error for retry.
            failed = dict(current)
            failed['prompt'] = cleaned
            failed['image_style'] = style
            failed['image_style_label'] = IMAGE_STYLE_LABELS.get(style, style)
            failed['status'] = 'error'
            failed['error'] = str(exc)
            # Do not drop a previously accepted / previewed image on failure.
            failed['accepted'] = bool(current.get('accepted'))
            failed['image_url'] = current.get('image_url') or ''
            failed['cloudinary_public_id'] = (
                current.get('cloudinary_public_id') or ''
            )
            failed['attached_url'] = current.get('attached_url') or ''
            failed['previous_image_url'] = current.get('previous_image_url') or ''
            session.metadata['featured_image'] = failed
            session.last_explanations = [
                'Featured image generation failed — article and prompt kept.',
                str(exc),
                'Edit the prompt or retry Generate.',
            ]
            session.touch()
            raise

        openai_seconds = float(
            (getattr(outcome, 'metadata', None) or {}).get('openai_seconds')
            or (
                ((getattr(outcome, 'metadata', None) or {}).get('duration_ms') or 0)
                / 1000.0
            )
            or 0.0
        )
        prompt_chars_api = int(
            (getattr(outcome, 'metadata', None) or {}).get('prompt_chars')
            or len(cleaned)
        )
        prompt_chars_original = int(
            (getattr(outcome, 'metadata', None) or {}).get('prompt_chars_original')
            or len(cleaned)
        )

        state = outcome.to_dict()
        state['planner'] = current.get('planner') or {}
        state['original_prompt'] = (
            current.get('original_prompt') or state.get('original_prompt') or cleaned
        )
        state['image_style'] = style
        state['image_style_label'] = IMAGE_STYLE_LABELS.get(style, style)
        # Candidate preview; draft attachment is only replaced on Accept.
        state['previous_image_url'] = (current.get('image_url') or '').strip()
        state['previous_cloudinary_public_id'] = (
            current.get('cloudinary_public_id') or ''
        )
        state['previous_attached_url'] = current.get('attached_url') or ''
        state['accepted'] = False
        state['pending_accept'] = True
        # Keep prior Cloudinary id for reference until Accept replaces it.
        state['cloudinary_public_id'] = current.get('cloudinary_public_id') or ''
        state['attached_url'] = current.get('attached_url') or ''
        state['error'] = ''

        # GPT Image returns large b64 data-URLs. Persist a CDN URL and never
        # keep multi-MB base64 blobs in the Django session.
        preview_url = (state.get('image_url') or '').strip()
        cloudinary_seconds = 0.0
        tiny_data_url = (
            preview_url.startswith('data:image/') and len(preview_url) < 8192
        )
        if preview_url.startswith('data:image/') and not tiny_data_url:
            logger.info(
                'workspace image decode/upload start: source_chars=%d session=%s',
                len(preview_url),
                getattr(session, 'session_id', ''),
            )
            upload_started = time.monotonic()
            try:
                upload = upload_featured_image_asset(
                    preview_url,
                    public_id_prefix='peyvand/editorial/featured-preview',
                    session_id=(
                        f'{getattr(session, "session_id", "") or "preview"}-gen'
                    ),
                )
                cloudinary_seconds = round(time.monotonic() - upload_started, 3)
                state['image_url'] = upload.get('secure_url') or ''
                state['preview_cloudinary_public_id'] = upload.get('public_id') or ''
                meta_clean = dict(state.get('metadata') or {})
                meta_clean.pop('b64_data_url', None)
                state['metadata'] = meta_clean
                if not state['image_url']:
                    raise FeaturedImageAttachError(
                        'Cloudinary upload returned no secure_url.'
                    )
                logger.info(
                    'workspace image Cloudinary upload: public_id=%s '
                    'seconds=%.3f url=%s',
                    state.get('preview_cloudinary_public_id'),
                    cloudinary_seconds,
                    str(state.get('image_url') or '')[:160],
                )
            except FeaturedImageAttachError as exc:
                logger.exception('workspace image Cloudinary upload failed')
                # Never persist multi-MB data URLs in session.
                state['image_url'] = current.get('image_url') or ''
                state['status'] = 'error'
                state['error'] = f'Cloudinary upload failed: {exc}'
                state['pending_accept'] = False
                session.metadata['featured_image'] = state
                session.touch()
                raise GenerationError(str(exc)) from exc
        elif tiny_data_url:
            logger.info(
                'workspace image skip CDN for tiny placeholder data-url '
                '(%d chars)',
                len(preview_url),
            )

        total_seconds = round(time.monotonic() - wall_started, 3)
        timing = {
            'prompt_chars': prompt_chars_api,
            'prompt_chars_original': prompt_chars_original,
            'openai_seconds': round(openai_seconds, 3),
            'cloudinary_seconds': round(cloudinary_seconds, 3),
            'total_seconds': total_seconds,
        }
        state['timing'] = timing
        logger.info(
            'workspace image timing: prompt_chars=%s openai=%.3fs '
            'cloudinary=%.3fs total=%.3fs session=%s',
            timing['prompt_chars'],
            timing['openai_seconds'],
            timing['cloudinary_seconds'],
            timing['total_seconds'],
            getattr(session, 'session_id', ''),
        )

        if regenerate and not state.get('previous_prompt'):
            state['previous_prompt'] = previous_prompt
        meta = dict(state.get('metadata') or {})
        if current.get('planner'):
            meta['planner'] = current.get('planner')
        meta['timing'] = timing
        state['metadata'] = meta
        session.metadata['featured_image'] = state
        logger.info(
            'workspace image session save: status=%s image_url_chars=%d',
            state.get('status'),
            len(str(state.get('image_url') or '')),
        )
        seo = dict(session.metadata.get('seo') or {})
        seo['image_prompt'] = cleaned
        session.metadata['seo'] = seo
        session.mark_pipeline('image_ready')
        session.last_explanations = [
            (
                'Featured image regenerated (article, SEO, tags, category, '
                'summary unchanged). Accept to replace the draft featured image.'
                if regenerate
                else 'Featured image generated — review, then Accept to attach.'
            ),
            state.get('explanation') or '',
            f'Style: {IMAGE_STYLE_LABELS.get(style, style)}.',
            f'Provider: {state.get("provider") or "—"}.',
            (
                f'Timing — OpenAI: {timing["openai_seconds"]} s · '
                f'Cloudinary: {timing["cloudinary_seconds"]} s · '
                f'Total: {timing["total_seconds"]} s'
            ),
        ]
        session.last_explanations = [
            item for item in session.last_explanations if item
        ]
        session.touch()
        return self._public_featured_image_state(state)

    def restore_original_image_prompt(self, session: WorkspaceSession) -> dict:
        """Restore the originally generated prompt (before editor edits)."""
        current = self._featured_image_state(session)
        original = (current.get('original_prompt') or '').strip()
        if not original:
            raise ValueError('No original image prompt is available.')
        state = dict(current)
        state['previous_prompt'] = (current.get('prompt') or '').strip()
        state['prompt'] = original
        state['status'] = 'prompt_ready'
        state['error'] = ''
        session.metadata['featured_image'] = state
        session.last_explanations = [
            'Restored the original AI featured image prompt. Article unchanged.',
        ]
        session.touch()
        return self._public_featured_image_state(state)

    def save_image_prompt_edits(
        self,
        session: WorkspaceSession,
        *,
        prompt: str,
    ) -> dict:
        """Persist optional editor edits to the image prompt (not the article)."""
        current = self._featured_image_state(session)
        cleaned = (prompt or '').strip()
        if not cleaned:
            raise ValueError('Image prompt cannot be empty.')
        if not (current.get('original_prompt') or '').strip():
            current['original_prompt'] = cleaned
        state = dict(current)
        state['previous_prompt'] = (current.get('prompt') or '').strip()
        state['prompt'] = cleaned
        state['status'] = current.get('status') or 'prompt_ready'
        state['error'] = ''
        session.metadata['featured_image'] = state
        seo = dict(session.metadata.get('seo') or {})
        seo['image_prompt'] = cleaned
        session.metadata['seo'] = seo
        session.last_explanations = [
            'Saved image prompt edits. Article unchanged.',
        ]
        session.touch()
        return self._public_featured_image_state(state)

    def use_previous_image_prompt(self, session: WorkspaceSession) -> dict:
        """Restore the previous featured-image prompt into the editable field."""
        current = self._featured_image_state(session)
        previous = (current.get('previous_prompt') or '').strip()
        if not previous:
            raise ValueError('No previous image prompt is available.')
        state = dict(current)
        state['previous_prompt'] = (current.get('prompt') or '').strip()
        state['prompt'] = previous
        state['status'] = 'prompt_ready'
        state['error'] = ''
        session.metadata['featured_image'] = state
        session.last_explanations = [
            'Restored the previous featured image prompt. Article unchanged.',
        ]
        session.touch()
        return self._public_featured_image_state(state)

    def accept_featured_image(
        self,
        session: WorkspaceSession,
        *,
        user,
    ) -> dict:
        """
        Accept the generated image: upload to Cloudinary and attach to the
        Blog draft as featured_image. Creates/updates the draft if needed.
        """
        current = self._featured_image_state(session)
        image_url = (current.get('image_url') or '').strip()
        if not image_url:
            raise ValueError('Generate an image before accepting it.')
        if current.get('status') == 'error':
            raise ValueError('Cannot accept a failed image — regenerate first.')

        blog_draft = self.save_blog_draft(session, user=user)
        post_id = blog_draft.get('post_id')
        if not post_id:
            raise ValueError('Could not link a Blog draft for the featured image.')

        from blog.models import Post

        post = Post.objects.get(pk=post_id)
        upload = upload_featured_image_asset(
            image_url,
            session_id=session.session_id or str(post_id),
        )
        attach_featured_image_to_post(post, public_id=upload['public_id'])

        state = dict(current)
        state['accepted'] = True
        state['pending_accept'] = False
        state['status'] = 'accepted'
        state['cloudinary_public_id'] = upload['public_id']
        state['attached_url'] = upload.get('secure_url') or image_url
        state['previous_image_url'] = current.get('previous_image_url') or ''
        state['error'] = ''
        state['attached_post_id'] = post.pk
        session.metadata['featured_image'] = state
        session.mark_pipeline('image_ready')
        session.last_explanations = [
            'Featured image accepted and attached to the Blog draft.',
            f'Cloudinary: {upload["public_id"]}.',
            'Article, SEO, tags, category and summary were not regenerated.',
        ]
        session.touch()
        public = self._public_featured_image_state(state)
        public['blog_draft'] = blog_draft
        return public

    def import_existing_article(
        self,
        session: WorkspaceSession,
        *,
        post_id,
    ) -> WorkspaceSession:
        """Load an existing Blog post into source material (read-only import)."""
        if not post_id:
            raise ValueError('post_id is required to import an article.')
        from blog.models import Post

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist as exc:
            raise ValueError(f'Post {post_id!r} was not found.') from exc
        body = post.content or ''
        session.source_url = ''
        session.source_material = str(body).strip()
        session.sections = ArticleSections(
            headline=post.title or '',
            lead='',
            body='',
            summary='',
            category=session.sections.category,
            tags=list(session.sections.tags),
        )
        session.research_notes = (
            f'Imported from existing article #{post.pk}: {post.title}\n'
            'Edit research notes before generating a new draft.'
        )
        session.metadata['imported_post_id'] = post.pk
        session.metadata['linked_post_id'] = post.pk
        session.metadata['source'] = {
            'source_id': f'blog-post-{post.pk}',
            'title': post.title or '',
            'publisher': '',
            'url': '',
            'source_type': 'blog_post',
            'warnings': [],
            'retrieval': 'blog_import',
        }
        session.metadata['source_binding'] = build_source_binding(
            session_id=session.session_id,
            source_url='',
            source_text=session.source_material,
            retrieval='blog_import',
        )
        session.workflow_state = WorkflowState.RESEARCHING
        session.mark_pipeline('source_imported', 'metadata_extracted')
        self._classify_session(
            session,
            title=post.title or '',
            text=session.source_material,
            url='',
            publisher='',
        )
        session.touch()
        return session

    def save_blog_draft(self, session: WorkspaceSession, *, user) -> dict:
        """
        Persist workspace sections as a Blog Draft Post.

        Creates a new Draft when none is linked; updates the linked Draft when
        present. Never publishes. Blog Draft is the canonical editable content.
        """
        import logging

        from django.urls import reverse

        from blog.models import Post
        from content_ai.editorial.drafts import EditorialDraft
        from content_ai.editorial.persistence import (
            BlogDraftPersistenceError,
            BlogDraftPersistenceService,
        )

        logger = logging.getLogger(__name__)
        logger.info(
            'save_blog_draft ENTER session=%s user=%s',
            getattr(session, 'session_id', None),
            getattr(user, 'username', None),
        )

        if user is None or not getattr(user, 'is_authenticated', False):
            raise ValueError('Authentication required to save a Blog draft.')

        headline = (session.sections.headline or '').strip()
        body = (session.sections.body or '').strip()
        lead = (session.sections.lead or '').strip()
        if not headline and not body and not lead:
            logger.warning('save_blog_draft SKIP empty sections')
            raise ValueError(
                'Add a headline, lead, or body before saving a Blog draft.'
            )

        persistence = BlogDraftPersistenceService()
        category = persistence.resolve_category(session.sections.category)
        session.sections.category = category.name

        featured = self._featured_image_state(session)
        featured_meta = {
            'prompt': featured.get('prompt') or '',
            'original_prompt': featured.get('original_prompt') or '',
            'image_style': featured.get('image_style') or '',
            'image_style_label': featured.get('image_style_label') or '',
            'aspect_ratio': featured.get('aspect_ratio') or '16:9',
            'status': featured.get('status') or '',
            'cloudinary_public_id': featured.get('cloudinary_public_id') or '',
            'accepted': bool(featured.get('accepted')),
            'image_url': featured.get('image_url') or '',
            'attached_url': featured.get('attached_url') or '',
        }

        draft = EditorialDraft(
            title=headline or 'Untitled AI draft',
            lead=lead,
            body=body,
            summary=(
                session.sections.summary
                or session.sections.excerpt
                or lead
            ),
            language=session.language,
            metadata={
                'category': category.name,
                'tags': list(session.sections.tags),
                'source_url': session.source_url,
                'content_type': session.resolved_content_type(),
                'goal': session.resolved_goal(),
                'template_id': session.template_id,
                'workspace_session_id': session.session_id,
                'featured_image': featured_meta,
            },
        )

        linked_id = (
            session.metadata.get('linked_post_id')
            or session.metadata.get('imported_post_id')
        )
        created = False
        post = None
        if linked_id:
            try:
                candidate = Post.objects.get(pk=linked_id)
            except Post.DoesNotExist:
                candidate = None
            if (
                candidate is not None
                and candidate.status == BlogDraftPersistenceService.DRAFT_STATUS
                and not candidate.is_deleted
            ):
                try:
                    logger.info(
                        'save_blog_draft calling update_blog_draft post_id=%s',
                        candidate.pk,
                    )
                    post = persistence.update_blog_draft(
                        candidate,
                        draft,
                        category=category,
                        source_url=session.source_url or '',
                    )
                except BlogDraftPersistenceError as exc:
                    logger.exception('save_blog_draft update_blog_draft FAILED')
                    raise ValueError(str(exc)) from exc

        if post is None:
            logger.info('save_blog_draft calling create_blog_draft')
            try:
                post = persistence.create_blog_draft(
                    draft,
                    author=user,
                    category=category,
                    source_url=session.source_url or '',
                )
                created = True
                logger.info(
                    'save_blog_draft create_blog_draft OK post_id=%s status=%s',
                    post.pk,
                    post.status,
                )
            except BlogDraftPersistenceError as exc:
                logger.exception('save_blog_draft create_blog_draft FAILED')
                raise ValueError(str(exc)) from exc

        # Keep an already-accepted featured image attached on Save Draft.
        if featured_meta.get('accepted') and featured_meta.get('cloudinary_public_id'):
            try:
                attach_featured_image_to_post(
                    post,
                    public_id=featured_meta['cloudinary_public_id'],
                )
            except FeaturedImageAttachError as exc:
                logger.warning(
                    'save_blog_draft could not re-attach featured image: %s',
                    exc,
                )

        admin_url = reverse('admin:blog_post_change', args=[post.pk])
        blog_draft = {
            'post_id': post.pk,
            'title': post.title,
            'status': 'draft',
            'created': created,
            'admin_url': admin_url,
            'category': post.category.name if post.category_id else '',
            'tags': list(session.sections.tags),
            'source_url': session.source_url or post.external_url or '',
            'featured_image': featured_meta,
        }
        session.metadata['linked_post_id'] = post.pk
        session.metadata['blog_draft'] = blog_draft
        session.metadata['featured_image_saved'] = featured_meta
        session.mark_pipeline('draft_generated', 'ready_for_publication')
        session.workflow_state = WorkflowState.READY_FOR_APPROVAL
        session.last_explanations = [
            (
                'Created Blog draft #{}.'.format(post.pk)
                if created
                else 'Updated Blog draft #{}.'.format(post.pk)
            ),
            'Draft is now visible under Admin → Posts → Draft Posts.',
            f'Open draft: {admin_url}',
            'Continue editing in Blog Admin or return here to revise.',
        ]
        if featured_meta.get('accepted') and featured_meta.get('cloudinary_public_id'):
            session.last_explanations.append(
                'Featured image, prompt, and style metadata saved with the draft.'
            )
        session.push_history(
            'Saved Blog draft',
            session.last_explanations[0],
        )
        session.touch()
        return blog_draft

    def publish_blog_draft(self, session: WorkspaceSession, *, user) -> dict:
        """
        Publish the linked Blog Draft Post (explicit staff action).

        Never auto-publishes: requires a linked draft and an authenticated
        staff-triggered API call. Syncs latest workspace sections before publish.
        """
        from django.urls import reverse

        from blog.models import Post
        from content_ai.editorial.persistence import BlogDraftPersistenceService

        if user is None or not getattr(user, 'is_authenticated', False):
            raise ValueError('Authentication required to publish a Blog draft.')

        linked_id = (
            session.metadata.get('linked_post_id')
            or session.metadata.get('imported_post_id')
        )
        post = None
        if linked_id:
            try:
                post = Post.objects.get(pk=linked_id)
            except Post.DoesNotExist:
                post = None

        # Sync latest editor text only while the linked post is still a draft.
        if post is None or (
            post.status == BlogDraftPersistenceService.DRAFT_STATUS
            and not post.is_deleted
        ):
            blog_draft = self.save_blog_draft(session, user=user)
            post_id = blog_draft.get('post_id')
            if not post_id:
                raise ValueError('No Blog draft is linked to this workspace session.')
            post = Post.objects.get(pk=post_id)
        elif post.is_deleted:
            raise ValueError('Cannot publish a deleted Blog draft.')

        if post.status != 1:
            post.status = 1
            post.save(update_fields=['status', 'updated_on'])

        public_url = reverse('post_detail', kwargs={'slug': post.slug})
        admin_url = reverse('admin:blog_post_change', args=[post.pk])
        published = {
            'post_id': post.pk,
            'title': post.title,
            'status': 'published',
            'slug': post.slug,
            'public_url': public_url,
            'admin_url': admin_url,
            'category': post.category.name if post.category_id else '',
        }
        session.metadata['linked_post_id'] = post.pk
        session.metadata['blog_draft'] = {
            **dict(session.metadata.get('blog_draft') or {}),
            **published,
            'created': False,
        }
        session.metadata['publish_success'] = published
        session.workflow_state = WorkflowState.PUBLISHED
        session.mark_pipeline('ready_for_publication')
        session.last_explanations = [
            f'Published Blog article #{post.pk}.',
            f'Public URL: {public_url}',
            'Use “Create another article” to start a clean workspace session.',
        ]
        session.push_history('Published Blog article', session.last_explanations[0])
        session.touch()
        return published

    def advance_workflow(
        self,
        session: WorkspaceSession,
        target: WorkflowState,
    ) -> WorkspaceSession:
        # Manual movement only for safe editorial states.
        allowed_manual = {
            WorkflowState.RESEARCHING,
            WorkflowState.DRAFTING,
            WorkflowState.REVIEWING,
            WorkflowState.REVISION_REQUIRED,
            WorkflowState.READY_FOR_APPROVAL,
            WorkflowState.APPROVED,
        }
        if target == WorkflowState.PUBLISHED or target not in allowed_manual:
            raise ValueError(
                f'Manual transition to {target.value!r} is not allowed '
                '(no auto-publish from workspace).'
            )
        from content_ai.workflow.states import can_transition

        if not can_transition(session.workflow_state, target):
            # Allow editor to set review-oriented states even if skipping stubs.
            if target not in {
                WorkflowState.REVIEWING,
                WorkflowState.READY_FOR_APPROVAL,
                WorkflowState.APPROVED,
                WorkflowState.REVISION_REQUIRED,
                WorkflowState.DRAFTING,
                WorkflowState.RESEARCHING,
            }:
                raise ValueError(
                    f'Invalid workflow move '
                    f'{session.workflow_state.value} → {target.value}.'
                )
        if target in {
            WorkflowState.READY_FOR_APPROVAL,
            WorkflowState.APPROVED,
        }:
            session.mark_pipeline('ready_for_publication')
        session.workflow_state = target
        session.last_explanations = [
            f'Workflow stage set to {target.value} (human-controlled).',
            'Publishing still requires Blog Admin Save / approval.',
        ]
        session.touch()
        return session
