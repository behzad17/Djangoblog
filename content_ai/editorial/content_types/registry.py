"""CONTENT_TYPE_REGISTRY — per-type generation and assistant strategies."""

from __future__ import annotations

from dataclasses import dataclass, field

from content_ai.editorial.content_types.constants import (
    CONTENT_TYPE_LABELS,
    CONTENT_TYPES,
    ContentType,
    EditorialGoal,
    GOAL_LABELS,
    WRITING_STYLE_LABELS,
    WritingStyle,
)


@dataclass(frozen=True, slots=True)
class ContentTypeProfile:
    """Configuration for one editorial content type."""

    content_type: str
    label: str
    lead_label: str
    headline_strategy: str
    lead_strategy: str
    body_structure: str
    default_goal: str = EditorialGoal.INFORM.value
    default_style: str = WritingStyle.JOURNALISTIC.value
    assistant_action_ids: tuple[str, ...] = ()
    seo_strategy: str = 'default'
    evaluation_strategy: str = 'default'
    template_id: str = ''
    section_labels: dict[str, str] = field(default_factory=dict)

    def resolved_template_id(self) -> str:
        return self.template_id or f'{self.content_type}.v1'


def _profile(
    content_type: str,
    *,
    lead_label: str,
    headline_strategy: str,
    lead_strategy: str,
    body_structure: str,
    default_goal: str,
    assistant_action_ids: tuple[str, ...],
    default_style: str = WritingStyle.JOURNALISTIC.value,
    seo_strategy: str = 'default',
    evaluation_strategy: str = 'default',
    headline_label: str | None = None,
) -> ContentTypeProfile:
    return ContentTypeProfile(
        content_type=content_type,
        label=CONTENT_TYPE_LABELS.get(content_type, content_type.title()),
        lead_label=lead_label,
        headline_strategy=headline_strategy,
        lead_strategy=lead_strategy,
        body_structure=body_structure,
        default_goal=default_goal,
        default_style=default_style,
        assistant_action_ids=assistant_action_ids,
        seo_strategy=seo_strategy,
        evaluation_strategy=evaluation_strategy,
        template_id=f'{content_type}.v1',
        section_labels={
            'headline': headline_label
            or (
                'Title'
                if content_type
                in {
                    ContentType.GUIDE,
                    ContentType.HOW_TO,
                    ContentType.FAQ,
                }
                else 'Headline'
            ),
            'lead': lead_label,
            'body': 'Body',
            'summary': 'Summary',
        },
    )


_COMMON = (
    'improve_readability',
    'shorten',
    'expand',
    'simplify',
    'persian_terminology',
    'better_wording',
    'summarise',
    'prepare_seo',
)

