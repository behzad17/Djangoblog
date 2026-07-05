from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import LinkType, RelatedLink, UsefulLinkCategory


LINK_TYPE_TO_CATEGORY_SLUG = {
    LinkType.PODCAST: 'podcasts',
    LinkType.VIDEO: 'movies-videos',
    LinkType.RADIO: 'radio',
    LinkType.SOCIAL: 'social-media',
    LinkType.WEBSITE: 'essential-apps',
    LinkType.FILE: 'adult-education',
}


def _active_link_count_annotation():
    return Count('links', filter=Q(links__is_active=True))


def links_list(request):
    """Topic directory landing page or category link listing."""
    category_slug = request.GET.get('category')
    legacy_type = request.GET.get('type')

    if not category_slug and legacy_type in dict(LinkType.choices):
        category_slug = LINK_TYPE_TO_CATEGORY_SLUG.get(legacy_type)
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

    links = RelatedLink.objects.filter(is_active=True, category=active_category)

    active_type = request.GET.get('type')
    if active_type and active_type in dict(LinkType.choices):
        links = links.filter(link_type=active_type)
    else:
        active_type = None

    context = {
        'links': links,
        'types': LinkType.choices,
        'active_type': active_type,
        'active_category': active_category,
        'category_has_links': active_category.link_count > 0,
    }
    return render(request, 'related_links/links_category.html', context)
