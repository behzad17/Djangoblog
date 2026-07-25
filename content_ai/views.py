"""Developer-only Content AI sandbox views."""

import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from content_ai.constants import AIGenerationTask
from content_ai.forms import ContentAISandboxForm
from content_ai.prompts.registry import get_prompt_template
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.schemas.requests import AdGenerationRequest, PostGenerationRequest
from content_ai.services.generation import ContentGenerationService


def user_can_access_sandbox(user):
    """Sandbox is for authenticated DEBUG sessions or superusers only."""
    if not getattr(user, 'is_authenticated', False):
        return False
    return bool(settings.DEBUG) or bool(user.is_superuser)


def _build_request(task, cleaned):
    if task == AIGenerationTask.AD_GENERATION:
        return AdGenerationRequest(
            business_name=cleaned.get('business_name', ''),
            category=cleaned.get('category', ''),
            language=cleaned.get('language', ''),
            city=cleaned.get('city', ''),
            description=cleaned.get('description', ''),
            target_audience=cleaned.get('target_audience', ''),
            instructions=cleaned.get('instructions', ''),
        )
    return PostGenerationRequest(
        title=cleaned.get('title', ''),
        source=cleaned.get('source', ''),
        language=cleaned.get('language', ''),
        category=cleaned.get('category', ''),
        context=cleaned.get('context', ''),
        instructions=cleaned.get('instructions', ''),
    )


@login_required
def sandbox(request):
    """
    Manual Content AI execution console.

    Not a public feature. Requires login and (DEBUG or superuser).
    """
    if not user_can_access_sandbox(request.user):
        raise PermissionDenied('Content AI sandbox is developer-only.')

    form = ContentAISandboxForm(request.POST or None)
    context = {
        'form': form,
        'prompt_preview': None,
        'result': None,
        'error': None,
        'elapsed_ms': None,
        'default_provider': getattr(settings, 'CONTENT_AI_PROVIDER', 'mock'),
    }

    if request.method == 'POST' and form.is_valid():
        task = form.cleaned_data['task']
        provider_name = form.cleaned_data.get('provider') or None
        schema_request = _build_request(task, form.cleaned_data)

        try:
            prompt_preview = get_prompt_template(task).build(schema_request)
            context['prompt_preview'] = prompt_preview

            started = time.perf_counter()
            result = ContentGenerationService().generate(
                task,
                schema_request,
                provider_name=provider_name,
            )
            context['elapsed_ms'] = round(
                (time.perf_counter() - started) * 1000,
                2,
            )
            context['result'] = result
        except (
            GenerationError,
            ProviderConfigurationError,
            ProviderNotFound,
        ) as exc:
            context['error'] = str(exc)

    return render(request, 'content_ai/sandbox.html', context)