CONTENT_TYPE_REGISTRY: dict[str, ContentTypeProfile] = {
    ContentType.NEWS: _profile(
        ContentType.NEWS,
        lead_label='Lead',
        headline_strategy='Short factual Persian news headline.',
        lead_strategy='One or two factual Persian news lead paragraphs.',
        body_structure=(
            'Inverted-pyramid news body with key facts first, then context, '
            'then secondary detail.'
        ),
        default_goal=EditorialGoal.INFORM.value,
        default_style=WritingStyle.JOURNALISTIC.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'make_neutral',
            'prepare_seo',
            *_COMMON,
        ),
        seo_strategy='news',
    ),
    ContentType.REPORT: _profile(
        ContentType.REPORT,
        lead_label='Executive summary',
        headline_strategy='Descriptive report title naming the subject and scope.',
        lead_strategy='Executive summary of findings for busy readers.',
        body_structure=(
            'Background, key findings, supporting detail, and conclusion.'
        ),
        default_goal=EditorialGoal.DOCUMENT.value,
        default_style=WritingStyle.ANALYTICAL.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'strengthen_findings',
            *_COMMON,
        ),
        evaluation_strategy='report',
    ),
    ContentType.REPORTAGE: _profile(
        ContentType.REPORTAGE,
        lead_label='Opening',
        headline_strategy='Narrative reportage title with place or theme.',
        lead_strategy='Scene-setting opening that draws the reader in.',
        body_structure=(
            'Observed scenes, voices, context, and closing observation.'
        ),
        default_goal=EditorialGoal.INFORM.value,
        default_style=WritingStyle.HUMAN_INTEREST.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_flow',
            *_COMMON,
        ),
    ),
    ContentType.GUIDE: _profile(
        ContentType.GUIDE,
        lead_label='Introduction',
        headline_strategy='Action-oriented guide title.',
        lead_strategy='Introduction explaining who the guide helps and why.',
        body_structure=(
            'Step-by-step instructions, important notes, useful links, '
            'then a short summary.'
        ),
        default_goal=EditorialGoal.TEACH.value,
        default_style=WritingStyle.EDUCATIONAL.value,
        assistant_action_ids=(
            'improve_instructions',
            'simplify_instructions',
            'add_warning',
            'improve_structure',
            'improve_headline',
            'rewrite_lead',
            'add_tips',
            *_COMMON,
        ),
        seo_strategy='guide',
    ),
    ContentType.HOW_TO: _profile(
        ContentType.HOW_TO,
        lead_label='Introduction',
        headline_strategy='How-to title focused on the outcome.',
        lead_strategy='Brief intro plus prerequisites overview.',
        body_structure=(
            'Required prerequisites, numbered steps, warnings, tips, summary.'
        ),
        default_goal=EditorialGoal.TEACH.value,
        default_style=WritingStyle.EDUCATIONAL.value,
        assistant_action_ids=(
            'improve_instructions',
            'simplify_instructions',
            'add_warning',
            'improve_structure',
            'improve_headline',
            'rewrite_lead',
            'add_tips',
            *_COMMON,
        ),
        seo_strategy='howto',
    ),
    ContentType.PRESS_RELEASE: _profile(
        ContentType.PRESS_RELEASE,
        lead_label='Opening',
        headline_strategy='Announcement-style title naming the organisation and news.',
        lead_strategy='Opening announcement paragraph with the core news.',
        body_structure=(
            'Announcement, details, quote if available, and background.'
        ),
        default_goal=EditorialGoal.ANNOUNCE.value,
        default_style=WritingStyle.OFFICIAL.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'formal_tone',
            *_COMMON,
        ),
    ),
    ContentType.ANALYSIS: _profile(
        ContentType.ANALYSIS,
        lead_label='Opening context',
        headline_strategy='Analytical title that frames the question or tension.',
        lead_strategy='Opening context that frames the issue.',
        body_structure=(
            'Context, analysis, implications, and conclusion.'
        ),
        default_goal=EditorialGoal.EXPLAIN.value,
        default_style=WritingStyle.ANALYTICAL.value,
        assistant_action_ids=(
            'strengthen_argument',
            'neutralise_tone',
            'improve_clarity',
            'improve_headline',
            'rewrite_lead',
            *_COMMON,
        ),
        evaluation_strategy='analysis',
    ),
    ContentType.OPINION: _profile(
        ContentType.OPINION,
        lead_label='Opening',
        headline_strategy='Opinion title stating a clear stance or question.',
        lead_strategy='Opening that states the viewpoint early.',
        body_structure='Argument, supporting points, counterpoint, closing stance.',
        default_goal=EditorialGoal.PERSUADE.value,
        default_style=WritingStyle.ANALYTICAL.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'strengthen_argument',
            'neutralise_tone',
            'improve_clarity',
            *_COMMON,
        ),
    ),
    ContentType.INTERVIEW: _profile(
        ContentType.INTERVIEW,
        lead_label='Introduction',
        headline_strategy='Speaker-oriented interview title.',
        lead_strategy='Introduction presenting the interviewee and topic.',
        body_structure='Questions and answers with a short closing summary.',
        default_goal=EditorialGoal.INFORM.value,
        default_style=WritingStyle.CONVERSATIONAL.value,
        assistant_action_ids=(
            'improve_introduction',
            'condense_answers',
            'improve_flow',
            'improve_headline',
            'rewrite_lead',
            *_COMMON,
        ),
    ),
    ContentType.FAQ: _profile(
        ContentType.FAQ,
        lead_label='Introduction',
        headline_strategy='FAQ title naming the topic clearly.',
        lead_strategy='Short introduction before the questions.',
        body_structure='Clear question-and-answer pairs, then a short summary.',
        default_goal=EditorialGoal.EXPLAIN.value,
        default_style=WritingStyle.EDUCATIONAL.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_structure',
            'simplify',
            *_COMMON,
        ),
    ),
    ContentType.ANNOUNCEMENT: _profile(
        ContentType.ANNOUNCEMENT,
        lead_label='Opening',
        headline_strategy='Direct announcement title.',
        lead_strategy='Opening that states what is changing and when.',
        body_structure='What is announced, who is affected, dates, next steps.',
        default_goal=EditorialGoal.ANNOUNCE.value,
        default_style=WritingStyle.OFFICIAL.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'formal_tone',
            'add_warning',
            *_COMMON,
        ),
    ),
    ContentType.EXPLAINER: _profile(
        ContentType.EXPLAINER,
        lead_label='What happened',
        headline_strategy='Explainer title focused on understanding the topic.',
        lead_strategy='What happened, in plain language.',
        body_structure=(
            'What happened, why it matters, frequently asked questions, summary.'
        ),
        default_goal=EditorialGoal.EXPLAIN.value,
        default_style=WritingStyle.EDUCATIONAL.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_clarity',
            'simplify',
            'generate_faq',
            *_COMMON,
        ),
        seo_strategy='explainer',
    ),
    ContentType.FEATURE: _profile(
        ContentType.FEATURE,
        lead_label='Introduction',
        headline_strategy='Feature title with human or thematic hook.',
        lead_strategy='Narrative introduction establishing theme and stakes.',
        body_structure='Feature narrative with scenes, voices, and closing reflection.',
        default_goal=EditorialGoal.INSPIRE.value,
        default_style=WritingStyle.HUMAN_INTEREST.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_flow',
            'friendly_tone',
            *_COMMON,
        ),
    ),
    ContentType.EDITORIAL: _profile(
        ContentType.EDITORIAL,
        lead_label='Opening',
        headline_strategy='Editorial title with a clear institutional stance.',
        lead_strategy='Opening that states the editorial position.',
        body_structure='Position, reasoning, community impact, call to attention.',
        default_goal=EditorialGoal.PERSUADE.value,
        default_style=WritingStyle.JOURNALISTIC.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'strengthen_argument',
            'formal_tone',
            *_COMMON,
        ),
    ),
    ContentType.EVENT: _profile(
        ContentType.EVENT,
        lead_label='Opening',
        headline_strategy='Event title naming what, when, and where.',
        lead_strategy='Opening with date, place, and why the event matters.',
        body_structure=(
            'What the event is, schedule, who it is for, how to take part, '
            'and practical details.'
        ),
        default_goal=EditorialGoal.ANNOUNCE.value,
        default_style=WritingStyle.JOURNALISTIC.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_clarity',
            *_COMMON,
        ),
        seo_strategy='event',
    ),
    ContentType.REVIEW: _profile(
        ContentType.REVIEW,
        lead_label='Introduction',
        headline_strategy='Review title naming the work and a clear angle.',
        lead_strategy='Introduction stating what is reviewed and the overall take.',
        body_structure=(
            'Context, strengths, weaknesses, and a fair concluding assessment.'
        ),
        default_goal=EditorialGoal.COMPARE.value,
        default_style=WritingStyle.CONVERSATIONAL.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'strengthen_argument',
            'improve_clarity',
            *_COMMON,
        ),
    ),
    ContentType.COMMUNITY_STORY: _profile(
        ContentType.COMMUNITY_STORY,
        lead_label='Introduction',
        headline_strategy='Community story title centred on people or place.',
        lead_strategy='Introduction that introduces the people and community stakes.',
        body_structure=(
            'Lived experience, community context, voices, and a respectful close.'
        ),
        default_goal=EditorialGoal.INSPIRE.value,
        default_style=WritingStyle.HUMAN_INTEREST.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_flow',
            'friendly_tone',
            *_COMMON,
        ),
    ),
    ContentType.OTHER: _profile(
        ContentType.OTHER,
        lead_label='Introduction',
        headline_strategy='Clear Persian title matching the source intent.',
        lead_strategy='Short introduction grounded in the source.',
        body_structure='Well-structured Persian article body with a short summary.',
        default_goal=EditorialGoal.INFORM.value,
        default_style=WritingStyle.NEUTRAL.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            *_COMMON,
        ),
    ),
}


