"""Editorial Studio — News Import service (ES-001).

Fetches a news URL, extracts readable content, and runs the production
editorial generation pipeline (WorkflowOrchestrator via EditorialAIService).
Does not publish.
"""

from __future__ import annotations

from urllib.parse import urlparse

from content_ai.editorial.service import EditorialAIService
from content_ai.providers.exceptions import GenerationError
from content_ai.source.extract import (
    ArticleExtractionError,
    ExtractedArticle,
    extract_article_from_url,
)
from content_ai.source.inspector import SourceInspector

PERSIAN_NEWS_INSTRUCTIONS = (
    'Write a Persian editorial draft for the Iranian community in Sweden. '
    'Base the draft only on the provided source article. Preserve key facts, '
    'names, dates, and figures. Do not invent information. Use clear, '
    'community-facing Persian.'
)


class NewsImportService:
    """One-shot news URL → Persian draft via the production AI workflow."""

    def __init__(
        self,
        editorial: EditorialAIService | None = None,
        extractor=extract_article_from_url,
    ):
        self.editorial = editorial or EditorialAIService()
        self.extractor = extractor

    def import_news(
        self,
        url: str,
        *,
        provider_name: str | None = None,
    ) -> dict:
        """
        Extract article from ``url`` and generate a Persian draft.

        Returns a JSON-serialisable payload with source info, draft, and
        workflow metadata. Raises ArticleExtractionError or GenerationError.
        """
        article = self.extractor(url)
        source_meta = self._source_metadata(article)
        draft = self.editorial.generate_draft(
            title=article.title,
            source=article.url,
            language='fa',
            category='news',
            context=article.text,
            instructions=PERSIAN_NEWS_INSTRUCTIONS,
            provider_name=provider_name,
        )
        metadata = dict(draft.metadata or {})
        telemetry = draft.telemetry
        return {
            'source': source_meta,
            'title': draft.title or article.title,
            'draft': draft.body,
            'language': draft.language or 'fa',
            'metadata': {
                'source_url': article.url,
                'source_domain': source_meta.get('domain', ''),
                'detected_language': source_meta.get('detected_language', ''),
                'workflow_stages': metadata.get('workflow_stages') or [],
                'workflow_state': metadata.get('workflow_state') or '',
                'provider': (
                    draft.metadata.get('provider')
                    or (telemetry.provider if telemetry else '')
                    or metadata.get('provider')
                    or ''
                ),
                'duration_ms': (
                    telemetry.duration_ms if telemetry else None
                ),
                'prompt_version': metadata.get('prompt_version') or '',
                'intelligence': metadata.get('intelligence') or {},
                'warnings': list(draft.metadata.get('warnings') or []),
            },
        }

    def _source_metadata(self, article: ExtractedArticle) -> dict:
        record = SourceInspector().inspect(
            url=article.url,
            text=article.text,
            title=article.title,
            language=article.detected_language,
        )
        domain = article.domain or urlparse(article.url).netloc
        return {
            'url': article.url,
            'domain': domain,
            'title': article.title,
            'source_type': record.source_type,
            'detected_language': (
                record.detected_language or article.detected_language
            ),
            'trust_score': record.trust_score,
            'excerpt': (article.text[:400] + '…')
            if len(article.text) > 400
            else article.text,
            'warnings': list(record.warnings),
        }


__all__ = [
    'ArticleExtractionError',
    'GenerationError',
    'NewsImportService',
    'PERSIAN_NEWS_INSTRUCTIONS',
]
