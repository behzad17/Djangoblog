"""
Search view for blog posts.

This module provides a fast, safe, and isolated search feature with filtering
and sorting capabilities.
"""
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db.models.functions import Coalesce

from .models import Post, Category


def search_posts(request):
    """
    Search, filter, and sort blog posts.
    
    GET Parameters:
    - q: Search query (searches in title, content, excerpt)
    - category: Category slug or ID to filter by
    - sort: 'newest' or 'popular' (defaults to 'newest')
    - page: Page number for pagination
    
    Returns:
    - Rendered search results page with pagination
    """
    # Get GET parameters
    query = request.GET.get('q', '').strip()
    category_param = request.GET.get('category', '')
    sort_param = request.GET.get('sort', 'newest')
    page_number = request.GET.get('page', 1)
    
    # Start with published posts only (same filter as main listing)
    queryset = Post.objects.filter(status=1).select_related('category', 'author')
    
    # Apply search query
    if query:
        # Search in title, content, and excerpt using Q objects
        search_q = Q(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        )
        queryset = queryset.filter(search_q)
    
    # Apply category filter
    if category_param:
        try:
            # Try to filter by slug first (more common)
            if category_param.isdigit():
                # If it's a number, treat as ID
                queryset = queryset.filter(category_id=int(category_param))
            else:
                # Otherwise treat as slug
                queryset = queryset.filter(category__slug=category_param)
        except (ValueError, Category.DoesNotExist):
            # Invalid category parameter, ignore it
            pass
    
    # Apply sorting
    if sort_param == 'popular':
        # Try to sort by view count if PostViewCount exists
        # Use Coalesce to handle posts without view_count_cache (default to 0)
        try:
            # Annotate with view count, defaulting to 0 if no view_count_cache exists
            queryset = queryset.annotate(
                view_count=Coalesce('view_count_cache__total_views', 0)
            ).order_by('-view_count', '-created_on')
        except Exception:
            # If view_count_cache doesn't exist or fails, fallback to newest
            queryset = queryset.order_by('-created_on')
    else:
        # Default: sort by newest (created_on descending)
        queryset = queryset.order_by('-created_on')
    
    # Annotate with comment count (for display)
    queryset = queryset.annotate(
        comment_count=Count('comments', filter=Q(comments__approved=True))
    )
    
    # Paginate results (12 per page for good performance)
    paginator = Paginator(queryset, 12)
    
    try:
        page_obj = paginator.page(page_number)
    except Exception:
        # Invalid page number, default to page 1
        page_obj = paginator.page(1)
    
    # Get all categories for the dropdown
    categories = Category.objects.all().order_by('name')
    
    # Prepare context
    context = {
        'query': query,
        'category_param': category_param,
        'sort_param': sort_param,
        'page_obj': page_obj,
        'categories': categories,
        'total_count': paginator.count,
        'results': page_obj.object_list,
    }
    
    return render(request, 'blog/search.html', context)

