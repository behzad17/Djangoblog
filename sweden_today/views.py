from django.shortcuts import render


def handler404(request, exception):
    """
    Custom 404 error handler.
    Renders the 404.html template when a page is not found.
    """
    return render(request, '404.html', status=404) 