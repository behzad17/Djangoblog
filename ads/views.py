from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db import models
from .models import AdCategory, Ad


def _visible_ads_queryset():
    """
    Base queryset for ads that should be visible on the site.
    """
    today = timezone.now().date()
    qs = Ad.objects.filter(
        is_active=True,
        is_approved=True,
        url_approved=True,
    )
    # Apply date filters only when set
    qs = qs.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today),
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today),
    )
    return qs.select_related("category")


def ad_category_list(request):
    """
    Dedicated advertisements landing page showing all ad categories and counts.
    """
    categories = AdCategory.objects.all().order_by("name")
    # Prefetch visible ads to show counts efficiently
    visible_ads = _visible_ads_queryset()
    counts = {cat.id: 0 for cat in categories}
    for ad in visible_ads:
        if ad.category_id in counts:
            counts[ad.category_id] += 1

    return render(
        request,
        "ads/ads_home.html",
        {
            "categories": categories,
            "ad_counts": counts,
        },
    )


def ad_list_by_category(request, category_slug):
    """
    List all visible ads for a specific category.
    Each category has its own dedicated URL.
    """
    category = get_object_or_404(AdCategory, slug=category_slug)
    ads = _visible_ads_queryset().filter(category=category)
    context = {
        "category": category,
        "ads": ads,
    }
    return render(request, "ads/ads_by_category.html", context)


def ad_detail(request, slug):
    """
    Detail page for a single ad.

    Each ad has its own slug-based URL. Only visible if the ad is currently
    active, approved, and within its date range.
    """
    ad = get_object_or_404(_visible_ads_queryset(), slug=slug)
    context = {
        "ad": ad,
    }
    return render(request, "ads/ad_detail.html", context)


# Create your views here.
