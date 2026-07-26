"""Featured-image generation orchestration for Editorial Workspace."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from content_ai.editorial.image.prompt import (
    FeaturedImageBrief,
    build_featured_image_brief,
)
from content_ai.editorial.image.style import (
    DEFAULT_IMAGE_STYLE,
    resolve_image_style,
)
from content_ai.providers.exceptions import (
    CapabilityError,
    GenerationError,
    ProviderConfigurationError,
)
from content_ai.providers.registry import get_provider

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ImageGenerationOutcome:
    prompt: str
    previous_prompt: str
    original_prompt: str
    explanation: str
    image_url: str
    revised_prompt: str
    provider: str
    aspect_ratio: str
    image_style: str
    status: str
    error: str = ''
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['metadata'] = dict(self.metadata or {})
        return payload


class FeaturedImageService:
    """
    Plan → prompt → generate featured images.

    Regeneration only re-runs image generation — never regenerates the article.
    """

    ASPECT_RATIO = '16:9'

    def prepare_brief(
        self,
        *,
        headline: str = '',
        lead: str = '',
        body: str = '',
        content_type: str = 'news',
        goal: str = '',
        category: str = '',
        tags: list[str] | None = None,
        publisher: str = '',
        image_style: str | None = None,
    ) -> FeaturedImageBrief:
        return build_featured_image_brief(
            headline=headline,
            lead=lead,
            body=body,
            content_type=content_type,
            goal=goal,
            category=category,
            tags=tags,
            publisher=publisher,
            image_style=image_style,
        )

    def generate(
        self,
        prompt: str,
        *,
        previous_prompt: str = '',
        original_prompt: str = '',
        explanation: str = '',
        image_style: str | None = None,
        provider_name: str | None = None,
    ) -> ImageGenerationOutcome:
        cleaned = (prompt or '').strip()
        if not cleaned:
            raise ValueError('Image prompt is required before generation.')

        prior = (previous_prompt or '').strip()
        style = resolve_image_style(image_style)
        logger.info(
            'FeaturedImageService.generate: provider=%s style=%s '
            'aspect_ratio=%s prompt_chars=%d prompt_preview=%r',
            provider_name or '(default)',
            style,
            self.ASPECT_RATIO,
            len(cleaned),
            cleaned[:240],
        )

        try:
            provider = get_provider(provider_name)
        except Exception as exc:  # noqa: BLE001
            raise ProviderConfigurationError(str(exc)) from exc

        caps = provider.capabilities()
        if not caps.supports('image_generation'):
            raise CapabilityError(
                f'Provider {provider.name!r} does not support image generation.'
            )

        try:
            result = provider.generate_image(
                cleaned,
                aspect_ratio=self.ASPECT_RATIO,
                image_style=style,
            )
        except (GenerationError, ProviderConfigurationError, CapabilityError):
            raise
        except Exception as exc:  # noqa: BLE001
            raise GenerationError(str(exc)) from exc

        image_url = (getattr(result, 'image_url', None) or '').strip()
        if not image_url:
            image_url = (getattr(result, 'b64_data_url', None) or '').strip()
        if not image_url:
            raise GenerationError('Image provider returned no image URL.')

        logger.info(
            'FeaturedImageService.generate ok: provider=%s model=%s '
            'url_preview=%s',
            getattr(result, 'provider', None) or provider.name,
            getattr(result, 'model', None),
            image_url[:160],
        )

        return ImageGenerationOutcome(
            prompt=cleaned,
            previous_prompt=prior,
            original_prompt=(original_prompt or '').strip(),
            explanation=(explanation or '').strip(),
            image_url=image_url,
            revised_prompt=(getattr(result, 'revised_prompt', None) or '').strip(),
            provider=getattr(result, 'provider', None) or provider.name,
            aspect_ratio=self.ASPECT_RATIO,
            image_style=style or DEFAULT_IMAGE_STYLE,
            status='generated',
            metadata=dict(getattr(result, 'metadata', None) or {}),
        )
