"""Build content-type-aware generation instructions."""

from __future__ import annotations

from content_ai.editorial.content_types.constants import (
    GOAL_LABELS,
    PROMPT_ENGINE_VERSION,
    WRITING_STYLE_GUIDANCE,
    WRITING_STYLE_LABELS,
)
from content_ai.editorial.content_types.registry import (
    get_profile,
    resolve_goal,
    resolve_style,
)


def _style_block(*, content_type: str, style: str | None) -> str:
    resolved = resolve_style(style, content_type=content_type)
    label = WRITING_STYLE_LABELS.get(resolved, resolved)
    guidance = WRITING_STYLE_GUIDANCE.get(resolved, '')
    return (
        f'Writing style: {label}.\n'
        f'Style guidance: {guidance}\n'
    )


def headline_lead_pass_rules(
    *,
    content_type: str = 'news',
    goal: str | None = None,
    style: str | None = None,
) -> str:
    profile = get_profile(content_type)
    resolved_goal = resolve_goal(goal, content_type=profile.content_type)
    goal_label = GOAL_LABELS.get(resolved_goal, resolved_goal)
    return (
        f'Content type: {profile.label} '
        f'(template {profile.resolved_template_id()}, '
        f'prompt engine {PROMPT_ENGINE_VERSION}).\n'
        f'Editorial goal: {goal_label}.\n'
        f'{_style_block(content_type=profile.content_type, style=style)}'
        'Generate ONLY the Persian headline/title and opening section first.\n'
        'Do NOT write the article body yet.\n'
        f'Headline strategy: {profile.headline_strategy}\n'
        f'{profile.lead_label} strategy: {profile.lead_strategy}\n'
        'TITLE must be a fresh Persian headline/title. Do not copy the '
        'source-language title into TITLE.\n'
        f'LEAD is the {profile.lead_label.lower()} in Persian, grounded in the '
        'source.\n'
        'Return exactly this labelled structure:\n'
        'TITLE:\n...\n'
        'LEAD:\n...\n'
    )


def body_pass_rules(
    *,
    content_type: str = 'news',
    goal: str | None = None,
    style: str | None = None,
) -> str:
    profile = get_profile(content_type)
    resolved_goal = resolve_goal(goal, content_type=profile.content_type)
    goal_label = GOAL_LABELS.get(resolved_goal, resolved_goal)
    return (
        f'Content type: {profile.label} '
        f'(template {profile.resolved_template_id()}, '
        f'prompt engine {PROMPT_ENGINE_VERSION}).\n'
        f'Editorial goal: {goal_label}.\n'
        f'{_style_block(content_type=profile.content_type, style=style)}'
        'TITLE and LEAD are already decided and locked below.\n'
        'Do NOT rewrite TITLE or LEAD.\n'
        f'Generate BODY using this structure: {profile.body_structure}\n'
        'Return exactly this labelled structure:\n'
        'BODY:\n...\n'
        'SUMMARY:\n...\n'
        'CATEGORY:\n...\n'
        'TAGS:\ncomma, separated, tags\n'
        'Base BODY only on the provided source. Do not invent facts, names, '
        'dates, or figures. Use clear community-facing Persian.\n'
    )
