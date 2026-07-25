"""Fetch a news URL and extract readable article content.

Uses the standard library only (urllib + html.parser). Does not invent a
vendor crawler stack; this is the concrete extractor behind Source package
URL ingest for Editorial Studio News Import (ES-001).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class ArticleExtractionError(Exception):
    """Raised when a URL cannot be fetched or readable content is missing."""


@dataclass(frozen=True, slots=True)
class ExtractedArticle:
    """Readable article payload extracted from a news URL."""

    url: str
    title: str
    text: str
    domain: str
    detected_language: str = ''


class _ReadableHTMLParser(HTMLParser):
    """Collect title and visible text; skip script/style/nav chrome."""

    _SKIP_TAGS = frozenset(
        {
            'script',
            'style',
            'noscript',
            'svg',
            'iframe',
            'nav',
            'footer',
            'header',
            'aside',
            'form',
            'button',
        }
    )

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.h1_parts: list[str] = []
        self.article_parts: list[str] = []
        self.body_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False
        self._in_h1 = False
        self._in_article = False
        self._in_p = False
        self._capture_p = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == 'title':
            self._in_title = True
        elif tag == 'h1':
            self._in_h1 = True
        elif tag == 'article':
            self._in_article = True
        elif tag in {'p', 'li', 'h2', 'h3'}:
            self._in_p = True
            self._capture_p = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self._SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == 'title':
            self._in_title = False
        elif tag == 'h1':
            self._in_h1 = False
        elif tag == 'article':
            self._in_article = False
        elif tag in {'p', 'li', 'h2', 'h3'}:
            if self._capture_p:
                bucket = (
                    self.article_parts if self._in_article else self.body_parts
                )
                if bucket and not bucket[-1].endswith('\n'):
                    bucket.append('\n')
            self._in_p = False
            self._capture_p = False

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = (data or '').strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        if self._in_h1:
            self.h1_parts.append(text)
        if self._capture_p or self._in_p:
            bucket = self.article_parts if self._in_article else self.body_parts
            bucket.append(text)
            bucket.append(' ')


def _normalise_whitespace(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text or '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _detect_language_hint(text: str) -> str:
    sample = text or ''
    if any('\u0600' <= c <= '\u06FF' for c in sample):
        return 'fa'
    # Light Swedish/Latin heuristic for ES-001 metadata only.
    lowered = sample.lower()
    swedish_markers = (' och ', ' det ', ' att ', ' för ', ' är ', ' på ')
    if any(marker in f' {lowered} ' for marker in swedish_markers):
        return 'sv'
    return ''


def validate_news_url(url: str) -> str:
    """Validate and normalise an http(s) news URL."""
    raw = (url or '').strip()
    if not raw:
        raise ArticleExtractionError('Please paste a news article URL.')
    parsed = urlparse(raw)
    if parsed.scheme not in {'http', 'https'}:
        raise ArticleExtractionError(
            'URL must start with http:// or https://.'
        )
    if not parsed.netloc:
        raise ArticleExtractionError('URL is missing a domain name.')
    return raw


def fetch_url_html(url: str, *, timeout: float = 15.0) -> str:
    """Download HTML for ``url``. Raises ArticleExtractionError on failure."""
    validated = validate_news_url(url)
    request = Request(
        validated,
        headers={
            'User-Agent': (
                'PeyvandEditorialStudio/1.0 (+https://peyvand.se; news-import)'
            ),
            'Accept': 'text/html,application/xhtml+xml',
        },
        method='GET',
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or 'utf-8'
            raw = response.read()
    except HTTPError as exc:
        raise ArticleExtractionError(
            f'Could not fetch the article (HTTP {exc.code}).'
        ) from exc
    except URLError as exc:
        raise ArticleExtractionError(
            'Could not reach the article URL. Check the link and try again.'
        ) from exc
    except TimeoutError as exc:
        raise ArticleExtractionError(
            'Timed out while fetching the article URL.'
        ) from exc
    try:
        return raw.decode(charset, errors='replace')
    except LookupError:
        return raw.decode('utf-8', errors='replace')


def extract_readable_content(html: str, *, url: str = '') -> ExtractedArticle:
    """Extract title + readable body text from HTML."""
    parser = _ReadableHTMLParser()
    try:
        parser.feed(html or '')
        parser.close()
    except Exception as exc:  # noqa: BLE001
        raise ArticleExtractionError(
            'Could not parse the article HTML.'
        ) from exc

    title = _normalise_whitespace(' '.join(parser.h1_parts)) or (
        _normalise_whitespace(' '.join(parser.title_parts))
    )
    body = _normalise_whitespace(''.join(parser.article_parts))
    if len(body) < 120:
        body = _normalise_whitespace(''.join(parser.body_parts))
    if not body or len(body) < 40:
        raise ArticleExtractionError(
            'Could not extract readable article content from this page.'
        )
    if not title:
        title = 'Untitled article'
    domain = urlparse(url).netloc if url else ''
    return ExtractedArticle(
        url=url or '',
        title=title,
        text=body,
        domain=domain,
        detected_language=_detect_language_hint(f'{title}\n{body}'),
    )


def extract_article_from_url(
    url: str,
    *,
    timeout: float = 15.0,
) -> ExtractedArticle:
    """Fetch ``url`` and return readable article content."""
    validated = validate_news_url(url)
    html = fetch_url_html(validated, timeout=timeout)
    return extract_readable_content(html, url=validated)
