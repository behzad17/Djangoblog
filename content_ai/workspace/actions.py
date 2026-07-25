"""AI Assistant action catalogue for the Editorial Workspace (APF-001)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class WorkspaceAction:
    id: str
    label: str
    target_section: str  # headline|lead|body|summary|all|seo|social
    description: str = ''
    implemented: bool = True


# Contextual actions — each operates independently (stubs may no-op regenerate).
WORKSPACE_ACTIONS: tuple[WorkspaceAction, ...] = (
    WorkspaceAction('improve_headline', 'Improve headline', 'headline'),
    WorkspaceAction('rewrite_lead', 'Rewrite lead', 'lead'),
    WorkspaceAction('improve_readability', 'Improve readability', 'body'),
    WorkspaceAction('shorten', 'Shorten article', 'body'),
    WorkspaceAction('expand', 'Expand article', 'body'),
    WorkspaceAction('formal_tone', 'Formal tone', 'body'),
    WorkspaceAction('friendly_tone', 'Friendly tone', 'body'),
    WorkspaceAction('simplify', 'Simplify language', 'body'),
    WorkspaceAction('persian_terminology', 'Improve Persian terminology', 'body'),
    WorkspaceAction('better_wording', 'Suggest better wording', 'body'),
    WorkspaceAction('summarise', 'Summarise', 'summary'),
    WorkspaceAction('generate_faq', 'Generate FAQ', 'body', implemented=False),
    WorkspaceAction('related_topics', 'Suggest related topics', 'all', implemented=False),
    WorkspaceAction('social_caption', 'Social media caption', 'social', implemented=False),
    WorkspaceAction('newsletter_summary', 'Newsletter summary', 'summary', implemented=False),
    WorkspaceAction('prepare_seo', 'Prepare SEO', 'seo', implemented=False),
)


def list_actions_for_ui() -> list[dict]:
    return [asdict(action) for action in WORKSPACE_ACTIONS]


def get_action(action_id: str) -> WorkspaceAction | None:
    for action in WORKSPACE_ACTIONS:
        if action.id == action_id:
            return action
    return None
