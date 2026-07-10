from django.views.decorators.http import require_http_methods

from django.shortcuts import render

from community.selectors.categories import get_category_by_slug, list_active_categories
from community.selectors.search import search_discussions
from community.views.discussions import _paginate


@require_http_methods(['GET'])
def community_search(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()

    selected_category = None
    if category_slug:
        try:
            selected_category = get_category_by_slug(category_slug)
        except Exception:
            selected_category = None

    queryset = search_discussions(query, category=selected_category)
    page_obj = _paginate(request, queryset)

    return render(
        request,
        'community/discussion_search.html',
        {
            'query': query,
            'page_obj': page_obj,
            'discussions': page_obj.object_list,
            'categories': list_active_categories(),
            'selected_category': selected_category,
            'total_count': page_obj.paginator.count,
        },
    )
