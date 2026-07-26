"""Editorial featured-image prompt and generation (workspace assist)."""

from content_ai.editorial.image.attach import (
    FeaturedImageAttachError,
    attach_featured_image_to_post,
    extract_cloudinary_public_id,
    resolve_featured_image_public_id,
    upload_featured_image_asset,
)
from content_ai.editorial.image.planner import ImagePlan, plan_featured_image
from content_ai.editorial.image.prompt import (
    FeaturedImageBrief,
    build_featured_image_brief,
)
from content_ai.editorial.image.service import FeaturedImageService
from content_ai.editorial.image.style import (
    DEFAULT_IMAGE_STYLE,
    list_image_styles_for_ui,
    resolve_image_style,
)

__all__ = [
    'DEFAULT_IMAGE_STYLE',
    'FeaturedImageAttachError',
    'FeaturedImageBrief',
    'FeaturedImageService',
    'ImagePlan',
    'attach_featured_image_to_post',
    'build_featured_image_brief',
    'extract_cloudinary_public_id',
    'list_image_styles_for_ui',
    'plan_featured_image',
    'resolve_featured_image_public_id',
    'resolve_image_style',
    'upload_featured_image_asset',
]
