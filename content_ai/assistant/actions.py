"""Extensible action registry for the Admin AI Editorial Assistant.

v1 implements only ``generate`` and ``regenerate``. Future editing actions are
registered as disabled placeholders so the modal architecture stays stable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class AssistantAction:
    """One assistant capability shown in the Admin modal."""

    id: str
    label: str
    icon: str = ''
    enabled: bool = False
    primary: bool = False
    group: str = 'assistant'  # primary | assistant | result
    coming_soon: str = 'Coming soon'
    description: str = ''


# Registry order controls modal layout. Add new actions here without changing
# the modal shell — implement handlers later and flip ``enabled=True``.
ASSISTANT_ACTIONS: tuple[AssistantAction, ...] = (
    AssistantAction(
        id='generate',
        label='Generate',
        icon='✨',
        enabled=True,
        primary=True,
        group='primary',
        description='Create a new draft suggestion from the request fields.',
    ),
    AssistantAction(
        id='regenerate',
        label='Regenerate',
        icon='🔄',
        enabled=True,
        primary=False,
        group='assistant',
        description='Create another draft using the same request values.',
    ),
    AssistantAction(
        id='rewrite',
        label='Rewrite',
        icon='✍',
        enabled=False,
        group='assistant',
        description='Rewrite the active preview (future).',
    ),
    AssistantAction(
        id='shorter',
        label='Shorter',
        icon='✂',
        enabled=False,
        group='assistant',
        description='Shorten the active preview (future).',
    ),
    AssistantAction(
        id='longer',
        label='Longer',
        icon='📖',
        enabled=False,
        group='assistant',
        description='Expand the active preview (future).',
    ),
    AssistantAction(
        id='translate',
        label='Translate',
        icon='🌍',
        enabled=False,
        group='assistant',
        description='Translate the active preview (future).',
    ),
    AssistantAction(
        id='seo_optimize',
        label='SEO Optimize',
        icon='📰',
        enabled=False,
        group='assistant',
        description='SEO-oriented rewrite (future).',
    ),
    AssistantAction(
        id='social_post',
        label='Social Post',
        icon='📱',
        enabled=False,
        group='assistant',
        description='Generate a social post variant (future).',
    ),
)

_ACTIONS_BY_ID = {action.id: action for action in ASSISTANT_ACTIONS}

# v1 handlers that may call the generation pipeline.
IMPLEMENTED_ACTIONS = frozenset({'generate', 'regenerate'})


def get_assistant_actions() -> tuple[AssistantAction, ...]:
    return ASSISTANT_ACTIONS


def get_action(action_id: str) -> AssistantAction | None:
    return _ACTIONS_BY_ID.get(action_id)


def list_actions_for_ui() -> list[dict]:
    """JSON-serializable action descriptors for the Admin modal."""
    return [asdict(action) for action in ASSISTANT_ACTIONS]


def primary_actions() -> list[AssistantAction]:
    return [action for action in ASSISTANT_ACTIONS if action.group == 'primary']


def assistant_actions() -> list[AssistantAction]:
    return [action for action in ASSISTANT_ACTIONS if action.group == 'assistant']


def is_action_implemented(action_id: str) -> bool:
    action = get_action(action_id)
    return bool(action and action.enabled and action.id in IMPLEMENTED_ACTIONS)