def resolve_content_type(value: str | None) -> str:
    raw = (value or '').strip().lower().replace('-', '_').replace(' ', '_')
    aliases = {
        'howto': ContentType.HOW_TO.value,
        'how_to_guide': ContentType.HOW_TO.value,
        'press': ContentType.PRESS_RELEASE.value,
        'pressrelease': ContentType.PRESS_RELEASE.value,
        'gov': ContentType.ANNOUNCEMENT.value,
        'government': ContentType.ANNOUNCEMENT.value,
        'research': ContentType.ANALYSIS.value,
        'feature_article': ContentType.FEATURE.value,
        'community': ContentType.COMMUNITY_STORY.value,
        'community_story': ContentType.COMMUNITY_STORY.value,
        'event_listing': ContentType.EVENT.value,
        'auto': ContentType.NEWS.value,
    }
    resolved = aliases.get(raw, raw)
    if resolved in CONTENT_TYPE_REGISTRY:
        return resolved
    return ContentType.NEWS.value


def resolve_goal(value: str | None, *, content_type: str | None = None) -> str:
    raw = (value or '').strip().lower().replace('-', '_').replace(' ', '_')
    aliases = {
        'summarize': EditorialGoal.SUMMARISE.value,
        'summary': EditorialGoal.SUMMARISE.value,
        'document': EditorialGoal.DOCUMENT.value,
        'record': EditorialGoal.DOCUMENT.value,
    }
    resolved = aliases.get(raw, raw)
    if resolved in GOAL_LABELS:
        return resolved
    profile = get_profile(content_type)
    return profile.default_goal


