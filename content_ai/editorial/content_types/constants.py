"""Content type, editorial goal, and writing style identifiers."""

from __future__ import annotations

from enum import StrEnum


class ContentType(StrEnum):
    NEWS = 'news'
    REPORT = 'report'
    REPORTAGE = 'reportage'
    GUIDE = 'guide'
    HOW_TO = 'how_to'
    PRESS_RELEASE = 'press_release'
    ANALYSIS = 'analysis'
    OPINION = 'opinion'
    INTERVIEW = 'interview'
    FAQ = 'faq'
    ANNOUNCEMENT = 'announcement'
    EXPLAINER = 'explainer'
    FEATURE = 'feature'
    EDITORIAL = 'editorial'
    EVENT = 'event'
    REVIEW = 'review'
    COMMUNITY_STORY = 'community_story'
    OTHER = 'other'


class EditorialGoal(StrEnum):
    INFORM = 'inform'
    EXPLAIN = 'explain'
    TEACH = 'teach'
    WARN = 'warn'
    ANNOUNCE = 'announce'
    COMPARE = 'compare'
    SUMMARISE = 'summarise'
    PERSUADE = 'persuade'
    INSPIRE = 'inspire'
    DOCUMENT = 'document'


class WritingStyle(StrEnum):
    JOURNALISTIC = 'journalistic'
    EDUCATIONAL = 'educational'
    OFFICIAL = 'official'
    CONVERSATIONAL = 'conversational'
    NEUTRAL = 'neutral'
    ANALYTICAL = 'analytical'
    HUMAN_INTEREST = 'human_interest'


CONTENT_TYPES: tuple[str, ...] = tuple(item.value for item in ContentType)
EDITORIAL_GOALS: tuple[str, ...] = tuple(item.value for item in EditorialGoal)
WRITING_STYLES: tuple[str, ...] = tuple(item.value for item in WritingStyle)

# Shared prompt-engine version shown in explainability (RFC-001 PromptBuilder).
PROMPT_ENGINE_VERSION = 'v1'

CONTENT_TYPE_LABELS: dict[str, str] = {
    ContentType.NEWS: 'News',
    ContentType.REPORT: 'Report',
    ContentType.REPORTAGE: 'Reportage',
    ContentType.GUIDE: 'Guide',
    ContentType.HOW_TO: 'How-to',
    ContentType.PRESS_RELEASE: 'Press Release',
    ContentType.ANALYSIS: 'Analysis',
    ContentType.OPINION: 'Opinion',
    ContentType.INTERVIEW: 'Interview',
    ContentType.FAQ: 'FAQ',
    ContentType.ANNOUNCEMENT: 'Announcement',
    ContentType.EXPLAINER: 'Explainer',
    ContentType.FEATURE: 'Feature',
    ContentType.EDITORIAL: 'Editorial',
    ContentType.EVENT: 'Event',
    ContentType.REVIEW: 'Review',
    ContentType.COMMUNITY_STORY: 'Community Story',
    ContentType.OTHER: 'Other',
}

GOAL_LABELS: dict[str, str] = {
    EditorialGoal.INFORM: 'Inform',
    EditorialGoal.EXPLAIN: 'Explain',
    EditorialGoal.TEACH: 'Teach',
    EditorialGoal.WARN: 'Warn',
    EditorialGoal.ANNOUNCE: 'Announce',
    EditorialGoal.COMPARE: 'Compare',
    EditorialGoal.SUMMARISE: 'Summarise',
    EditorialGoal.PERSUADE: 'Persuade',
    EditorialGoal.INSPIRE: 'Inspire',
    EditorialGoal.DOCUMENT: 'Document',
}

WRITING_STYLE_LABELS: dict[str, str] = {
    WritingStyle.JOURNALISTIC: 'Journalistic',
    WritingStyle.EDUCATIONAL: 'Educational',
    WritingStyle.OFFICIAL: 'Official',
    WritingStyle.CONVERSATIONAL: 'Conversational',
    WritingStyle.NEUTRAL: 'Neutral',
    WritingStyle.ANALYTICAL: 'Analytical',
    WritingStyle.HUMAN_INTEREST: 'Human-interest',
}

WRITING_STYLE_GUIDANCE: dict[str, str] = {
    WritingStyle.JOURNALISTIC: (
        'Use clear journalistic Persian: factual, scannable, inverted-pyramid '
        'instincts, no fluff. Do not shorten the article for style alone — '
        'follow the selected Article Length for BODY depth.'
    ),
    WritingStyle.EDUCATIONAL: (
        'Use clear educational Persian: teach step by step, define terms briefly, '
        'help a first-time reader succeed.'
    ),
    WritingStyle.OFFICIAL: (
        'Use formal official Persian suitable for institutions: precise, respectful, '
        'unambiguous dates and obligations.'
    ),
    WritingStyle.CONVERSATIONAL: (
        'Use warm conversational Persian: approachable, still accurate, never slangy '
        'or unserious about important facts.'
    ),
    WritingStyle.NEUTRAL: (
        'Use balanced neutral Persian: calm tone, avoid loaded language, present '
        'facts without drama.'
    ),
    WritingStyle.ANALYTICAL: (
        'Use analytical Persian: reasoned structure, clear claims and implications, '
        'careful wording around uncertainty.'
    ),
    WritingStyle.HUMAN_INTEREST: (
        'Use human-interest Persian: centre people and lived experience while staying '
        'truthful to the source.'
    ),
}
