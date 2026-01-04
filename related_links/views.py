from django.shortcuts import render
from .models import RelatedLink, LinkType


def links_list(request):
    """Display list of related links with optional type filtering."""
    links = RelatedLink.objects.filter(is_active=True)
    
    # Filter by type if provided
    active_type = request.GET.get('type')
    if active_type and active_type in [choice[0] for choice in LinkType.choices]:
        links = links.filter(link_type=active_type)
    else:
        active_type = None
    
    # Get all types for filter tabs
    types = LinkType.choices
    
    context = {
        'links': links,
        'types': types,
        'active_type': active_type,
    }
    
    return render(request, 'related_links/links_list.html', context)

