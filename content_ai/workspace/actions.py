"""AI Assistant action catalogue for the Editorial Workspace (APF-001)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from content_ai.editorial.content_types import get_profile, resolve_content_type


@dataclass(frozen=True, slots=True)
class WorkspaceAction:
    id: str
    label: str
    target_section: str  # headline|lead|body|summary|all|seo|social
    description: str = ''
    implemented: bool = True


# Full catalogue — filtered per content type via CONTENT_TYPE_REGISTRY.
WORKSPACE_ACTIONS: tuple[WorkspaceAction, ...] = (
    WorkspaceAction('improve_headline', 'Improve headline', 'headline'),
    WorkspaceAction('rewrite_lead', 'Rewrite lead', 'lead'),
    WorkspaceAction(
        'make_neutral',
        'Make neutral',
        'body',
        description='Reduce loaded language for news and similar pieces.',
    ),
    WorkspaceAction('improve_readability', 'Improve readability', 'body'),
    WorkspaceAction('shorten', 'Shorten article', 'body'),
    WorkspaceAction('expand', 'Expand article', 'body'),
    WorkspaceAction('formal_tone', 'Formal tone', 'body'),
    WorkspaceAction('friendly_tone', 'Friendly tone', 'body'),
    WorkspaceAction('simplify', 'Simplify language', 'body'),
    WorkspaceAction(
        'simplify_instructions',
        'Simplify instructions',
        'body',
        description='Make guide/how-to steps easier to follow.',
    ),
    WorkspaceAction('persian_terminology', 'Improve Persian terminology', 'body'),
    WorkspaceAction('better_wording', 'Suggest better wording', 'body'),
    WorkspaceAction('summarise', 'Summarise', 'summary'),
    WorkspaceAction(
        'improve_instructions',
        'Improve steps',
        'body',
        description='Clarify steps and prerequisites for guides/how-tos.',
    ),
    WorkspaceAction(
        'add_warning',
        'Add warnings',
        'body',
        description='Add clear warnings where readers could make mistakes.',
    ),
    WorkspaceAction(
        'add_tips',
        'Add tips',
        'body',
        description='Add practical tips for readers.',
    ),
    WorkspaceAction(
        'improve_structure',
        'Improve structure',
        'body',
        description='Improve section order and hierarchy.',
    ),
    WorkspaceAction(
        'improve_introduction',
        'Improve introduction',
        'lead',
        description='Improve interview/feature introduction.',
    ),
    WorkspaceAction(
        'improve_flow',
        'Improve flow',
        'body',
        description='Improve narrative flow between sections.',
    ),
    WorkspaceAction(
        'condense_answers',
        'Condense answers',
        'body',
        description='Tighten interview answers while keeping voice.',
    ),
    WorkspaceAction(
        'strengthen_argument',
        'Strengthen logic',
        'body',
        description='Strengthen analytical or opinion reasoning.',
    ),
    WorkspaceAction(
        'neutralise_tone',
        'Neutralise tone',
        'body',
        description='Reduce loaded language while keeping substance.',
    ),
    WorkspaceAction(
        'improve_clarity',
        'Improve clarity',
        'body',
        description='Make analysis/explainer language clearer.',
    ),
    WorkspaceAction(
        'strengthen_findings',
        'Strengthen findings',
        'body',
        description='Make report findings clearer and more scannable.',
    ),
    WorkspaceAction(
        'generate_faq',
        'Generate FAQ',
        'body',
        description='Add a short FAQ section grounded in the source.',
    ),
    WorkspaceAction(
        'related_topics',
        'Suggest related topics',
        'all',
        implemented=False,
    ),
    WorkspaceAction(
        'social_caption',
        'Social media caption',
        'social',
        implemented=False,
    ),
    WorkspaceAction(
        'newsletter_summary',
        'Newsletter summary',
        'summary',
        implemented=False,
    ),
    WorkspaceAction(
        'prepare_seo',
        'Improve SEO',
        'seo',
        implemented=False,
    ),
)

_ACTIONS_BY_ID = {action.id: action for action in WORKSPACE_ACTIONS}


def list_actions_for_ui(content_type: str | None = None) -> list[dict]:
    """Return assistant actions for UI, filtered by content type when given."""
    if not content_type:
        return [asdict(action) for action in WORKSPACE_ACTIONS]
    profile = get_profile(resolve_content_type(content_type))
    allowed = set(profile.assistant_action_ids)
    # Always keep unimplemented reserved actions visible but disabled when listed.
    selected = [
        action
        for action in WORKSPACE_ACTIONS
        if action.id in allowed or (
            not action.implemented and action.id in {
                'related_topics',
                'social_caption',
                'newsletter_summary',
                'prepare_seo',
            }
        )
    ]
    if not selected:
        selected = list(WORKSPACE_ACTIONS)
    # Rewrite lead label for non-news types.
    payload = []
    for action in selected:
        item = asdict(action)
        if action.id == 'rewrite_lead' and profile.lead_label != 'Lead':
            item['label'] = f'Rewrite {profile.lead_label.lower()}'
        if action.id == 'improve_headline' and profile.section_labels.get(
            'headline'
        ) == 'Title':
            item['label'] = 'Improve title'
        payload.append(item)
    return payload


def get_action(action_id: str) -> WorkspaceAction | None:
    return _ACTIONS_BY_ID.get(action_id)
