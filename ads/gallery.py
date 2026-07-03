"""
Centralized gallery logic for Peyvand advertisements.

Visibility: gallery images are stored for all ads but only shown on detail
pages when ad.plan == 'pro' and at least one gallery image exists.
"""

from __future__ import annotations

from PIL import Image

from django.core.exceptions import ValidationError
from django.db import transaction

from .cloudinary_cleanup import cloudinary_delivery_url

MAX_GALLERY_IMAGES = 10
MAX_IMAGE_BYTES = 5 * 1024 * 1024
DETAIL_LIGHTBOX_WIDTH = 1600
DETAIL_THUMB_SIZE = 144
DETAIL_PRIMARY_WIDTH = 1200


def _field_url(image_value, *, width=None, height=None, crop=None):
    """Return an optimized delivery URL for a CloudinaryField value."""
    optimized = cloudinary_delivery_url(
        image_value,
        width=width,
        height=height,
        crop=crop,
    )
    if optimized:
        return optimized
    try:
        url = getattr(image_value, "url", None)
        if url:
            return url
    except Exception:
        pass
    return str(image_value) if image_value else ""


def should_show_gallery_lightbox(ad) -> bool:
    """Whether the detail page should show the gallery lightbox UI."""
    if ad.plan != "pro":
        return False
    return _gallery_image_count(ad) > 0


def _gallery_image_count(ad) -> int:
    cache = getattr(ad, "_prefetched_objects_cache", None)
    if cache is not None and "gallery_images" in cache:
        return len(cache["gallery_images"])
    return ad.gallery_images.count()


def get_ordered_gallery_images(ad):
    """Return gallery rows ordered for display (excludes primary image)."""
    cache = getattr(ad, "_prefetched_objects_cache", None)
    if cache is not None and "gallery_images" in cache:
        return list(cache["gallery_images"])
    return list(ad.gallery_images.all())


def build_detail_slides(ad):
    """
    Build lightbox slides for Pro ads with gallery images.
    Primary image is always slide 1; gallery images follow in sort_order.
    """
    if not should_show_gallery_lightbox(ad):
        return []

    slides = [
        {
            "url": _field_url(ad.image, width=DETAIL_LIGHTBOX_WIDTH, crop="limit"),
            "thumb_url": _field_url(
                ad.image,
                width=DETAIL_THUMB_SIZE,
                height=DETAIL_THUMB_SIZE,
                crop="fill",
            ),
            "alt": ad.title,
            "is_primary": True,
        }
    ]
    for index, gallery_image in enumerate(get_ordered_gallery_images(ad), start=2):
        slides.append(
            {
                "url": _field_url(
                    gallery_image.image,
                    width=DETAIL_LIGHTBOX_WIDTH,
                    crop="limit",
                ),
                "thumb_url": _field_url(
                    gallery_image.image,
                    width=DETAIL_THUMB_SIZE,
                    height=DETAIL_THUMB_SIZE,
                    crop="fill",
                ),
                "alt": f"{ad.title} - تصویر {index}",
                "is_primary": False,
            }
        )
    return slides


def get_detail_image_context(ad):
    """Template context for ad detail image/gallery rendering."""
    show_lightbox = should_show_gallery_lightbox(ad)
    slides = build_detail_slides(ad) if show_lightbox else []
    return {
        "ad_show_gallery_lightbox": show_lightbox,
        "ad_gallery_slides": slides,
        "detail_primary_image_url": _field_url(
            ad.image,
            width=DETAIL_PRIMARY_WIDTH,
            crop="limit",
        ),
    }


def validate_uploaded_image(image):
    """Validate a single uploaded image file (size + Pillow)."""
    if not image:
        return image

    if hasattr(image, "size") and image.size > MAX_IMAGE_BYTES:
        raise ValidationError("حجم فایل تصویر باید حداکثر ۵ مگابایت باشد.")

    try:
        image.seek(0)
        img = Image.open(image)
        img.verify()
        image.seek(0)
        img = Image.open(image)
        img.load()
        image.seek(0)
    except Exception as exc:
        raise ValidationError("لطفاً یک فایل تصویر معتبر بارگذاری کنید.") from exc

    return image


def validate_gallery_capacity(ad, *, additional_images=0):
    """Raise ValidationError when gallery capacity would be exceeded."""
    current_count = ad.gallery_images.count()
    if current_count + additional_images > MAX_GALLERY_IMAGES:
        raise ValidationError(
            f"حداکثر {MAX_GALLERY_IMAGES} تصویر گالری مجاز است."
        )


def process_gallery_submission(ad, post_data, files):
    """
    Apply gallery deletes, reordering, and new uploads for an ad.

    POST fields:
      - gallery_order: comma-separated existing AdGalleryImage IDs
      - gallery_delete: comma-separated AdGalleryImage IDs to remove
      - gallery_images: multiple file upload field

    Returns a list of user-facing error strings (empty if successful).
    """
    from .models import AdGalleryImage

    errors = []

    delete_raw = (post_data.get("gallery_delete") or "").strip()
    delete_ids = {
        int(value)
        for value in delete_raw.split(",")
        if value.strip().isdigit()
    }

    order_raw = (post_data.get("gallery_order") or "").strip()
    order_ids = [
        int(value)
        for value in order_raw.split(",")
        if value.strip().isdigit()
    ]

    if hasattr(files, "getlist"):
        new_files = files.getlist("gallery_images")
    else:
        uploaded = (files or {}).get("gallery_images", [])
        if isinstance(uploaded, list):
            new_files = uploaded
        elif uploaded:
            new_files = [uploaded]
        else:
            new_files = []

    with transaction.atomic():
        from .models import Ad

        Ad.objects.select_for_update().get(pk=ad.pk)

        existing_qs = ad.gallery_images.all()
        existing_by_id = {item.id: item for item in existing_qs}

        for image_id in delete_ids:
            gallery_image = existing_by_id.pop(image_id, None)
            if gallery_image is not None and gallery_image.ad_id == ad.pk:
                gallery_image.delete()

        remaining_count = ad.gallery_images.count()
        if remaining_count + len(new_files) > MAX_GALLERY_IMAGES:
            errors.append(f"حداکثر {MAX_GALLERY_IMAGES} تصویر گالری مجاز است.")
            return errors

        for uploaded in new_files:
            try:
                validate_uploaded_image(uploaded)
            except ValidationError as error:
                errors.append(error.messages[0] if error.messages else str(error))
                return errors

        valid_order_ids = [
            image_id for image_id in order_ids if image_id in existing_by_id
        ]

        for sort_order, image_id in enumerate(valid_order_ids):
            AdGalleryImage.objects.filter(pk=image_id, ad=ad).update(sort_order=sort_order)

        next_sort_order = len(valid_order_ids)
        for uploaded in new_files:
            validate_gallery_capacity(ad, additional_images=1)
            AdGalleryImage.objects.create(
                ad=ad,
                image=uploaded,
                sort_order=next_sort_order,
            )
            next_sort_order += 1

    return errors
