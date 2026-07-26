"""Build featured-image prompts from Editorial Workspace article fields."""

from __future__ import annotations

from dataclasses import dataclass

from content_ai.editorial.image.style import (
    PEYVAND_STYLE_BLOCK,
    PEOPLE_RULES,
    SWEDEN_RULES,
    category_visual_hint,
    content_type_visual,
)


@dataclass(frozen=True, slots=True)
class FeaturedImageBrief:
    """Prompt + short editorial explanation for a featured image."""

    prompt: str
    explanation: str
    aspect_ratio: str = '16:9'


def _clip(text: str, limit: int) -> str:
    cleaned = ' '.join((text or '').split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + '…'


def build_featured_image_brief(
    *,
    headline: str = '',
    lead: str = '',
    body: str = '',
    content_type: str = 'news',
    goal: str = '',
    category: str = '',
    tags: list[str] | None = None,
    publisher: str = '',
) -> FeaturedImageBrief:
    """
    Build an English image-generation prompt from Persian article fields.

    Never uses a source URL alone — requires editorial article content.
    """
    headline = (headline or '').strip()
    lead = (lead or '').strip()
    body = (body or '').strip()
    if not (headline or lead or body):
        raise ValueError(
            'Cannot build an image prompt without headline, lead, or article body.'
        )

    tags = [str(t).strip() for t in (tags or []) if str(t).strip()]
    content_type = (content_type or 'news').strip() or 'news'
    goal = (goal or '').strip()
    category = (category or '').strip()
    publisher = (publisher or '').strip()

    type_visual = content_type_visual(content_type)
    cat_hint = category_visual_hint(
        category=category,
        tags=tags,
        text_blob=f'{headline}\n{lead}\n{body}',
    )

    subject_lines = [
        f'Article headline (Persian): {_clip(headline, 220)}' if headline else '',
        f'Lead (Persian): {_clip(lead, 400)}' if lead else '',
        f'Article excerpt (Persian): {_clip(body, 900)}' if body else '',
        f'Content type: {content_type}.',
        f'Editorial goal: {goal}.' if goal else '',
        f'Category: {category}.' if category else '',
        f'Tags: {", ".join(tags)}.' if tags else '',
        f'Publisher context: {publisher}.' if publisher else '',
        f'Visual approach for content type: {type_visual}',
        f'Category visual cue: {cat_hint}',
    ]
    subject_block = '\n'.join(line for line in subject_lines if line)

    prompt = (
        'Create a professional featured image for a Persian news / community '
        'website article.\n'
        'Communicate the article\'s main idea clearly and professionally. '
        'Do NOT create artistic, fantasy, or cinematic spectacle imagery.\n\n'
        f'{PEYVAND_STYLE_BLOCK}\n\n'
        f'{PEOPLE_RULES}\n\n'
        f'{SWEDEN_RULES}\n\n'
        'Article context (use for meaning only; do not render any of this as '
        'text in the image):\n'
        f'{subject_block}\n\n'
        'Final instruction: produce one clean 16:9 editorial image that a '
        'reader immediately understands from a thumbnail.'
    )

    explanation = (
        f'This image concept centres on one clear subject matching '
        f'{category or content_type or "the article topic"}, using Peyvand\'s '
        f'minimal editorial style so the story remains readable as a hero '
        f'image and as a thumbnail. '
        f'Content-type cue: {type_visual} '
        f'Category cue: {cat_hint}'
    )

    return FeaturedImageBrief(
        prompt=prompt.strip(),
        explanation=explanation.strip(),
        aspect_ratio='16:9',
    )
