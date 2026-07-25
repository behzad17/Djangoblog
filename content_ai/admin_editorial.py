"""Admin helpers for AI-assisted Blog draft generation (human-in-the-loop).

Suggestions are stored in the session and applied to the Admin change form.
Nothing is saved until the editor explicitly saves a Draft.
"""

from __future__ import annotations

from django import forms

from blog.models import Category

SESSION_SUGGESTION_KEY = 'content_ai_blog_admin_suggestion'


class AdminGenerateWithAIForm(forms.Form):
    """Intermediate Admin form for requesting an AI Blog draft suggestion."""

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


def suggestion_from_draft(draft, *, category_id) -> dict:
    """Serialize an EditorialDraft into a session-safe suggestion payload."""
    return {
        'title': draft.title or '',
        'content': draft.body or '',
        'excerpt': draft.summary or '',
        'category_id': category_id,
        'status': 0,
        'language': draft.language or '',
        'metadata': dict(draft.metadata or {}),
    }


def apply_suggestion_to_initial(initial: dict, suggestion: dict) -> dict:
    """Merge an AI suggestion into Admin form initial data (Draft only)."""
    data = dict(initial or {})
    if suggestion.get('title'):
        data['title'] = suggestion['title']
    if 'content' in suggestion:
        data['content'] = suggestion.get('content') or ''
    if 'excerpt' in suggestion:
        data['excerpt'] = suggestion.get('excerpt') or ''
    if suggestion.get('category_id'):
        data['category'] = suggestion['category_id']
    data['status'] = 0
    return data
