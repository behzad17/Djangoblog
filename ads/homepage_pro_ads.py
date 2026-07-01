"""Homepage Pro ads selection — visibility rules and rotation."""

import hashlib

from django.db.models import Q
from django.utils import timezone

from ads.models import Ad

HOMEPAGE_PRO_ADS_LIMIT = 6
HOMEPAGE_PRO_NEWEST_COUNT = 3
HOMEPAGE_PRO_ROTATING_COUNT = 3
HOMEPAGE_PRO_ROTATION_SECONDS = 12 * 3600


def _visible_pro_ads_queryset():
    """Active, approved Pro ads within optional start/end date window."""
    today = timezone.now().date()
    return (
        Ad.objects.filter(
            is_active=True,
            is_approved=True,
            plan="pro",
        )
        .filter(
            Q(start_date__isnull=True) | Q(start_date__lte=today),
            Q(end_date__isnull=True) | Q(end_date__gte=today),
        )
        .select_related("category")
        .order_by("-created_on")
    )


def _rotation_score(ad_id, bucket):
    digest = hashlib.md5(f"{bucket}:{ad_id}".encode()).hexdigest()
    return int(digest, 16)


def get_homepage_pro_ads():
    """
    Return up to six visible Pro ads for the homepage.

    - Six or fewer active Pro ads: return all, newest first.
    - More than six: three newest plus three rotating picks from the rest.
      Rotation bucket changes every 12 hours (stable across requests/dynos).
    """
    base_qs = _visible_pro_ads_queryset()
    ordered_ids = list(base_qs.values_list("id", flat=True))

    if not ordered_ids:
        return []

    if len(ordered_ids) <= HOMEPAGE_PRO_ADS_LIMIT:
        return list(base_qs.filter(id__in=ordered_ids))

    newest_ids = ordered_ids[:HOMEPAGE_PRO_NEWEST_COUNT]
    remaining_ids = ordered_ids[HOMEPAGE_PRO_NEWEST_COUNT:]
    bucket = int(timezone.now().timestamp()) // HOMEPAGE_PRO_ROTATION_SECONDS
    rotating_ids = sorted(
        remaining_ids,
        key=lambda ad_id: _rotation_score(ad_id, bucket),
    )[:HOMEPAGE_PRO_ROTATING_COUNT]
    selected_ids = newest_ids + rotating_ids

    ads_by_id = {ad.id: ad for ad in base_qs.filter(id__in=selected_ids)}
    return [ads_by_id[ad_id] for ad_id in selected_ids if ad_id in ads_by_id]
