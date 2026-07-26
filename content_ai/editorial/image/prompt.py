"""Build featured-image prompts from article understanding + image plan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from content_ai.editorial.image.planner import ImagePlan, plan_featured_image
from content_ai.editorial.image.style import (
    IMAGE_STYLE_GUIDANCE,
    IMAGE_STYLE_LABELS,
    PEYVAND_STYLE_BLOCK,
    PEOPLE_RULES,
    SWEDEN_RULES,
    resolve_image_style,
)


@dataclass(frozen=True, slots=True)
class FeaturedImageBrief:
    """Prompt + short editorial explanation for a featured image."""

    prompt: str
    explanation: str
    aspect_ratio: str = '16:9'
    image_style: str = 'editorial_photo'
    plan: ImagePlan | None = None

    def plan_dict(self) -> dict[str, Any]:
        return self.plan.to_dict() if self.plan else {}


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
    image_style: str | None = None,
    plan: ImagePlan | None = None,
) -> FeaturedImageBrief:
    """
    Build an English image-generation prompt from Persian article fields.

    Always plans the image first (unless an ImagePlan is supplied).
    Never uses a source URL alone — requires editorial article content.
    Never uses title alone.
    """
    headline = (headline or '').strip()
    lead = (lead or '').strip()
    body = (body or '').strip()
    if not headline and not lead and not body:
        raise ValueError(
            'Cannot build an image prompt without headline, lead, or article body.'
        )
    if not lead and not body:
        raise ValueError(
            'Cannot build an image prompt from title alone — need lead or body.'
        )

    tags = [str(t).strip() for t in (tags or []) if str(t).strip()]
    content_type = (content_type or 'news').strip() or 'news'
    goal = (goal or '').strip()
    category = (category or '').strip()
    publisher = (publisher or '').strip()
    style = resolve_image_style(image_style)
    style_label = IMAGE_STYLE_LABELS.get(style, style)
    style_guidance = IMAGE_STYLE_GUIDANCE.get(style, '')

    if plan is None:
        plan = plan_featured_image(
            headline=headline,
            lead=lead,
            body=body,
            content_type=content_type,
            goal=goal,
            category=category,
            tags=tags,
            image_style=style,
        )

    subject_lines = [
        f'Article headline (Persian): {_clip(headline, 180)}' if headline else '',
        f'Lead (Persian): {_clip(lead, 220)}' if lead else '',
        f'Article excerpt (Persian): {_clip(body, 320)}' if body else '',
        f'Content type: {content_type}.',
        f'Editorial goal: {goal}.' if goal else '',
        f'Category: {category}.' if category else '',
        f'Tags: {", ".join(tags[:8])}.' if tags else '',
        f'Selected image style: {style_label}.',
        style_guidance,
    ]
    subject_block = '\n'.join(line for line in subject_lines if line)

    # Keep the editable session prompt lean so OpenAI compaction rarely truncates.
    prompt = (
        'Create a professional featured image for a Persian news / community '
        'website article. One clear visual idea. No text, logos, or watermarks.\n\n'
        f'{PEYVAND_STYLE_BLOCK}\n\n'
        f'{PEOPLE_RULES}\n'
        f'{SWEDEN_RULES}\n\n'
        'Internal visual plan (follow closely; do not render as text):\n'
        f'{plan.to_prompt_block()}\n\n'
        'Article context (use for meaning only; do not render any of this as '
        'text in the image):\n'
        f'{subject_block}\n\n'
        'Final instruction: produce one clean 16:9 editorial image that a '
        'reader understands within two seconds from a thumbnail.'
    )

    explanation = (
        f'{style_label} concept focused on “{plan.main_subject}” in '
        f'{plan.environment}, matching '
        f'{category or content_type or "the article topic"}. '
        f'Peyvand minimal editorial identity — clear as a hero and thumbnail.'
    )

    return FeaturedImageBrief(
        prompt=prompt.strip(),
        explanation=explanation.strip(),
        aspect_ratio='16:9',
        image_style=style,
        plan=plan,
    )
