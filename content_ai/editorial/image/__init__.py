"""Editorial featured-image prompt and generation (workspace assist)."""

from content_ai.editorial.image.prompt import (
    FeaturedImageBrief,
    build_featured_image_brief,
)
from content_ai.editorial.image.service import FeaturedImageService

__all__ = [
    'FeaturedImageBrief',
    'FeaturedImageService',
    'build_featured_image_brief',
]
