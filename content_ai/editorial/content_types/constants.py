"""Content type and editorial goal identifiers."""

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


CONTENT_TYPES: tuple[str, ...] = tuple(item.value for item in ContentType)
EDITORIAL_GOALS: tuple[str, ...] = tuple(item.value for item in EditorialGoal)

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
    ContentType.FEATURE: 'Feature article',
    ContentType.EDITORIAL: 'Editorial',
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
}
