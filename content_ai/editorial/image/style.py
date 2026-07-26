"""Peyvand visual style rules for editorial featured images."""

from __future__ import annotations

from enum import StrEnum

DEFAULT_IMAGE_STYLE = 'editorial_photo'


class ImageStyle(StrEnum):
    EDITORIAL_PHOTO = 'editorial_photo'
    EDITORIAL_ILLUSTRATION = 'editorial_illustration'


IMAGE_STYLES: tuple[str, ...] = tuple(item.value for item in ImageStyle)

IMAGE_STYLE_LABELS: dict[str, str] = {
    ImageStyle.EDITORIAL_PHOTO: 'Editorial Photo',
    ImageStyle.EDITORIAL_ILLUSTRATION: 'Editorial Illustration',
}

IMAGE_STYLE_GUIDANCE: dict[str, str] = {
    ImageStyle.EDITORIAL_PHOTO: (
        'Medium: highly realistic professional editorial photography, '
        'magazine quality, natural lighting, real environments.'
    ),
    ImageStyle.EDITORIAL_ILLUSTRATION: (
        'Medium: clean modern editorial magazine illustration — minimal, '
        'flat or softly rendered, professional. No cartoon style. No fantasy.'
    ),
}

# Core brand visual language — clarity over artistry.
PEYVAND_STYLE_BLOCK = (
    'Peyvand visual identity: minimal, modern, editorial, professional, '
    'Scandinavian, natural, clean, readable, timeless, simple.\n'
    'Always communicate ONE visual idea.\n'
    'Prefer: one clear subject, simple composition, large visual focus, '
    'clean background, natural colours, natural perspective, natural daylight, '
    'editorial quality. Avoid complexity.\n'
    'NEVER generate: crowded scenes, large groups, fantasy, sci-fi, surrealism, '
    'abstract symbolism, overly artistic compositions, heavy cinematic effects, '
    'extreme HDR, heavy contrast, lens flares, fire, explosions, action scenes, '
    'visual clutter, or unnecessary objects.\n'
    'The image must be understandable within 2 seconds even as a thumbnail.\n'
    'Composition: balanced 16:9 hero layout, clear hierarchy, simple visual '
    'storytelling, magazine quality.\n'
    'TEXT RULE: never include text, logos, watermarks, captions, screens, UI, '
    'signs with readable text, or typography.'
)

PEOPLE_RULES = (
    'People: only include people if needed. Prefer 1 person, or 2 people '
    'maximum. Natural expressions, natural clothing, authentic situations. '
    'Avoid exaggerated emotions and large crowds.'
)

SWEDEN_RULES = (
    'Sweden when appropriate: authentic Swedish environments, architecture, '
    'Scandinavian interiors, Swedish public transport, police, healthcare, '
    'schools and offices. Never overuse Swedish flags.'
)

# Content-type visual adaptation (keys match editorial content types loosely).
CONTENT_TYPE_VISUALS: dict[str, str] = {
    'news': 'Editorial photography suitable for a news homepage.',
    'guide': 'Bright, friendly, educational imagery.',
    'howto': 'Bright, friendly, educational imagery.',
    'analysis': 'Minimal symbolic composition — still concrete and simple.',
    'opinion': 'Minimal symbolic composition — still concrete and simple.',
    'editorial': 'Minimal symbolic composition — still concrete and simple.',
    'interview': 'Focus on the interviewee or a calm interview setting.',
    'report': 'Documentary-style realistic imagery.',
    'reportage': 'Documentary-style realistic imagery.',
    'feature': 'Editorial photography with a clear human or place focus.',
    'community_story': (
        'Friendly conversation / helping each other — authentic interaction.'
    ),
    'community': (
        'Friendly conversation / helping each other — authentic interaction.'
    ),
    'press_release': 'Professional institutional or workplace setting.',
    'announcement': 'Clear institutional or community setting without clutter.',
    'event': 'Calm event environment — venue without chaos.',
    'review': 'Clear product/place subject in a clean editorial frame.',
    'explainer': 'Simple educational environment that clarifies the topic.',
    'faq': 'Simple educational environment that clarifies the topic.',
    'other': 'Clean professional editorial imagery matching the topic.',
}

# Category keyword → visual cue (matched against category / tags / body).
CATEGORY_VISUAL_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ('tax', 'skatt', 'مالیات', 'skatteverket'),
        'Desk, tax papers, laptop, calculator, coffee — no readable text.',
    ),
    (
        ('police', 'polis', 'پلیس'),
        'Police officer, police vehicle, street or police station — no action.',
    ),
    (
        ('education', 'utbildning', 'آموزش', 'school', 'skolan'),
        'Teacher, student, books, classroom.',
    ),
    (
        ('health', 'vård', 'سلامت', 'sjuk', 'healthcare', 'clinic'),
        'Doctor, clinic, medical consultation — calm and respectful.',
    ),
    (
        ('business', 'företag', 'کسب', 'company', 'office', 'entrepreneur'),
        'Meeting, office, small company, entrepreneur.',
    ),
    (
        ('technology', 'teknik', 'فناوری', 'digital', 'developer'),
        'Laptop, developer, modern office, clean workspace — no UI text.',
    ),
    (
        ('housing', 'bostad', 'مسکن', 'apartment', 'hyra'),
        'Apartment, residential building, house keys, moving boxes.',
    ),
    (
        ('migration', 'مهاجرت', 'migrationsverket', 'asyl', 'uppehåll'),
        'Government office, waiting area, documents, family — respectful.',
    ),
    (
        ('community', 'انجمن', 'community', 'volunteer'),
        'Friendly conversation, helping each other, small group.',
    ),
    (
        ('transport', 'trafik', 'حمل', 'train', 'bus', 'bil', 'körkort'),
        'Train, bus, road, or driving context — clear and uncluttered.',
    ),
)


def resolve_image_style(value: str | None) -> str:
    raw = (value or '').strip().lower().replace('-', '_').replace(' ', '_')
    aliases = {
        'photo': ImageStyle.EDITORIAL_PHOTO.value,
        'photography': ImageStyle.EDITORIAL_PHOTO.value,
        'editorial_photography': ImageStyle.EDITORIAL_PHOTO.value,
        'realistic': ImageStyle.EDITORIAL_PHOTO.value,
        'illustration': ImageStyle.EDITORIAL_ILLUSTRATION.value,
        'illustrated': ImageStyle.EDITORIAL_ILLUSTRATION.value,
        'draw': ImageStyle.EDITORIAL_ILLUSTRATION.value,
    }
    resolved = aliases.get(raw, raw)
    if resolved in IMAGE_STYLE_LABELS:
        return resolved
    return DEFAULT_IMAGE_STYLE


def list_image_styles_for_ui() -> list[dict[str, str]]:
    return [
        {'id': key, 'label': IMAGE_STYLE_LABELS[key]}
        for key in IMAGE_STYLES
    ]


def content_type_visual(content_type: str | None) -> str:
    key = (content_type or 'news').strip().lower().replace('-', '_')
    return CONTENT_TYPE_VISUALS.get(key, CONTENT_TYPE_VISUALS['other'])


def category_visual_hint(
    *,
    category: str = '',
    tags: list[str] | None = None,
    text_blob: str = '',
) -> str:
    blob = ' '.join(
        part
        for part in (
            category or '',
            ' '.join(tags or []),
            text_blob or '',
        )
        if part
    ).lower()
    for keywords, hint in CATEGORY_VISUAL_HINTS:
        if any(keyword in blob for keyword in keywords):
            return hint
    return (
        'Choose one clear real-world subject that matches the article category '
        'and main topic.'
    )
