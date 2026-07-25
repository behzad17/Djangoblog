from django import forms

from content_ai.constants import AIGenerationTask
from content_ai.providers.registry import list_providers


class ContentAISandboxForm(forms.Form):
    """Developer-only form for manual Content AI generation."""

    task = forms.ChoiceField(
        choices=(
            (AIGenerationTask.POST_GENERATION, 'POST_GENERATION'),
            (AIGenerationTask.AD_GENERATION, 'AD_GENERATION'),
        ),
        initial=AIGenerationTask.POST_GENERATION,
    )
    provider = forms.ChoiceField(
        required=False,
        help_text='Leave blank to use CONTENT_AI_PROVIDER from settings.',
    )

    # PostGenerationRequest fields
    title = forms.CharField(required=False, initial='Sandbox post title')
    source = forms.CharField(required=False, initial='sandbox')
    language = forms.CharField(required=False, initial='sv')
    category = forms.CharField(required=False, initial='news')
    context = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        initial='Developer sandbox context',
    )
    instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        initial='Keep the response short.',
    )

    # AdGenerationRequest fields
    business_name = forms.CharField(required=False, initial='Sandbox Cafe')
    city = forms.CharField(required=False, initial='Stockholm')
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        initial='A small cafe for testing ads generation.',
    )
    target_audience = forms.CharField(required=False, initial='locals')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        provider_choices = [('', 'Default (settings)')]
        provider_choices.extend((name, name) for name in list_providers())
        self.fields['provider'].choices = provider_choices
