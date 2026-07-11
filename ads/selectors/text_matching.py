"""Persian-aware text normalization and token matching for related content."""

import re
import unicodedata
from typing import Iterable

_PERSIAN_STOP_WORDS = frozenset(
    {
        'و',
        'در',
        'به',
        'از',
        'با',
        'برای',
        'که',
        'این',
        'آن',
        'ان',
        'را',
        'است',
        'یک',
        'یا',
        'تا',
        'بر',
        'هر',
        'هم',
        'من',
        'ما',
        'شما',
        'the',
        'and',
        'for',
        'with',
        'how',
        'what',
        'where',
        'when',
    }
)

_ARABIC_TO_PERSIAN = str.maketrans(
    {
        '\u064A': '\u06CC',  # ي -> ی
        '\u0643': '\u06A9',  # ك -> ک
        '\u0629': '\u0647',  # ة -> ه
        '\u0640': '',  # tatweel
    }
)

_TOKEN_SPLIT_RE = re.compile(r'[^\w\u0600-\u06FF]+')
_MIN_PREFIX_LENGTH = 3
_MIN_TOKEN_LENGTH = 2


def normalize_persian_text(text: str) -> str:
    """Normalize Persian/Arabic variants for consistent comparison."""
    if not text:
        return ''

    normalized = unicodedata.normalize('NFKC', text)
    normalized = normalized.translate(_ARABIC_TO_PERSIAN)
    normalized = normalized.replace('\u200C', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.casefold().strip()


def tokenize_persian_text(text: str) -> list[str]:
    """Return normalized, de-duplicated tokens from text."""
    tokens: list[str] = []
    seen: set[str] = set()
    for token in _iter_tokens(text):
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def extract_search_keywords(*texts: str) -> list[str]:
    """Extract keyword tokens from one or more text fields."""
    keywords: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for token in tokenize_persian_text(text):
            if token in seen:
                continue
            seen.add(token)
            keywords.append(token)
    return keywords


def keyword_search_variants(token: str) -> set[str]:
    """
    Expand a token into search variants for database pre-filtering.

    Includes the token, common suffix-stripped roots, and meaningful prefixes.
    """
    normalized = normalize_persian_text(token)
    if not normalized:
        return set()

    variants = {normalized}
    for suffix in ('های', 'ها', 'ات', 'ان', 'ی'):
        if normalized.endswith(suffix) and len(normalized) - len(suffix) >= _MIN_PREFIX_LENGTH:
            variants.add(normalized[: -len(suffix)])

    if len(normalized) >= _MIN_PREFIX_LENGTH + 1:
        variants.add(normalized[: _MIN_PREFIX_LENGTH + 1])

    return {variant for variant in variants if len(variant) >= _MIN_PREFIX_LENGTH}


def tokens_match(left: str, right: str) -> bool:
    """Return whether two normalized tokens refer to the same word stem."""
    left = normalize_persian_text(left)
    right = normalize_persian_text(right)
    if not left or not right:
        return False
    if left == right:
        return True

    shorter, longer = (left, right) if len(left) <= len(right) else (right, left)
    if len(shorter) >= _MIN_PREFIX_LENGTH and longer.startswith(shorter):
        return True

    common_prefix = 0
    for left_char, right_char in zip(left, right):
        if left_char != right_char:
            break
        common_prefix += 1

    min_length = min(len(left), len(right))
    return (
        common_prefix >= _MIN_PREFIX_LENGTH
        and common_prefix >= max(min_length - 2, _MIN_PREFIX_LENGTH)
    )


def score_token_overlap(query_tokens: Iterable[str], haystack_tokens: Iterable[str], *, weight: int) -> int:
    """Score weighted token overlap using Persian-aware stem matching."""
    haystack = list(haystack_tokens)
    score = 0
    for query_token in query_tokens:
        if any(tokens_match(query_token, candidate) for candidate in haystack):
            score += weight
    return score


def _iter_tokens(text: str) -> Iterable[str]:
    normalized = normalize_persian_text(text)
    for raw in _TOKEN_SPLIT_RE.split(normalized):
        token = raw.strip()
        if len(token) < _MIN_TOKEN_LENGTH or token in _PERSIAN_STOP_WORDS:
            continue
        yield token
