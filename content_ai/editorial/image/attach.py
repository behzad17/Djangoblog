"""Attach generated featured images to Blog draft posts via Cloudinary."""

from __future__ import annotations

import base64
import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class FeaturedImageAttachError(Exception):
    """Raised when a generated image cannot be attached to a draft."""


_DATA_URL_RE = re.compile(
    r'^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$',
    re.DOTALL,
)
# Cloudinary delivery URL → public_id (with optional folder path).
_CLOUDINARY_UPLOAD_RE = re.compile(
    r'/upload/(?:[^/]+/)*?(?:v\d+/)?(.+?)(?:\.[a-zA-Z0-9]+)?$'
)


def extract_cloudinary_public_id(value: str) -> str:
    """
    Return a Cloudinary public_id from a public_id string or delivery URL.

    Examples:
    - ``peyvand/editorial/featured/abc`` → same
    - ``https://res.cloudinary.com/.../upload/v123/peyvand/editorial/featured/abc.png``
      → ``peyvand/editorial/featured/abc``
    """
    raw = (value or '').strip()
    if not raw:
        return ''
    if raw.startswith('data:'):
        return ''
    if 'res.cloudinary.com' in raw or '/image/upload/' in raw or '/upload/' in raw:
        path = urlparse(raw).path
        match = _CLOUDINARY_UPLOAD_RE.search(path)
        if match:
            return match.group(1).lstrip('/')
        return ''
    # Already a public_id (possibly with folders).
    return raw.lstrip('/')


def resolve_featured_image_public_id(featured: dict[str, Any] | None) -> str:
    """Pick the best Cloudinary public_id from featured-image session state."""
    state = dict(featured or {})
    for key in (
        'cloudinary_public_id',
        'preview_cloudinary_public_id',
        'attached_url',
        'image_url',
    ):
        found = extract_cloudinary_public_id(str(state.get(key) or ''))
        if found and found != 'placeholder':
            return found
    return ''


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

    # Reuse an existing Cloudinary asset without re-uploading when possible.
    existing = extract_cloudinary_public_id(source)
    if existing and source.startswith('http') and 'res.cloudinary.com' in source:
        logger.info(
            'Cloudinary featured image reuse existing public_id=%s',
            existing,
        )
        return {
            'public_id': existing,
            'secure_url': source,
            'bytes': None,
            'format': None,
            'width': None,
            'height': None,
            'reused': True,
        }

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
    # ``folder`` already namespaces the asset — public_id must be the leaf only,
    # otherwise Cloudinary doubles the path (folder/folder/id).
    if session_id:
        leaf = re.sub(r'[^a-zA-Z0-9_-]+', '-', str(session_id)[:32]).strip('-')
        if leaf:
            options['public_id'] = leaf

    file_arg: Any = source
    match = _DATA_URL_RE.match(source)
    if match:
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
    logger.info(
        'Cloudinary featured image uploaded public_id=%s url=%s',
        public_id,
        (secure_url or '')[:160],
    )
    return {
        'public_id': public_id,
        'secure_url': secure_url,
        'bytes': (result or {}).get('bytes'),
        'format': (result or {}).get('format'),
        'width': (result or {}).get('width'),
        'height': (result or {}).get('height'),
        'reused': False,
    }


def attach_featured_image_to_post(post, *, public_id: str) -> Any:
    """Set ``Post.featured_image`` to a Cloudinary public_id and save."""
    if post is None:
        raise FeaturedImageAttachError('Post is required.')
    pid = extract_cloudinary_public_id(public_id) or (public_id or '').strip()
    if not pid or pid == 'placeholder':
        raise FeaturedImageAttachError('Cloudinary public_id is required.')

    # Full save — CloudinaryField has historically not persisted reliably with
    # update_fields=['featured_image'] alone.
    post.featured_image = pid
    post.save()
    post.refresh_from_db(fields=['featured_image'])

    stored = ''
    raw = post.featured_image
    if raw is not None:
        stored = (
            getattr(raw, 'public_id', None)
            or extract_cloudinary_public_id(str(raw))
            or str(raw)
        )
    stored = (stored or '').strip()
    logger.info(
        'attach_featured_image_to_post post_id=%s requested=%s stored=%s',
        getattr(post, 'pk', None),
        pid,
        stored,
    )
    if not stored or stored == 'placeholder':
        raise FeaturedImageAttachError(
            f'Post.featured_image remained placeholder after save '
            f'(requested public_id={pid!r}).'
        )
    return post
