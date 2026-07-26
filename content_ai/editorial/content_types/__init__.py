"""Editorial content-type catalogue (Editorial AI v2).

Extensible registry of content types, editorial goals, and per-type
generation / assistant strategies. Defaults preserve news-shaped behaviour.
"""

from __future__ import annotations

from content_ai.editorial.content_types.classify import (
    ClassificationResult,
    classify_content,
)
from content_ai.editorial.content_types.constants import (
    CONTENT_TYPES,
    EDITORIAL_GOALS,
    ContentType,
    EditorialGoal,
)
from content_ai.editorial.content_types.goals import (
    GoalDetectionResult,
    detect_editorial_goal,
)
from content_ai.editorial.content_types.prompts import (
    body_pass_rules,
    headline_lead_pass_rules,
)
from content_ai.editorial.content_types.registry import (
    CONTENT_TYPE_REGISTRY,
    ContentTypeProfile,
    get_profile,
    list_content_types_for_ui,
    list_goals_for_ui,
    resolve_content_type,
    resolve_goal,
)

__all__ = [
    'CONTENT_TYPE_REGISTRY',
    'CONTENT_TYPES',
    'EDITORIAL_GOALS',
    'ClassificationResult',
    'ContentType',
    'ContentTypeProfile',
    'EditorialGoal',
    'GoalDetectionResult',
    'body_pass_rules',
    'classify_content',
    'detect_editorial_goal',
    'get_profile',
    'headline_lead_pass_rules',
    'list_content_types_for_ui',
    'list_goals_for_ui',
    'resolve_content_type',
    'resolve_goal',
]
