"""
Cloudinary asset lifecycle helpers for advertisement images.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_public_id(image_value):
    """Extract a Cloudinary public_id from a field value."""
    if not image_value:
        return None
    public_id = getattr(image_value, "public_id", None)
    if public_id:
        return str(public_id)
    value = str(image_value).strip()
    return value or None


def cloudinary_delivery_url(image_value, *, width=None, height=None, crop=None):
    """
    Build an optimized Cloudinary delivery URL (f_auto, q_auto).
    Falls back to the field URL when public_id cannot be resolved.
    """
    public_id = get_public_id(image_value)
    if not public_id:
        return ""

    try:
        from cloudinary.utils import cloudinary_url

        options = {
            "fetch_format": "auto",
            "quality": "auto",
        }
        if width is not None:
            options["width"] = width
        if height is not None:
            options["height"] = height
        if crop:
            options["crop"] = crop
        url, _ = cloudinary_url(public_id, **options)
        return url
    except Exception as exc:
        logger.warning("Failed to build Cloudinary delivery URL for %s: %s", public_id, exc)
        try:
            fallback_url = getattr(image_value, "url", None)
            if fallback_url:
                return fallback_url
        except Exception:
            pass
        return str(image_value) if image_value else ""


def destroy_cloudinary_asset(image_value):
    """Delete a single Cloudinary asset. Failures are logged, not raised."""
    public_id = get_public_id(image_value)
    if not public_id:
        return

    try:
        import cloudinary.uploader

        cloudinary.uploader.destroy(public_id)
        logger.info("Deleted Cloudinary asset: %s", public_id)
    except Exception as exc:
        logger.warning("Failed to delete Cloudinary asset %s: %s", public_id, exc)
