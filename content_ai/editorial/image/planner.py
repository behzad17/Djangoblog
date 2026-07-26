"""Internal image planner — understand the article before prompting.

Planner output is INTERNAL ONLY and must not be shown to editors.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from content_ai.editorial.image.style import (
    category_visual_hint,
    content_type_visual,
    resolve_image_style,
)


@dataclass(frozen=True, slots=True)
class ImagePlan:
    """Structured visual plan derived from the article (internal)."""

    main_subject: str
    secondary_subject: str
    environment: str
    visual_focus: str
    camera_angle: str
    composition: str
    mood: str
    lighting: str
    visual_complexity: str
    image_style: str
    things_to_avoid: str
    content_type_cue: str
    category_cue: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_prompt_block(self) -> str:
        lines = [
            f'Main visual subject: {self.main_subject}',
            (
                f'Secondary subject (optional): {self.secondary_subject}'
                if self.secondary_subject
                else 'Secondary subject: none'
            ),
            f'Environment: {self.environment}',
            f'Visual focus: {self.visual_focus}',
            f'Camera angle: {self.camera_angle}',
            f'Composition: {self.composition}',
            f'Mood: {self.mood}',
            f'Lighting: {self.lighting}',
            f'Visual complexity: {self.visual_complexity}',
            f'Image style: {self.image_style}',
            f'Things to avoid: {self.things_to_avoid}',
            f'Content-type cue: {self.content_type_cue}',
            f'Category cue: {self.category_cue}',
        ]
        return '\n'.join(lines)


_AVOID = (
    'crowded scenes, large groups, fantasy, sci-fi, surrealism, abstract '
    'symbolism, overly artistic compositions, heavy cinematic effects, '
    'extreme HDR, heavy contrast, lens flares, fire, explosions, action '
    'scenes, visual clutter, unnecessary objects, readable text, logos, '
    'watermarks, captions, screens, UI, typography'
)


def _clip(text: str, limit: int) -> str:
    cleaned = ' '.join((text or '').split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + '…'


def _people_needed(blob: str, content_type: str) -> bool:
    lowered = blob.lower()
    type_key = (content_type or '').lower()
    if type_key in {'interview', 'community_story', 'community', 'guide', 'howto'}:
        return True
    people_markers = (
        'interview', 'مصاحبه', 'teacher', 'student', 'doctor', 'nurse',
        'police', 'polis', 'پلیس', 'family', 'خانواده', 'migrant', 'مهاجر',
        'entrepreneur', 'meeting', 'community', 'انجمن', 'کمک',
    )
    return any(marker in lowered for marker in people_markers)


def plan_featured_image(
    *,
    headline: str = '',
    lead: str = '',
    body: str = '',
    content_type: str = 'news',
    goal: str = '',
    category: str = '',
    tags: list[str] | None = None,
    image_style: str | None = None,
) -> ImagePlan:
    """
    Derive an internal visual plan from article understanding.

    Requires article substance (not URL / title alone).
    """
    headline = (headline or '').strip()
    lead = (lead or '').strip()
    body = (body or '').strip()
    if not headline and not lead and not body:
        raise ValueError('Image planner requires article content.')
    if not lead and not body:
        raise ValueError(
            'Image planner needs lead or body — title alone is not enough.'
        )

    tags = [str(t).strip() for t in (tags or []) if str(t).strip()]
    content_type = (content_type or 'news').strip() or 'news'
    category = (category or '').strip()
    style = resolve_image_style(image_style)
    blob = f'{headline}\n{lead}\n{body}\n{category}\n{" ".join(tags)}'
    type_cue = content_type_visual(content_type)
    cat_cue = category_visual_hint(
        category=category,
        tags=tags,
        text_blob=blob,
    )

    topic = _clip(headline or lead, 120) or 'the article topic'
    needs_people = _people_needed(blob, content_type)

    if 'tax' in cat_cue.lower() or 'desk' in cat_cue.lower():
        main = 'A calm desk with tax papers, laptop, calculator and coffee'
        environment = 'Quiet Scandinavian home-office or desk'
        secondary = 'Soft window light in the background'
    elif 'police' in cat_cue.lower():
        main = 'A Swedish-style police officer or police vehicle on a calm street'
        environment = 'Quiet Swedish street or police-station exterior'
        secondary = ''
    elif 'classroom' in cat_cue.lower() or 'education' in cat_cue.lower():
        main = 'Teacher and student with books in a simple classroom'
        environment = 'Bright Swedish classroom'
        secondary = 'Books on a desk'
    elif 'clinic' in cat_cue.lower() or 'healthcare' in cat_cue.lower():
        main = 'Doctor in a calm medical consultation'
        environment = 'Clean Swedish clinic interior'
        secondary = ''
    elif 'office' in cat_cue.lower() or 'meeting' in cat_cue.lower():
        main = 'Small-company meeting or entrepreneur at a clean desk'
        environment = 'Modern Scandinavian office'
        secondary = ''
    elif 'technology' in cat_cue.lower() or 'laptop' in cat_cue.lower() and 'tax' not in cat_cue.lower():
        main = 'Developer or clean laptop workspace'
        environment = 'Modern office with natural light'
        secondary = ''
    elif 'apartment' in cat_cue.lower() or 'housing' in cat_cue.lower() or 'keys' in cat_cue.lower():
        main = 'Residential building, apartment entrance, or house keys'
        environment = 'Swedish residential exterior or hallway'
        secondary = 'Moving boxes optional, uncluttered'
    elif 'government' in cat_cue.lower() or 'migration' in cat_cue.lower():
        main = 'Calm government waiting area with documents'
        environment = 'Scandinavian public office interior'
        secondary = 'One or two people waiting respectfully' if needs_people else ''
    elif 'community' in cat_cue.lower() or 'conversation' in cat_cue.lower():
        main = 'Friendly conversation / people helping each other'
        environment = 'Everyday community setting in Sweden'
        secondary = 'Small group, maximum two people in focus'
    else:
        main = f'One clear real-world subject representing: {topic}'
        environment = 'Authentic Swedish / Scandinavian everyday setting when relevant'
        secondary = 'One supporting detail only if needed'

    if content_type in {'interview'}:
        main = 'Interview subject in a calm interview setting'
        camera = 'Eye-level medium shot'
        mood = 'Attentive, respectful, calm'
    elif content_type in {'guide', 'howto', 'explainer', 'faq'}:
        camera = 'Slightly elevated or eye-level, clear instructional framing'
        mood = 'Bright, friendly, educational'
    elif content_type in {'analysis', 'opinion', 'editorial'}:
        camera = 'Clean wide or medium shot with strong negative space'
        mood = 'Thoughtful, minimal, serious'
    elif content_type in {'report', 'reportage'}:
        camera = 'Documentary eye-level'
        mood = 'Observational, grounded'
    else:
        camera = 'Natural eye-level editorial framing'
        mood = 'Calm, professional, trustworthy'

    style_label = (
        'Highly realistic professional editorial photography, magazine quality'
        if style == 'editorial_photo'
        else (
            'Clean modern editorial magazine illustration, minimal, flat or '
            'softly rendered — not cartoon, not fantasy'
        )
    )

    return ImagePlan(
        main_subject=main,
        secondary_subject=secondary,
        environment=environment,
        visual_focus='Large clear primary subject; readable as a thumbnail',
        camera_angle=camera,
        composition=(
            'Simple balanced 16:9 layout, one visual idea, clean background, '
            'natural perspective'
        ),
        mood=mood,
        lighting='Natural daylight, soft and even — no dramatic cinematic lighting',
        visual_complexity='Low — prefer simplicity over detail',
        image_style=style_label,
        things_to_avoid=_AVOID,
        content_type_cue=type_cue,
        category_cue=cat_cue,
    )
