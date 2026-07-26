"""Peyvand visual style rules for editorial featured images."""

from __future__ import annotations

# Core brand visual language — clarity over artistry.
PEYVAND_STYLE_BLOCK = (
    'Peyvand visual style: professional, minimal, clean, clear, editorial, '
    'modern, natural, and easy to understand. Avoid visual complexity.\n'
    'Create ONE clear visual idea with one main subject.\n'
    'Avoid crowded scenes, unnecessary objects, excessive detail, dramatic '
    'action, fantasy, surrealism, exaggerated cinematic lighting, visual '
    'effects, heavy shadows, clutter, and unrealistic compositions.\n'
    'Avoid visual metaphors unless the article is analysis or opinion.\n'
    'The image must immediately communicate the topic and remain '
    'understandable as a small thumbnail.\n'
    'Composition: simple, balanced, large clear subject, clean background, '
    'natural colours, soft lighting.\n'
    'Medium: editorial photography or high-quality editorial illustration.\n'
    'Aesthetic: modern Scandinavian, professional news-magazine quality.\n'
    'Quality: high realism, natural perspective, clarity over artistic style.\n'
    'Aspect ratio: 16:9 hero image suitable for a news website.\n'
    'TEXT RULE: the image must contain NO readable text, titles, captions, '
    'labels, logos, watermarks, typography, UI elements, or screenshots.'
)

PEOPLE_RULES = (
    'People: only include people if the article naturally requires them. '
    'Avoid large crowds. Prefer authentic everyday situations, natural facial '
    'expressions and clothing. Avoid exaggerated emotions.'
)

SWEDEN_RULES = (
    'Sweden context when appropriate: use authentic Swedish environments; '
    'architecture, road signs, police uniforms, government offices and public '
    'transport should resemble Sweden. Do not exaggerate national symbols; '
    'avoid unnecessary Swedish flags.'
)

# Content-type visual adaptation (keys match editorial content types loosely).
CONTENT_TYPE_VISUALS: dict[str, str] = {
    'news': 'Realistic editorial photography suitable for a news homepage.',
    'guide': 'Bright, friendly, instructional imagery that feels helpful.',
    'howto': 'Bright, friendly, instructional imagery that feels helpful.',
    'analysis': (
        'Cleaner symbolic composition while remaining minimal and concrete '
        '(light metaphor only if needed).'
    ),
    'opinion': (
        'Cleaner symbolic composition while remaining minimal and concrete '
        '(light metaphor only if needed).'
    ),
    'editorial': (
        'Cleaner symbolic composition while remaining minimal and concrete.'
    ),
    'interview': 'Focus on the interview subject or a calm interview setting.',
    'report': 'Realistic documentary-style imagery.',
    'reportage': 'Realistic documentary-style imagery.',
    'feature': 'Realistic editorial photography with a clear human or place focus.',
    'community_story': 'Authentic human interaction in an everyday setting.',
    'community': 'Authentic human interaction in an everyday setting.',
    'press_release': 'Professional institutional or workplace setting.',
    'announcement': 'Clear institutional or community setting without clutter.',
    'event': 'Calm event environment — venue or gathering without chaos.',
    'review': 'Clear product/place subject in a clean editorial frame.',
    'explainer': 'Simple educational environment that clarifies the topic.',
    'faq': 'Simple educational environment that clarifies the topic.',
    'other': 'Clean professional editorial photography matching the topic.',
}

# Category keyword → visual cue (matched against category / tags / body).
CATEGORY_VISUAL_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ('tax', 'skatt', 'مالیات', 'skatteverket'),
        'Simple desk with tax documents, laptop and calculator — no readable text.',
    ),
    (
        ('police', 'polis', 'پلیس'),
        'Swedish-style police vehicle or officer on a calm street — no action scenes.',
    ),
    (
        ('housing', 'bostad', 'مسکن', 'apartment', 'hyra'),
        'Apartment exterior, residential building, or house keys — calm and real.',
    ),
    (
        ('education', 'utbildning', 'آموزش', 'school', 'skolan'),
        'Classroom, books, or teacher in a simple educational setting.',
    ),
    (
        ('business', 'företag', 'کسب', 'company', 'office'),
        'Professional office, meeting, or small-company workplace.',
    ),
    (
        ('health', 'vård', 'سلامت', 'sjuk', 'healthcare', 'clinic'),
        'Professional clinic, doctor, or hospital setting — calm and respectful.',
    ),
    (
        ('transport', 'trafik', 'حمل', 'train', 'bus', 'bil', 'körkort'),
        'Train, bus, road, or driving context — clear and uncluttered.',
    ),
    (
        ('migration', 'مهاجرت', 'migrationsverket', 'asyl', 'uppehåll'),
        'Government office, documents, or everyday life — respectful and calm.',
    ),
    (
        ('technology', 'teknik', 'فناوری', 'digital'),
        'Modern clean technology environment without UI screenshots or text.',
    ),
)


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
