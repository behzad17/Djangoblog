"""Editorial Studio — Smart News Import (ES-001A).

Fetches a URL, extracts readable content, and runs the production editorial
generation pipeline (WorkflowOrchestrator via EditorialAIService).
Returns a structured Persian draft. Does not publish, edit, or save.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from content_ai.editorial.service import EditorialAIService
from content_ai.editorial.structured import parse_structured_draft
from content_ai.providers.exceptions import GenerationError
from content_ai.source.extract import (
    ArticleExtractionError,
    ExtractedArticle,
    extract_article_from_url,
)
from content_ai.source.inspector import SourceInspector

CONTENT_TYPES = (
    'auto',
    'news',
    'government',
    'research',
    'press_release',
)

OUTPUT_MODES = (
    'publish_ready',
    'educational',
    'summary',
)

CONTENT_TYPE_LABELS = {
    'news': 'news article',
    'government': 'government information',
    'research': 'research / analysis',
    'press_release': 'press release',
}

OUTPUT_MODE_INSTRUCTIONS = {
    'publish_ready': (
        'Produce a publish-ready Persian news draft suitable for Peyvand.'
    ),
    'educational': (
        'Produce an educational Persian article that explains what happened, '
        'why it matters for the Iranian community in Sweden, impact, and '
        'practical guidance. Keep facts grounded in the source.'
    ),
    'summary': (
        'Produce a concise Persian summary draft with a clear lead and short body. '
        'Keep only the most important facts from the source.'
    ),
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _contains_word(blob: str, *tokens: str) -> bool:
    return any(re.search(rf'\b{re.escape(token)}\b', blob) for token in tokens)


def detect_content_type(article: ExtractedArticle) -> str:
    """Lightweight content-type hint from URL/title/text (no LLM call)."""
    blob = ' '.join(
        [
            article.url or '',
            article.domain or '',
            article.title or '',
            (article.text or '')[:800],
        ]
    ).lower()
    # Avoid bare "kommun" — common in ordinary municipal news.
    if _contains_word(
        blob,
        'regeringen',
        'myndigheten',
        'myndighet',
        'förordning',
        'riksdagen',
        'riksdag',
        'skatteverket',
        'migrationsverket',
        'government',
    ) or any(
        token in blob
        for token in ('skatteverket.se', 'migrationsverket.se', 'regeringen.se')
    ):
        return 'government'
    if _contains_word(blob, 'pressmeddelande') or any(
        token in blob for token in ('press release', 'press-release')
    ):
        return 'press_release'
    if _contains_word(
        blob, 'studie', 'forskning', 'rapport', 'research', 'analysis'
    ):
        return 'research'
    return 'news'


def source_name_from_domain(domain: str) -> str:
    host = (domain or '').strip().lower()
    if host.startswith('www.'):
        host = host[4:]
    if not host:
        return 'Unknown source'
    # Keep IPs / localhost readable (avoid "127" from 127.0.0.1).
    first = host.split('.')[0]
    if first.isdigit() or host in {'localhost'} or ':' in host.split('.')[0]:
        return host
    # Prefer first label as a readable source name (e.g. svd.se → SVD).
    return first.upper() if len(first) <= 5 else first.capitalize()


def build_instructions(
    *,
    content_type: str,
    output_mode: str,
) -> str:
    type_label = CONTENT_TYPE_LABELS.get(content_type, 'news article')
    mode_instruction = OUTPUT_MODE_INSTRUCTIONS.get(
        output_mode,
        OUTPUT_MODE_INSTRUCTIONS['publish_ready'],
    )
    return (
        f'The source is a {type_label}. {mode_instruction} '
        'Keep facts grounded in the source; do not invent details.'
    )


class NewsImportService:
    """Smart news URL → structured Persian draft via production AI workflow."""

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
        content_type: str = 'auto',
        output_mode: str = 'publish_ready',
        provider_name: str | None = None,
    ) -> dict:
        """
        Extract article from ``url`` and generate a structured Persian draft.

        Raises ArticleExtractionError or GenerationError with editor-facing
        messages where possible.
        """
        content_type = (content_type or 'auto').strip().lower()
        output_mode = (output_mode or 'publish_ready').strip().lower()
        if content_type not in CONTENT_TYPES:
            raise ArticleExtractionError(
                'Unknown content type. Choose Auto Detect, News, '
                'Government Information, Research, or Press Release.'
            )
        if output_mode not in OUTPUT_MODES:
            raise ArticleExtractionError(
                'Unknown output mode. Choose Publish-ready News, '
                'Educational Article, or Summary.'
            )

        article = self.extractor(url)
        resolved_type = (
            detect_content_type(article)
            if content_type == 'auto'
            else content_type
        )
        source_meta = self._source_metadata(article)
        category_hint = {
            'news': 'news',
            'government': 'laws',
            'research': 'news',
            'press_release': 'news',
        }.get(resolved_type, 'news')

        draft = self.editorial.generate_draft(
            title=article.title,
            source=article.url,
            language='fa',
            category=category_hint,
            context=article.text,
            instructions=build_instructions(
                content_type=resolved_type,
                output_mode=output_mode,
            ),
            provider_name=provider_name,
        )

        metadata = dict(draft.metadata or {})
        telemetry = draft.telemetry
        provider = (
            (telemetry.provider if telemetry else '')
            or metadata.get('provider')
            or ''
        )
        duration_ms = telemetry.duration_ms if telemetry else None
        source_language = (
            source_meta.get('detected_language')
            or article.detected_language
            or 'sv'
        )
        output_language = draft.language or 'fa'
        suggested_category = (
            metadata.get('suggested_category') or category_hint or 'news'
        )
        suggested_tags = list(metadata.get('suggested_tags') or [])
        summary = draft.summary or draft.lead or ''

        return {
            'title': draft.title,
            'lead': draft.lead,
            'body': draft.body,
            'summary': summary,
            'short_summary': summary,
            'suggested_category': suggested_category,
            'suggested_tags': suggested_tags,
            'source_url': article.url,
            'source_name': source_meta.get('name') or '',
            'language': output_language,
            'source_language': source_language,
            'output_language': output_language,
            'content_type': resolved_type,
            'content_type_requested': content_type,
            'output_mode': output_mode,
            # Back-compat for earlier ES-001 clients/tests.
            'draft': draft.body,
            'source': source_meta,
            'source_title': article.title,
            'workflow_stages': metadata.get('workflow_stages') or [],
            'provider': provider,
            'duration_ms': duration_ms,
            'generated_at': _utc_now_iso(),
            'metadata': {
                'source_url': article.url,
                'source_name': source_meta.get('name') or '',
                'source_domain': source_meta.get('domain', ''),
                'source_title': article.title,
                'language': output_language,
                'detected_language': source_language,
                'content_type': resolved_type,
                'output_mode': output_mode,
                'workflow_stages': metadata.get('workflow_stages') or [],
                'provider': provider,
                'duration_ms': duration_ms,
                'generation_passes': metadata.get('generation_passes') or [],
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
            'name': source_name_from_domain(domain),
            'title': article.title,
            'source_type': record.source_type,
            'detected_language': (
                record.detected_language or article.detected_language
            ),
        }


__all__ = [
    'CONTENT_TYPES',
    'OUTPUT_MODES',
    'ArticleExtractionError',
    'GenerationError',
    'NewsImportService',
    'build_instructions',
    'detect_content_type',
    'parse_structured_draft',
    'source_name_from_domain',
]
