from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import RelatedLink, UsefulLinkCategory, UsefulLinkResourceType


# Legacy ?type= values from the old CharField choices (kept for URL compatibility).
LEGACY_TYPE_TO_CATEGORY_SLUG = {
    'podcast': 'podcasts',
    'video': 'movies-videos',
    'radio': 'radio',
    'social': 'social-media',
    'website': 'essential-apps',
    'file': 'adult-education',
}

# Map legacy ?type= filter values to new resource type slugs where they differ.
LEGACY_TYPE_TO_RESOURCE_SLUG = {
    'social': 'social-media',
    'file': 'document-pdf',
}


def _resolve_resource_type_slug(raw_type):
    if not raw_type:
        return None
    return LEGACY_TYPE_TO_RESOURCE_SLUG.get(raw_type, raw_type)


def _active_link_count_annotation():
    return Count('links', filter=Q(links__is_active=True))


def links_list(request):
    """Topic directory landing page or category link listing."""
    category_slug = request.GET.get('category')
    legacy_type = request.GET.get('type')

    if not category_slug and legacy_type in LEGACY_TYPE_TO_CATEGORY_SLUG:
        category_slug = LEGACY_TYPE_TO_CATEGORY_SLUG.get(legacy_type)
        if category_slug:
            return redirect(f"{reverse('related_links:links_list')}?category={category_slug}")

    if not category_slug:
        categories = (
            UsefulLinkCategory.objects.filter(is_active=True)
            .annotate(link_count=_active_link_count_annotation())
        )
        return render(
            request,
            'related_links/links_directory.html',
            {'categories': categories},
        )

    active_category = get_object_or_404(
        UsefulLinkCategory.objects.annotate(link_count=_active_link_count_annotation()),
        slug=category_slug,
        is_active=True,
    )

    links = RelatedLink.objects.filter(
        is_active=True,
        category=active_category,
    ).select_related('resource_type')

    active_type = request.GET.get('type')
    type_slug = _resolve_resource_type_slug(active_type)
    if type_slug:
        resource_type = UsefulLinkResourceType.objects.filter(
            slug=type_slug,
            is_active=True,
        ).first()
        if resource_type:
            links = links.filter(resource_type=resource_type)
            active_type = type_slug
        else:
            active_type = None
    else:
        active_type = None

    types = UsefulLinkResourceType.objects.filter(is_active=True).values_list(
        'slug',
        'name_fa',
    )

    context = {
        'links': links,
        'types': types,
        'active_type': active_type,
        'active_category': active_category,
        'category_has_links': active_category.link_count > 0,
        'show_type_filters': active_category.link_count >= 8,
    }
    return render(request, 'related_links/links_category.html', context)
