"""Build featured-image prompts from the structured Image Plan (v2).

The OpenAI prompt is built from planner JSON fields — not from long
article dumps that drift into generic lifestyle scenes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from content_ai.editorial.image.planner import ImagePlan, plan_featured_image
from content_ai.editorial.image.style import (
    IMAGE_STYLE_LABELS,
    PEYVAND_STYLE_BLOCK,
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
    Plan first, then build an English image prompt from the structured plan.

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
    style = resolve_image_style(image_style)
    style_label = IMAGE_STYLE_LABELS.get(style, style)

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

    secondary = (
        ', '.join(plan.secondary_elements)
        if plan.secondary_elements
        else 'none'
    )
    avoid = ', '.join(plan.avoid) if plan.avoid else 'generic lifestyle scenes'

    # Prompt is driven by the structured plan (front-page photograph rule).
    prompt = (
        'Create one professional 16:9 featured image for a Persian news / '
        'community website.\n'
        'Answer this brief as a newspaper front-page photograph would: show '
        'the article\'s primary institutional or real-world subject — not a '
        'generic Swedish lifestyle scene.\n\n'
        f'{PEYVAND_STYLE_BLOCK}\n\n'
        'STRUCTURED IMAGE PLAN (follow exactly; do not render as text):\n'
        f'{plan.to_prompt_block()}\n\n'
        'Render instructions:\n'
        f'- Show primarily: {plan.primary_visual_subject}\n'
        f'- Location: {plan.location}\n'
        f'- Supporting elements only if needed (max two): {secondary}\n'
        f'- Style: {plan.visual_style}\n'
        f'- Mood: {plan.mood}\n'
        f'- Hard avoid: {avoid}\n'
        '- Exactly one primary subject. No collage. No infographic. '
        'No readable text, logos, or watermarks.\n\n'
        'Article topic anchor (meaning only; never render as text):\n'
        f'- Headline: {_clip(headline, 160)}\n'
        f'- Lead: {_clip(lead, 180)}\n'
        f'- Category: {category or content_type or "news"}\n'
        f'- Editor style: {style_label}\n\n'
        'Final instruction: produce one clean editorial image that a reader '
        'understands within two seconds from a thumbnail, matching the '
        'primary visual subject above.'
    )

    explanation = (
        f'{style_label} front-page concept: “{plan.primary_visual_subject}” '
        f'for “{plan.primary_subject}”'
        f'{f" at {plan.location}" if plan.location else ""}. '
        f'Peyvand minimal editorial identity — institutional relevance over lifestyle.'
    )

    return FeaturedImageBrief(
        prompt=prompt.strip(),
        explanation=explanation.strip(),
        aspect_ratio='16:9',
        image_style=style,
        plan=plan,
    )