def resolve_style(
    value: str | None,
    *,
    content_type: str | None = None,
) -> str:
    raw = (value or '').strip().lower().replace('-', '_').replace(' ', '_')
    aliases = {
        'humaninterest': WritingStyle.HUMAN_INTEREST.value,
        'human_interest': WritingStyle.HUMAN_INTEREST.value,
        'journalism': WritingStyle.JOURNALISTIC.value,
        'edu': WritingStyle.EDUCATIONAL.value,
        'formal': WritingStyle.OFFICIAL.value,
        'casual': WritingStyle.CONVERSATIONAL.value,
    }
    resolved = aliases.get(raw, raw)
    if resolved in WRITING_STYLE_LABELS:
        return resolved
    profile = get_profile(content_type)
    return profile.default_style


def get_profile(content_type: str | None = None) -> ContentTypeProfile:
    key = resolve_content_type(content_type)
    return CONTENT_TYPE_REGISTRY[key]


def list_content_types_for_ui() -> list[dict[str, str]]:
    return [
        {'id': key, 'label': CONTENT_TYPE_LABELS.get(key, key)}
        for key in CONTENT_TYPES
    ]


def list_goals_for_ui() -> list[dict[str, str]]:
    return [
        {'id': key, 'label': GOAL_LABELS.get(key, key.title())}
        for key in GOAL_LABELS
    ]


def list_styles_for_ui() -> list[dict[str, str]]:
    return [
        {'id': key, 'label': WRITING_STYLE_LABELS.get(key, key.title())}
        for key in WRITING_STYLE_LABELS
    ]
