"""Configurable article length for editorial generation prompts."""

from __future__ import annotations

from enum import StrEnum

DEFAULT_ARTICLE_LENGTH = 'full'


class ArticleLength(StrEnum):
    FULL = 'full'
    STANDARD = 'standard'
    BRIEF = 'brief'
    NEWS_FLASH = 'news_flash'


ARTICLE_LENGTHS: tuple[str, ...] = tuple(item.value for item in ArticleLength)

ARTICLE_LENGTH_LABELS: dict[str, str] = {
    ArticleLength.FULL: 'Full Article',
    ArticleLength.STANDARD: 'Standard',
    ArticleLength.BRIEF: 'Brief',
    ArticleLength.NEWS_FLASH: 'News Flash',
}

# Prompt guidance injected into generation — length is controlled by prompt,
# never by truncating model output afterwards.
ARTICLE_LENGTH_GUIDANCE: dict[str, str] = {
    ArticleLength.FULL: (
        'Article length: Full Article (default).\n'
        'Write a complete Persian editorial article, not a summary.\n'
        'The finished article should read as if it were originally written '
        'by a professional Persian journalist.\n'
        'Structure the article naturally with:\n'
        '- A strong headline\n'
        '- An engaging lead\n'
        '- Multiple well-developed body sections\n'
        '- Logical transitions between sections\n'
        '- A clear ending when appropriate\n'
        'Preserve all important facts, explanations, timelines, numbers, '
        'quotations and context from the source.\n'
        'Preserve all important sections of the source.\n'
        'If the source contains multiple themes or sections, ensure each is '
        'represented in the Persian article.\n'
        'Expand explanations where necessary for Persian-speaking readers, '
        'but never invent facts or add unsupported information.\n'
        'Omit only repetition, boilerplate, advertisements, navigation '
        'elements and information irrelevant to readers.\n'
        'Do not omit facts simply to make the article shorter.\n'
        'Do NOT intentionally shorten or summarise the story.\n'
        'SUMMARY may be short; BODY must remain complete and well-developed.'
    ),
    ArticleLength.STANDARD: (
        'Article length: Standard.\n'
        'Write a medium-length Persian editorial article.\n'
        'Preserve key facts while reducing repetition and secondary detail.\n'
        'Aim for a balanced BODY — fuller than a brief, shorter than a full '
        'feature reconstruction.'
    ),
    ArticleLength.BRIEF: (
        'Article length: Brief.\n'
        'Write a concise Persian article focused on the most important '
        'information.\n'
        'Keep BODY compact while remaining clear and editorially polished.'
    ),
    ArticleLength.NEWS_FLASH: (
        'Article length: News Flash.\n'
        'Write a very concise Persian news flash suitable for breaking news.\n'
        'Keep BODY to a few short paragraphs with only the essential facts.'
    ),
}


def resolve_article_length(value: str | None) -> str:
    raw = (value or '').strip().lower().replace('-', '_').replace(' ', '_')
    aliases = {
        'full_article': ArticleLength.FULL.value,
        'complete': ArticleLength.FULL.value,
        'long': ArticleLength.FULL.value,
        'medium': ArticleLength.STANDARD.value,
        'short': ArticleLength.BRIEF.value,
        'summary': ArticleLength.BRIEF.value,
        'flash': ArticleLength.NEWS_FLASH.value,
        'newsflash': ArticleLength.NEWS_FLASH.value,
        'breaking': ArticleLength.NEWS_FLASH.value,
    }
    resolved = aliases.get(raw, raw)
    if resolved in ARTICLE_LENGTH_LABELS:
        return resolved
    return DEFAULT_ARTICLE_LENGTH


def article_length_prompt_block(value: str | None = None) -> str:
    length = resolve_article_length(value)
    return ARTICLE_LENGTH_GUIDANCE[length]


def list_article_lengths_for_ui() -> list[dict[str, str]]:
    return [
        {'id': key, 'label': ARTICLE_LENGTH_LABELS[key]}
        for key in ARTICLE_LENGTHS
    ]
