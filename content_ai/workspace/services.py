"""Workspace service — compose existing AI layers (APF-001)."""

from __future__ import annotations

from content_ai.editorial.service import EditorialAIService
from content_ai.evaluation.evaluator import Evaluator
from content_ai.evaluation.snapshot import create_snapshot
from content_ai.fact_check import FactChecker
from content_ai.source import SourceInspector
from content_ai.workflow import WorkflowOrchestrator, WorkflowState
from content_ai.workspace.actions import get_action
from content_ai.workspace.session import ArticleSections, WorkspaceSession


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

    Does not publish. Does not replace Blog Admin article creation.
    """

    def __init__(
        self,
        editorial: EditorialAIService | None = None,
        source_inspector: SourceInspector | None = None,
        fact_checker: FactChecker | None = None,
        evaluator: Evaluator | None = None,
        workflow: WorkflowOrchestrator | None = None,
    ):
        self.editorial = editorial or EditorialAIService()
        self.source_inspector = source_inspector or SourceInspector()
        self.fact_checker = fact_checker or FactChecker()
        self.evaluator = evaluator or Evaluator()
        self.workflow = workflow or WorkflowOrchestrator()

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
        record = self.source_inspector.inspect(
            url=url,
            text=text,
            title=title,
            publisher=publisher,
            language=session.language,
        )
        session.source_url = record.url
        session.source_material = record.raw_text or text
        session.research_notes = self._research_notes(record)
        session.workflow_state = WorkflowState.RESEARCHING
        session.last_explanations = [
            'Source material recorded for editorial research.',
            'Trust score and classification are placeholders (RFC-006 stub).',
        ]
        session.metadata['source'] = {
            'source_id': record.source_id,
            'title': record.title,
            'publisher': record.publisher,
            'url': record.url,
            'detected_language': record.detected_language,
            'detected_country': record.detected_country,
            'source_type': record.source_type,
            'trust_score': record.trust_score,
            'freshness': record.freshness,
            'classification': record.classification,
            'warnings': list(record.warnings),
        }
        session.touch()
        return session.metadata['source']

    def _research_notes(self, record) -> str:
        lines = [
            f'Source: {record.title or "(untitled)"}',
            f'Type: {record.source_type}',
            f'Language: {record.detected_language or "unknown"}',
            'Entities: (manual review — auto NER not implemented)',
            'Topics: (manual review)',
            'Possible missing information: verify dates, agency names, numbers.',
            'Related sources: (future RFC-006)',
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
    ) -> WorkspaceSession:
        working_title = title or session.sections.headline or 'Untitled draft'
        context = '\n\n'.join(
            part
            for part in (
                session.source_material,
                session.research_notes,
            )
            if part
        )
        draft = self.editorial.generate_draft(
            title=working_title,
            language=session.language,
            category=category or session.sections.category,
            context=context,
            instructions=instructions,
            provider_name=provider_name,
        )
        lead, body = _split_draft_body(draft.body)
        session.sections = ArticleSections(
            headline=draft.title or working_title,
            lead=lead,
            body=body or draft.body,
            summary=draft.summary or '',
            category=category or session.sections.category,
            tags=list(session.sections.tags),
            excerpt=(draft.summary or lead)[:300],
        )
        session.workflow_state = WorkflowState.DRAFTING
        session.last_explanations = [
            'Draft generated via EditorialAIService (existing pipeline).',
            'Sections are independently editable; regenerate one section at a time.',
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
        )
        explanation = f'{section} regenerated independently.'
        if section == 'headline':
            session.sections.headline = focused.title or focused.body.strip().split('\n')[0]
        elif section == 'lead':
            lead, _ = _split_draft_body(focused.body)
            session.sections.lead = lead or focused.body
        elif section == 'body':
            _, body = _split_draft_body(focused.body)
            session.sections.body = body or focused.body
        elif section == 'summary':
            session.sections.summary = focused.summary or focused.body[:400]
        elif section == 'excerpt':
            session.sections.excerpt = (focused.summary or focused.body)[:300]
        elif section == 'category':
            session.sections.category = focused.metadata.get('category') or session.sections.category
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
        session.touch()
        return payload

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
        session.source_material = str(body)
        session.sections.headline = post.title or session.sections.headline
        session.research_notes = (
            f'Imported from existing article #{post.pk}: {post.title}\n'
            'Edit research notes before generating a new draft.'
        )
        session.metadata['imported_post_id'] = post.pk
        session.workflow_state = WorkflowState.RESEARCHING
        session.last_explanations = [
            f'Imported article #{post.pk} as source material.',
            'Import does not modify or publish the original post.',
        ]
        session.touch()
        return session

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
        session.workflow_state = target
        session.last_explanations = [
            f'Workflow stage set to {target.value} (human-controlled).',
            'Publishing still requires Blog Admin Save / approval.',
        ]
        session.touch()
        return session
