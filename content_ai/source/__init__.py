"""Source Intelligence package (RFC-006 / ES-001 extraction).

Passive credibility scoring remains stubbed. Article URL fetch/extract is
implemented for Editorial Studio News Import.
"""

from content_ai.source.extract import (
    ArticleExtractionError,
    ExtractedArticle,
    extract_article_from_url,
    extract_readable_content,
    fetch_url_html,
    validate_news_url,
)
from content_ai.source.inspector import SourceInspector
from content_ai.source.models import SourceRecord, create_source_record

__all__ = [
    'ArticleExtractionError',
    'ExtractedArticle',
    'SourceInspector',
    'SourceRecord',
    'create_source_record',
    'extract_article_from_url',
    'extract_readable_content',
    'fetch_url_html',
    'validate_news_url',
]
