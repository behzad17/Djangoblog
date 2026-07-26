"""Editorial content-type catalogue (Editorial Intelligence v1).

Extensible registry of content types, editorial goals, writing styles, and
per-type generation / assistant strategies. Defaults preserve news-shaped
behaviour when signals are weak.
"""

from __future__ import annotations

from content_ai.editorial.content_types.classify import (
    ClassificationResult,
    classify_content,
)
from content_ai.editorial.content_types.constants import (
    CONTENT_TYPES,
    EDITORIAL_GOALS,
    PROMPT_ENGINE_VERSION,
    WRITING_STYLES,
    ContentType,
    EditorialGoal,
    WritingStyle,
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
    list_styles_for_ui,
    resolve_content_type,
    resolve_goal,
    resolve_style,
)
from content_ai.editorial.content_types.style import (
    StyleDetectionResult,
    detect_writing_style,
)

__all__ = [
    'CONTENT_TYPE_REGISTRY',
    'CONTENT_TYPES',
    'EDITORIAL_GOALS',
    'PROMPT_ENGINE_VERSION',
    'WRITING_STYLES',
    'ClassificationResult',
    'ContentType',
    'ContentTypeProfile',
    'EditorialGoal',
    'GoalDetectionResult',
    'StyleDetectionResult',
    'WritingStyle',
    'body_pass_rules',
    'classify_content',
    'detect_editorial_goal',
    'detect_writing_style',
    'get_profile',
    'headline_lead_pass_rules',
    'list_content_types_for_ui',
    'list_goals_for_ui',
    'list_styles_for_ui',
    'resolve_content_type',
    'resolve_goal',
    'resolve_style',
]
