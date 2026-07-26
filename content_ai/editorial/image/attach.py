"""Attach generated featured images to Blog draft posts via Cloudinary."""

from __future__ import annotations

import base64
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class FeaturedImageAttachError(Exception):
    """Raised when a generated image cannot be attached to a draft."""


_DATA_URL_RE = re.compile(
    r'^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$',
    re.DOTALL,
)


def upload_featured_image_asset(
    image_url: str,
    *,
    public_id_prefix: str = 'peyvand/editorial/featured',
    session_id: str = '',
) -> dict[str, Any]:
    """
    Upload an image URL or data-URL to Cloudinary.

    Returns dict with public_id, secure_url, and raw upload response fields.
    """
    source = (image_url or '').strip()
    if not source:
        raise FeaturedImageAttachError('No image URL to upload.')

    try:
        import cloudinary.uploader
    except ImportError as exc:
        raise FeaturedImageAttachError(
            'Cloudinary is not available for featured image upload.'
        ) from exc

    folder = public_id_prefix.rstrip('/')
    options: dict[str, Any] = {
        'folder': folder,
        'resource_type': 'image',
        'overwrite': True,
    }
    if session_id:
        options['public_id'] = f'{folder}/{session_id[:32]}'

    file_arg: Any = source
    match = _DATA_URL_RE.match(source)
    if match:
        # Cloudinary accepts raw bytes for data-URL uploads in tests/mocks.
        try:
            file_arg = base64.b64decode(match.group(2))
        except Exception as exc:  # noqa: BLE001
            raise FeaturedImageAttachError(
                'Invalid base64 image data URL.'
            ) from exc

    try:
        result = cloudinary.uploader.upload(file_arg, **options)
    except Exception as exc:  # noqa: BLE001
        logger.exception('Cloudinary featured image upload failed')
        raise FeaturedImageAttachError(
            f'Failed to upload featured image: {exc}'
        ) from exc

    public_id = (result or {}).get('public_id') or ''
    secure_url = (result or {}).get('secure_url') or (result or {}).get('url') or ''
    if not public_id:
        raise FeaturedImageAttachError(
            'Cloudinary upload returned no public_id.'
        )
    return {
        'public_id': public_id,
        'secure_url': secure_url,
        'bytes': (result or {}).get('bytes'),
        'format': (result or {}).get('format'),
        'width': (result or {}).get('width'),
        'height': (result or {}).get('height'),
    }


def attach_featured_image_to_post(post, *, public_id: str) -> Any:
    """Set ``Post.featured_image`` to a Cloudinary public_id and save."""
    if post is None:
        raise FeaturedImageAttachError('Post is required.')
    pid = (public_id or '').strip()
    if not pid:
        raise FeaturedImageAttachError('Cloudinary public_id is required.')
    post.featured_image = pid
    post.save(update_fields=['featured_image'])
    return post
