"""Admin helpers for the AI Editorial Assistant (human-in-the-loop).

Generation previews are ephemeral. Nothing is saved until the editor chooses
Use Draft into the Admin form and then uses Save Draft.
"""

from __future__ import annotations

from django import forms

from blog.models import Category

SESSION_SUGGESTION_KEY = 'content_ai_blog_admin_suggestion'
MAX_TEMPORARY_VERSIONS = 3


class AdminGenerateWithAIForm(forms.Form):
    """Fields collected by the Admin AI assistant modal."""

    title = forms.CharField(
        max_length=200,
        required=False,
        help_text='Optional working title for the draft.',
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by('display_order', 'name'),
        required=True,
    )
    language = forms.CharField(
        max_length=32,
        required=False,
        initial='sv',
        help_text='Language hint for generation (not stored on Post).',
    )
    context = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Background or source notes for the model.',
    )
    instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Extra editorial instructions.',
    )


class TemporaryVersionHistory:
    """
    In-memory ring buffer of AI previews for one modal session.

    Keeps at most ``MAX_TEMPORARY_VERSIONS`` entries. Not persisted.
    """

    def __init__(self, max_versions: int = MAX_TEMPORARY_VERSIONS):
        if max_versions < 1:
            raise ValueError('max_versions must be >= 1')
        self.max_versions = max_versions
        self._versions: list[dict] = []
        self.active_index: int | None = None

    def __len__(self) -> int:
        return len(self._versions)

    @property
    def versions(self) -> list[dict]:
        return list(self._versions)

    @property
    def active(self) -> dict | None:
        if self.active_index is None:
            return None
        return self._versions[self.active_index]

    def add(self, version: dict) -> dict:
        """Append a preview; drop the oldest when over capacity."""
        payload = dict(version)
        self._versions.append(payload)
        if len(self._versions) > self.max_versions:
            self._versions = self._versions[-self.max_versions :]
        self.active_index = len(self._versions) - 1
        return payload

    def select(self, index: int) -> dict:
        if index < 0 or index >= len(self._versions):
            raise IndexError('version index out of range')
        self.active_index = index
        return self._versions[index]

    def clear(self) -> None:
        self._versions = []
        self.active_index = None


def suggestion_from_draft(draft, *, category_id) -> dict:
    """Serialize an EditorialDraft into an Admin form suggestion payload."""
    return {
        'title': draft.title or '',
        'content': draft.body or '',
        'excerpt': draft.summary or '',
        'category_id': category_id,
        'status': 0,
        'language': draft.language or '',
        'metadata': dict(draft.metadata or {}),
    }


def preview_from_draft(draft, *, category_id, request_values=None) -> dict:
    """Build a modal preview payload (includes telemetry when present)."""
    import uuid

    from content_ai.constants import AIGenerationTask
    from content_ai.prompts.loader import DEFAULT_PROMPT_VERSION
    from content_ai.serializers import serialize_editorial_draft

    serialized = serialize_editorial_draft(draft)
    if not serialized.get('title') and request_values:
        serialized['title'] = request_values.get('title') or ''
    metadata = serialized.get('metadata') or {}
    telemetry = serialized.get('telemetry') or {}
    provider = ''
    model_name = ''
    if isinstance(telemetry, dict):
        provider = telemetry.get('provider') or ''
        model_name = telemetry.get('model') or ''
    provider = provider or metadata.get('provider') or ''
    model_name = model_name or metadata.get('model') or ''
    return {
        'generation_id': str(uuid.uuid4()),
        'title': serialized.get('title') or '',
        'summary': serialized.get('summary') or '',
        'body': serialized.get('body') or '',
        'language': serialized.get('language') or '',
        'metadata': metadata,
        'telemetry': serialized.get('telemetry'),
        'category_id': category_id,
        'status': 0,
        'prompt_task': metadata.get('prompt_task')
        or AIGenerationTask.POST_GENERATION,
        'prompt_version': metadata.get('prompt_version')
        or DEFAULT_PROMPT_VERSION,
        'provider': provider,
        'model': model_name,
    }


def apply_suggestion_to_initial(initial: dict, suggestion: dict) -> dict:
    """Merge an AI suggestion into Admin form initial data (Draft only)."""
    data = dict(initial or {})
    if suggestion.get('title'):
        data['title'] = suggestion['title']
    if 'content' in suggestion:
        data['content'] = suggestion.get('content') or ''
    elif 'body' in suggestion:
        data['content'] = suggestion.get('body') or ''
    if 'excerpt' in suggestion:
        data['excerpt'] = suggestion.get('excerpt') or ''
    elif 'summary' in suggestion:
        data['excerpt'] = suggestion.get('summary') or ''
    if suggestion.get('category_id'):
        data['category'] = suggestion['category_id']
    data['status'] = 0
    return data


def categories_for_assistant():
    """Category choices for the Admin modal select."""
    return [
        {'id': category.pk, 'name': category.name}
        for category in Category.objects.all().order_by('display_order', 'name')
    ]
