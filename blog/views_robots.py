from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def robots_txt(request):
    """Serve robots.txt file."""
    context = {
        'sitemap_url': request.build_absolute_uri('/sitemap.xml')
    }
    content = render_to_string('robots.txt', context)
    response = HttpResponse(content, content_type='text/plain')
    return response

