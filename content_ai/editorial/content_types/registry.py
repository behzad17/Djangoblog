"""CONTENT_TYPE_REGISTRY — per-type generation and assistant strategies."""

from __future__ import annotations

from dataclasses import dataclass, field

from content_ai.editorial.content_types.constants import (
    CONTENT_TYPE_LABELS,
    CONTENT_TYPES,
    ContentType,
    EditorialGoal,
    GOAL_LABELS,
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
    seo_strategy: str = 'default',
    evaluation_strategy: str = 'default',
) -> ContentTypeProfile:
    return ContentTypeProfile(
        content_type=content_type,
        label=CONTENT_TYPE_LABELS.get(content_type, content_type.title()),
        lead_label=lead_label,
        headline_strategy=headline_strategy,
        lead_strategy=lead_strategy,
        body_structure=body_structure,
        default_goal=default_goal,
        assistant_action_ids=assistant_action_ids,
        seo_strategy=seo_strategy,
        evaluation_strategy=evaluation_strategy,
        template_id=f'{content_type}.v1',
        section_labels={
            'headline': 'Headline' if content_type != ContentType.GUIDE else 'Title',
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
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            *_COMMON,
        ),
        seo_strategy='news',
    ),
    ContentType.REPORT: _profile(
        ContentType.REPORT,
        lead_label='Executive summary',
        headline_strategy='Clear report title naming the subject and scope.',
        lead_strategy='Executive summary of findings for busy readers.',
        body_structure=(
            'Background, key findings, supporting detail, and conclusion.'
        ),
        default_goal=EditorialGoal.INFORM.value,
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
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_instructions',
            'add_warning',
            'add_tips',
            'improve_structure',
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
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_instructions',
            'add_warning',
            'add_tips',
            'improve_structure',
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
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'strengthen_argument',
            'neutralise_tone',
            'improve_clarity',
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
        headline_strategy='Speaker-focused interview headline.',
        lead_strategy='Introduction presenting the interviewee and topic.',
        body_structure='Questions and answers with a short closing summary.',
        default_goal=EditorialGoal.INFORM.value,
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'improve_introduction',
            'improve_flow',
            'condense_answers',
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
        assistant_action_ids=(
            'improve_headline',
            'rewrite_lead',
            'strengthen_argument',
            'formal_tone',
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
    }
    resolved = aliases.get(raw, raw)
    if resolved in GOAL_LABELS:
        return resolved
    profile = get_profile(content_type)
    return profile.default_goal


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
