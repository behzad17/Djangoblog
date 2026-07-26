"""Source inspector — manual text and URL fetch ingest (RFC-006 / APF-001)."""

from __future__ import annotations

from content_ai.source.extract import (
    EXTRACTION_FAILED_MESSAGE,
    ArticleExtractionError,
    extract_article_from_url,
)
from content_ai.source.models import SourceRecord, create_source_record


class SourceInspector:
    """
    Inspect source material for the Editorial Workspace.

    - Pasted text is used as-is.
    - When a URL is provided without text, fetches HTML and extracts the
      main article body + metadata.
    - Does not invent content when extraction fails — raises instead.
    """

    def __init__(self, extractor=None):
        self._extractor = extractor

    @property
    def extractor(self):
        return self._extractor or extract_article_from_url

    def inspect(
        self,
        *,
        url: str = '',
        text: str = '',
        title: str = '',
        publisher: str = '',
        language: str = '',
        fetch: bool = True,
    ) -> SourceRecord:
        incoming_url = (url or '').strip()
        incoming_text = (text or '').strip()
        warnings = ['Trust score is a placeholder.']

        if incoming_url and not incoming_text and fetch:
            try:
                article = self.extractor(incoming_url)
            except ArticleExtractionError as exc:
                message = str(exc).strip() or EXTRACTION_FAILED_MESSAGE
                if 'Unable to extract article content' not in message:
                    message = EXTRACTION_FAILED_MESSAGE
                raise ArticleExtractionError(message) from exc

            body = (article.text or '').strip()
            if not body:
                raise ArticleExtractionError(EXTRACTION_FAILED_MESSAGE)

            detected_language = (
                article.detected_language or language or ''
            )
            return create_source_record(
                title=(title or '').strip() or article.title,
                publisher=(publisher or '').strip() or article.publisher,
                url=article.url or incoming_url,
                publication_date=article.publication_date,
                detected_language=detected_language,
                detected_country=article.detected_country,
                source_type='url',
                trust_score=None,
                raw_text=body,
                warnings=warnings + [
                    'Fetched HTML and extracted readable article content.',
                ],
                metadata={
                    'inspector': 'url_fetch',
                    'retrieval': 'url_fetch',
                    'domain': article.domain,
                    'extraction': dict(article.metadata or {}),
                },
            )

        source_type = 'url' if incoming_url else 'text'
        if incoming_url and not incoming_text:
            warnings.append('No external retrieval.')
            warnings.append(
                'URL recorded only — content was not fetched automatically.'
            )
        detected_language = language or ''
        sample = incoming_text or title or ''
        if any('\u0600' <= c <= '\u06FF' for c in sample):
            detected_language = detected_language or 'fa'
        return create_source_record(
            title=title or (incoming_url[:80] if incoming_url else 'Untitled source'),
            publisher=publisher,
            url=incoming_url,
            detected_language=detected_language,
            source_type=source_type,
            trust_score=None,
            raw_text=incoming_text,
            warnings=warnings,
            metadata={
                'inspector': 'manual',
                'retrieval': (
                    'manual_paste' if incoming_text else 'url_only_no_fetch'
                ),
            },
        )
