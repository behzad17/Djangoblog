"""Fetch a URL and extract readable article content + metadata.

Uses the standard library only (urllib + html.parser + json). Concrete
extractor for Editorial Studio (ES-001A) and Editorial Workspace ingest.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

EXTRACTION_FAILED_MESSAGE = (
    'Unable to extract article content from this URL.\n'
    'Paste the article text manually.'
)


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
    publisher: str = ''
    publication_date: date | None = None
    detected_country: str = ''
    metadata: dict | None = None


class _ReadableHTMLParser(HTMLParser):
    """Collect title, body, and common news metadata from HTML.

    Prefers ``<article>``, then ``<main>``, then body paragraphs.
    Captures Open Graph / article meta tags. ``header`` is not skipped so
    article ``h1`` headlines remain available.
    """

    _SKIP_TAGS = frozenset(
        {
            'script',
            'style',
            'noscript',
            'svg',
            'iframe',
            'nav',
            'footer',
            'aside',
            'form',
            'button',
        }
    )
    _META_TITLE_KEYS = frozenset({'og:title', 'twitter:title'})
    _META_SITE_KEYS = frozenset({'og:site_name', 'application-name', 'publisher'})
    _META_DATE_KEYS = frozenset(
        {
            'article:published_time',
            'og:published_time',
            'pubdate',
            'publish-date',
            'publication_date',
            'date',
            'dc.date',
            'dc.date.issued',
            'sailthru.date',
        }
    )

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.h1_candidates: list[str] = []
        self.og_title: str = ''
        self.site_name: str = ''
        self.published_raw: str = ''
        self.article_parts: list[str] = []
        self.main_parts: list[str] = []
        self.body_parts: list[str] = []
        self.json_ld_blocks: list[str] = []
        self._skip_depth = 0
        self._in_title = False
        self._in_h1 = False
        self._current_h1: list[str] = []
        self._in_article = False
        self._in_main = False
        self._in_p = False
        self._capture_p = False
        self._in_ld_json = False
        self._ld_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = {(k or '').lower(): (v or '') for k, v in attrs}
        if tag == 'meta':
            key = (attrs_dict.get('property') or attrs_dict.get('name') or '').lower()
            content = _normalise_whitespace(attrs_dict.get('content', ''))
            if not content:
                return
            if key in self._META_TITLE_KEYS and not self.og_title:
                self.og_title = content
            elif key in self._META_SITE_KEYS and not self.site_name:
                self.site_name = content
            elif key in self._META_DATE_KEYS and not self.published_raw:
                self.published_raw = content
            return
        if tag == 'script':
            script_type = (attrs_dict.get('type') or '').lower()
            if 'ld+json' in script_type:
                self._in_ld_json = True
                self._ld_parts = []
                return
            self._skip_depth += 1
            return
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == 'title':
            self._in_title = True
        elif tag == 'h1':
            self._in_h1 = True
            self._current_h1 = []
        elif tag == 'article':
            self._in_article = True
        elif tag == 'main':
            self._in_main = True
        elif tag in {'p', 'li', 'h2', 'h3'}:
            self._in_p = True
            self._capture_p = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'script' and self._in_ld_json:
            block = ''.join(self._ld_parts).strip()
            if block:
                self.json_ld_blocks.append(block)
            self._in_ld_json = False
            self._ld_parts = []
            return
        if tag in self._SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == 'title':
            self._in_title = False
        elif tag == 'h1':
            candidate = _normalise_whitespace(' '.join(self._current_h1))
            if candidate:
                self.h1_candidates.append(candidate)
            self._in_h1 = False
            self._current_h1 = []
        elif tag == 'article':
            self._in_article = False
        elif tag == 'main':
            self._in_main = False
        elif tag in {'p', 'li', 'h2', 'h3'}:
            if self._capture_p:
                bucket = self._active_bucket()
                if bucket and not bucket[-1].endswith('\n'):
                    bucket.append('\n')
            self._in_p = False
            self._capture_p = False

    def handle_data(self, data):
        if self._in_ld_json:
            self._ld_parts.append(data or '')
            return
        if self._skip_depth:
            return
        text = (data or '').strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        if self._in_h1:
            self._current_h1.append(text)
        if self._capture_p or self._in_p:
            bucket = self._active_bucket()
            bucket.append(text)
            bucket.append(' ')

    def _active_bucket(self) -> list[str]:
        if self._in_article:
            return self.article_parts
        if self._in_main:
            return self.main_parts
        return self.body_parts


def _normalise_whitespace(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text or '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _clean_document_title(title: str) -> str:
    """Strip common site-name suffixes from ``<title>`` text."""
    cleaned = _normalise_whitespace(title)
    if not cleaned:
        return ''
    for sep in (' | ', ' — ', ' – ', ' - ', ' :: ', ' • '):
        if sep in cleaned:
            parts = [p.strip() for p in cleaned.split(sep) if p.strip()]
            if parts:
                ranked = sorted(parts, key=len, reverse=True)
                for part in ranked:
                    if len(part) >= 12:
                        return part
                return parts[0]
    return cleaned


def _title_from_body(body: str) -> str:
    sample = _normalise_whitespace(body)
    if not sample:
        return ''
    sentence = re.split(r'(?<=[.!?])\s+', sample, maxsplit=1)[0].strip()
    if len(sentence) > 120:
        sentence = sentence[:117].rstrip() + '…'
    return sentence


def _detect_language_hint(text: str) -> str:
    sample = text or ''
    if any('\u0600' <= c <= '\u06FF' for c in sample):
        return 'fa'
    lowered = sample.lower()
    swedish_markers = (' och ', ' det ', ' att ', ' för ', ' är ', ' på ')
    if any(marker in f' {lowered} ' for marker in swedish_markers):
        return 'sv'
    return ''


def _country_from_domain(domain: str) -> str:
    host = (domain or '').lower()
    if host.endswith('.se') or '.se.' in host:
        return 'SE'
    if host.endswith('.ir') or '.ir.' in host:
        return 'IR'
    if host.endswith('.uk') or host.endswith('.co.uk'):
        return 'GB'
    if host.endswith('.de'):
        return 'DE'
    if host.endswith('.no'):
        return 'NO'
    if host.endswith('.dk'):
        return 'DK'
    if host.endswith('.fi'):
        return 'FI'
    return ''


def _publisher_from_domain(domain: str) -> str:
    host = (domain or '').strip().lower()
    if host.startswith('www.'):
        host = host[4:]
    if not host:
        return ''
    first = host.split('.')[0]
    if first.isdigit() or host in {'localhost'} or ':' in first:
        return host
    return first.upper() if len(first) <= 5 else first.capitalize()


def _parse_date(value: str) -> date | None:
    raw = (value or '').strip()
    if not raw:
        return None
    # ISO-8601 and common truncations.
    candidates = (
        raw,
        raw.replace('Z', '+00:00'),
        raw[:10],
        raw[:19],
    )
    for item in candidates:
        try:
            if 'T' in item or '+' in item or item.count('-') >= 2 and len(item) > 10:
                return datetime.fromisoformat(item).date()
        except ValueError:
            pass
        try:
            return datetime.strptime(item[:10], '%Y-%m-%d').date()
        except ValueError:
            continue
    return None


def _walk_json_ld(node, sink: dict) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_json_ld(item, sink)
        return
    if not isinstance(node, dict):
        return
    if '@graph' in node:
        _walk_json_ld(node.get('@graph'), sink)
    types = node.get('@type') or node.get('type') or ''
    if isinstance(types, list):
        type_blob = ' '.join(str(t) for t in types).lower()
    else:
        type_blob = str(types).lower()
    interesting = any(
        key in type_blob
        for key in (
            'newsarticle',
            'article',
            'reportage',
            'blogposting',
            'webpage',
        )
    )
    if interesting or not sink.get('title'):
        headline = node.get('headline') or node.get('name')
        if headline and not sink.get('title'):
            sink['title'] = _normalise_whitespace(str(headline))
        if node.get('datePublished') and not sink.get('date'):
            sink['date'] = str(node.get('datePublished'))
        publisher = node.get('publisher')
        if isinstance(publisher, dict) and not sink.get('publisher'):
            name = publisher.get('name')
            if name:
                sink['publisher'] = _normalise_whitespace(str(name))
        elif isinstance(publisher, str) and not sink.get('publisher'):
            sink['publisher'] = _normalise_whitespace(publisher)
        author = node.get('author')
        if isinstance(author, dict) and not sink.get('author'):
            name = author.get('name')
            if name:
                sink['author'] = _normalise_whitespace(str(name))
        article_body = node.get('articleBody')
        if article_body and not sink.get('body'):
            sink['body'] = _normalise_whitespace(str(article_body))


def _json_ld_metadata(blocks: list[str]) -> dict:
    sink: dict = {}
    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        _walk_json_ld(data, sink)
    return sink


def validate_news_url(url: str) -> str:
    """Validate and normalise an http(s) article URL."""
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
                'PeyvandEditorialWorkspace/1.0 '
                '(+https://peyvand.se; source-ingest)'
            ),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'sv,en,fa;q=0.8',
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
    """Extract title, body, and metadata from HTML."""
    parser = _ReadableHTMLParser()
    try:
        parser.feed(html or '')
        parser.close()
    except Exception as exc:  # noqa: BLE001
        raise ArticleExtractionError(
            'Could not parse the article HTML.'
        ) from exc

    ld = _json_ld_metadata(parser.json_ld_blocks)

    body = _normalise_whitespace(''.join(parser.article_parts))
    if len(body) < 120:
        body = _normalise_whitespace(''.join(parser.main_parts)) or body
    if len(body) < 120:
        body = _normalise_whitespace(''.join(parser.body_parts)) or body
    if len(body) < 120 and ld.get('body'):
        body = ld['body']
    if not body or len(body) < 40:
        raise ArticleExtractionError(EXTRACTION_FAILED_MESSAGE)

    document_title = _clean_document_title(' '.join(parser.title_parts))
    h1_title = parser.h1_candidates[0] if parser.h1_candidates else ''
    title = (
        _normalise_whitespace(parser.og_title)
        or _normalise_whitespace(ld.get('title') or '')
        or h1_title
        or document_title
        or _title_from_body(body)
        or 'Untitled article'
    )

    domain = urlparse(url).netloc if url else ''
    publisher = (
        _normalise_whitespace(parser.site_name)
        or _normalise_whitespace(ld.get('publisher') or '')
        or _publisher_from_domain(domain)
    )
    publication_date = _parse_date(parser.published_raw) or _parse_date(
        ld.get('date') or ''
    )
    detected_country = _country_from_domain(domain)
    meta = {
        'extractor': 'readable_html_v2',
        'had_article_tag': bool(parser.article_parts),
        'had_main_tag': bool(parser.main_parts),
        'had_json_ld': bool(parser.json_ld_blocks),
        'og_title': parser.og_title or '',
        'json_ld': {
            key: value
            for key, value in ld.items()
            if key != 'body'
        },
    }
    return ExtractedArticle(
        url=url or '',
        title=title,
        text=body,
        domain=domain,
        detected_language=_detect_language_hint(f'{title}\n{body}'),
        publisher=publisher,
        publication_date=publication_date,
        detected_country=detected_country,
        metadata=meta,
    )


def extract_article_from_url(
    url: str,
    *,
    timeout: float = 15.0,
) -> ExtractedArticle:
    """Fetch ``url`` and return readable article content."""
    validated = validate_news_url(url)
    try:
        html = fetch_url_html(validated, timeout=timeout)
        return extract_readable_content(html, url=validated)
    except ArticleExtractionError:
        # Normalise editor-facing failure for workspace ingest.
        raise
    except Exception as exc:  # noqa: BLE001
        raise ArticleExtractionError(EXTRACTION_FAILED_MESSAGE) from exc
