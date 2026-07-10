from django.http import JsonResponse


def health_check(request):
    """Placeholder endpoint to verify the Community URL namespace is mounted."""
    return JsonResponse({'status': 'ok', 'app': 'community'})
