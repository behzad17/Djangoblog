"""Internal image planner v2 — primary visual subject before prompting.

Planner output is INTERNAL ONLY and must not be shown to editors.

Core question the planner must answer:
"If this article were printed on the front page of a newspaper,
what should the photograph show?"
— not "what is this article generally related to?"
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


from content_ai.editorial.image.style import (
    resolve_image_style,
)


@dataclass(frozen=True, slots=True)
class ImagePlan:
    """Structured visual plan (v2) derived from the article (internal)."""

    primary_subject: str
    primary_visual_subject: str
    location: str
    secondary_elements: tuple[str, ...] = ()
    visual_style: str = 'Editorial photography'
    mood: str = 'Professional, trustworthy, institutional, calm, clean'
    avoid: tuple[str, ...] = ()

    # Legacy aliases kept for older session metadata / tests.
    @property
    def main_subject(self) -> str:
        return self.primary_visual_subject

    @property
    def secondary_subject(self) -> str:
        return ', '.join(self.secondary_elements) if self.secondary_elements else ''

    @property
    def environment(self) -> str:
        return self.location

    @property
    def things_to_avoid(self) -> str:
        return ', '.join(self.avoid)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload['secondary_elements'] = list(self.secondary_elements)
        payload['avoid'] = list(self.avoid)
        # Compatibility keys used by older UI/tests.
        payload['main_subject'] = self.primary_visual_subject
        payload['secondary_subject'] = self.secondary_subject
        payload['environment'] = self.location
        payload['things_to_avoid'] = self.things_to_avoid
        return payload

    def to_prompt_block(self) -> str:
        secondary = (
            ', '.join(self.secondary_elements)
            if self.secondary_elements
            else 'none'
        )
        avoid = ', '.join(self.avoid) if self.avoid else 'none'
        lines = [
            f'Primary subject (what the article is about): {self.primary_subject}',
            (
                'Primary visual subject (front-page photograph): '
                f'{self.primary_visual_subject}'
            ),
            f'Location: {self.location}',
            f'Secondary elements (optional, max two): {secondary}',
            f'Visual style: {self.visual_style}',
            f'Mood: {self.mood}',
            f'Avoid: {avoid}',
            'Visual complexity: exactly one primary subject; max two supporting '
            'elements; no collage, no infographic, no text in the image.',
        ]
        return '\n'.join(lines)


# Baseline avoid list — always applied unless the article is specifically
# about those subjects.
_BASE_AVOID: tuple[str, ...] = (
    'generic smiling people',
    'shopping',
    'children',
    'elderly people',
    'medical scenes unrelated to the topic',
    'food',
    'family moments',
    'random city streets',
    'tourism',
    'lifestyle photography',
    'coffee shops',
    'grocery delivery',
    'crowded scenes',
    'large groups',
    'fantasy',
    'sci-fi',
    'surrealism',
    'readable text',
    'logos',
    'watermarks',
    'typography',
    'collage',
    'infographic',
)


@dataclass(frozen=True, slots=True)
class _TopicRule:
    """Keyword → institutional visual mapping."""

    id: str
    keywords: tuple[str, ...]
    primary_subject: str
    primary_visual_subject: str
    location: str
    secondary_elements: tuple[str, ...]
    visual_style_photo: str
    mood: str
    extra_avoid: tuple[str, ...] = ()


# Ordered by specificity — first match wins.
_TOPIC_RULES: tuple[_TopicRule, ...] = (
    _TopicRule(
        id='constitution_parliament',
        keywords=(
            'constitution', 'grundlag', 'قانون اساسی', 'قوانین اساسی',
            'riksdag', 'riksdagen', 'parliament', 'پارلمان', 'مجلس',
            'ریکسداگ', 'ریکسداگ‌اوردنینگ', 'ریکسداگاوردنینگ',
            'regeringsformen', 'successionsordningen',
            'tryckfrihetsförordningen', 'yttrandefrihetsgrundlagen',
        ),
        primary_subject='Swedish Constitution and Parliament',
        primary_visual_subject=(
            'The Swedish Parliament building (Riksdagen) exterior or '
            'parliament chamber interior'
        ),
        location='Riksdagen, Stockholm, Sweden',
        secondary_elements=('official legal documents', 'subtle Swedish flag'),
        visual_style_photo='Architectural / documentary editorial photography',
        mood='Institutional, trustworthy, serious, calm, clean',
        extra_avoid=(
            'elderly receiving groceries',
            'community volunteering',
            'home interiors',
            'shopping bags',
        ),
    ),
    _TopicRule(
        id='government_politics',
        keywords=(
            'government', 'regering', 'دولت', 'وزیر', 'minister',
            'politik', 'politics', 'سیاست', 'cabinet', 'rosenbad',
            'government offices', 'statsminister',
        ),
        primary_subject='Swedish government / politics',
        primary_visual_subject=(
            'Swedish Government Offices exterior or formal government building'
        ),
        location='Government Offices, Stockholm, Sweden',
        secondary_elements=('official documents', 'microphones at a press podium'),
        visual_style_photo='Editorial / architectural photography',
        mood='Institutional, professional, trustworthy, calm',
        extra_avoid=('lifestyle scenes', 'casual street portraits'),
    ),
    _TopicRule(
        id='law_courts',
        keywords=(
            'court', 'domstol', 'دادگاه', 'supreme court', 'högsta domstolen',
            'law books', 'legal', 'حقوقی', 'قاضی', 'judge', 'آیین‌نامه',
        ),
        primary_subject='Law and courts',
        primary_visual_subject='Courtroom or official legal documents and law books',
        location='Swedish court building or formal legal office',
        secondary_elements=('law books', 'official papers'),
        visual_style_photo='Documentary editorial photography',
        mood='Serious, institutional, trustworthy, clean',
    ),
    _TopicRule(
        id='tax',
        keywords=(
            'tax', 'skatt', 'مالیات', 'skatteverket', 'skatte',
        ),
        primary_subject='Tax / Skatteverket',
        primary_visual_subject=(
            'Official tax authority office exterior or desk with unmarked '
            'official documents and calculator'
        ),
        location='Swedish tax authority / government office',
        secondary_elements=('official documents', 'calculator'),
        visual_style_photo='Editorial photography',
        mood='Professional, trustworthy, clean, calm',
        extra_avoid=('coffee lifestyle', 'home kitchen', 'shopping'),
    ),
    _TopicRule(
        id='immigration',
        keywords=(
            'migration', 'مهاجرت', 'migrationsverket', 'asyl', 'uppehåll',
            'immigration', 'passport', 'گذرنامه', 'پناه', 'border',
        ),
        primary_subject='Immigration / migration',
        primary_visual_subject=(
            'Migration office waiting area or passport and official documents '
            'on a counter'
        ),
        location='Migrationsverket / Swedish migration office',
        secondary_elements=('passport', 'official documents'),
        visual_style_photo='Documentary editorial photography',
        mood='Respectful, institutional, calm, clean',
        extra_avoid=('tourist photos', 'family picnic', 'airport shopping'),
    ),
    _TopicRule(
        id='police',
        keywords=('police', 'polis', 'پلیس', 'brott', 'جرم'),
        primary_subject='Police',
        primary_visual_subject=(
            'Swedish police officers or a police vehicle outside a station'
        ),
        location='Swedish police station exterior or quiet street',
        secondary_elements=('police vehicle',),
        visual_style_photo='Documentary editorial photography',
        mood='Calm, professional, trustworthy',
        extra_avoid=('action chase', 'violence', 'weapons close-up'),
    ),
    _TopicRule(
        id='healthcare',
        keywords=(
            'health', 'vård', 'سلامت', 'sjuk', 'healthcare', 'clinic',
            'hospital', 'بیمارستان', 'پزشک', 'doctor', 'nurse',
        ),
        primary_subject='Healthcare',
        primary_visual_subject='Hospital corridor or doctor with medical equipment',
        location='Swedish hospital / clinic interior',
        secondary_elements=('medical equipment',),
        visual_style_photo='Documentary editorial photography',
        mood='Calm, professional, trustworthy, clean',
        # Healthcare IS the topic — do not avoid medical scenes.
        extra_avoid=('shopping', 'tourism'),
    ),
    _TopicRule(
        id='education',
        keywords=(
            'education', 'utbildning', 'آموزش', 'school', 'skolan',
            'university', 'دانشگاه', 'student', 'دانشجو', 'teacher', 'معلم',
        ),
        primary_subject='Education',
        primary_visual_subject='University campus or classroom with students and teacher',
        location='Swedish school or university',
        secondary_elements=('books', 'desks'),
        visual_style_photo='Documentary editorial photography',
        mood='Bright, professional, calm, clean',
    ),
    _TopicRule(
        id='economy',
        keywords=(
            'economy', 'ekonomi', 'اقتصاد', 'finance', 'currency', 'krona',
            'industry', 'شرکت', 'company', 'börs', 'bank', 'بانک',
        ),
        primary_subject='Economy / finance',
        primary_visual_subject=(
            'Modern business district, finance office, or industrial facility'
        ),
        location='Swedish business district or company office',
        secondary_elements=('office documents', 'city skyline through a window'),
        visual_style_photo='Editorial photography',
        mood='Modern, professional, trustworthy, clean',
        extra_avoid=('graphs with readable numbers', 'stock ticker text'),
    ),
    _TopicRule(
        id='housing',
        keywords=(
            'housing', 'bostad', 'مسکن', 'apartment', 'hyra', 'اجاره',
            'مستاجر', 'landlord',
        ),
        primary_subject='Housing',
        primary_visual_subject='Swedish residential building exterior or apartment entrance',
        location='Swedish residential neighbourhood',
        secondary_elements=('house keys',),
        visual_style_photo='Architectural / editorial photography',
        mood='Calm, clean, trustworthy',
        extra_avoid=('furniture showroom lifestyle', 'family dinner'),
    ),
    _TopicRule(
        id='technology',
        keywords=(
            'technology', 'teknik', 'فناوری', 'digital', 'ai', 'هوش مصنوعی',
            'software', 'server', 'data', 'developer',
        ),
        primary_subject='Technology / digital infrastructure',
        primary_visual_subject=(
            'Server room, data centre aisle, or clean modern tech workspace'
        ),
        location='Modern tech office or data centre',
        secondary_elements=('servers', 'laptop without readable screen text'),
        visual_style_photo='Editorial photography',
        mood='Modern, clean, professional',
        extra_avoid=('readable UI', 'screens with text'),
    ),
    _TopicRule(
        id='culture',
        keywords=(
            'culture', 'kultur', 'فرهنگ', 'museum', 'موزه', 'concert',
            'کنسرت', 'artist', 'هنرمند', 'performance', 'theatre', 'تئاتر',
        ),
        primary_subject='Culture / arts',
        primary_visual_subject='Museum gallery, concert hall, or performance stage',
        location='Swedish cultural venue',
        secondary_elements=('stage lighting',),
        visual_style_photo='Editorial photography',
        mood='Creative yet professional, calm, clean',
    ),
    _TopicRule(
        id='transport',
        keywords=(
            'transport', 'trafik', 'حمل', 'train', 'bus', 'bil', 'körkort',
            'قطار', 'اتوبوس',
        ),
        primary_subject='Transport',
        primary_visual_subject='Swedish train station, bus, or clear road scene',
        location='Swedish public transport setting',
        secondary_elements=('platform',),
        visual_style_photo='Documentary editorial photography',
        mood='Calm, clean, modern',
    ),
)


def _clip(text: str, limit: int) -> str:
    cleaned = ' '.join((text or '').split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + '…'


def _normalize_blob(*parts: str) -> str:
    return ' '.join(p for p in parts if p).lower()


def _match_topic(blob: str) -> _TopicRule | None:
    for rule in _TOPIC_RULES:
        if any(keyword.lower() in blob for keyword in rule.keywords):
            return rule
    return None


def _build_avoid(
    rule: _TopicRule | None,
    *,
    topic_allows_people: bool,
    topic_is_healthcare: bool,
) -> tuple[str, ...]:
    avoid: list[str] = list(_BASE_AVOID)
    if rule:
        avoid.extend(rule.extra_avoid)
    if topic_is_healthcare:
        avoid = [a for a in avoid if 'medical' not in a.lower()]
    if topic_allows_people:
        # Keep generic lifestyle people banned; institutional people OK.
        pass
    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for item in avoid:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return tuple(out)


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
    Derive an internal v2 visual plan from article understanding.

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

    # Prefer headline + lead for subject extraction; body is secondary signal.
    blob = _normalize_blob(
        headline,
        lead,
        body[:1200],
        category,
        ' '.join(tags),
        content_type,
        goal or '',
    )
    rule = _match_topic(blob)

    if rule is not None:
        primary_subject = rule.primary_subject
        primary_visual = rule.primary_visual_subject
        location = rule.location
        secondary = rule.secondary_elements[:2]
        mood = rule.mood
        photo_style = rule.visual_style_photo
        topic_is_healthcare = rule.id == 'healthcare'
        topic_allows_people = rule.id in {
            'police',
            'healthcare',
            'education',
            'immigration',
        }
    else:
        topic = _clip(headline or lead, 100) or 'the article topic'
        primary_subject = topic
        primary_visual = (
            f'One clear institutional or real-world subject that would appear '
            f'on a newspaper front page about: {topic}'
        )
        location = 'Sweden — authentic setting matching the article subject'
        secondary = ()
        mood = 'Professional, trustworthy, institutional, calm, clean'
        photo_style = 'Editorial photography'
        topic_is_healthcare = False
        topic_allows_people = content_type in {
            'interview',
            'community_story',
            'community',
        }

    if style == 'editorial_illustration':
        visual_style = (
            'Clean modern editorial magazine illustration — minimal, '
            'professional, not cartoon, not fantasy'
        )
    else:
        visual_style = photo_style

    # Content-type mood nudges without changing the primary visual subject.
    if content_type in {'analysis', 'opinion', 'editorial'}:
        mood = f'{mood}; thoughtful, minimal'
    elif content_type in {'guide', 'howto', 'explainer', 'faq'}:
        mood = f'{mood}; clear and educational'
    elif content_type == 'interview' and rule is None:
        primary_visual = 'Interview subject in a calm professional setting'
        secondary = ('microphone',)
        topic_allows_people = True

    avoid = _build_avoid(
        rule,
        topic_allows_people=topic_allows_people,
        topic_is_healthcare=topic_is_healthcare,
    )

    return ImagePlan(
        primary_subject=primary_subject,
        primary_visual_subject=primary_visual,
        location=location,
        secondary_elements=secondary,
        visual_style=visual_style,
        mood=mood,
        avoid=avoid,
    )
