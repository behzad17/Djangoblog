"""Rate policies for post creation by the site's named publishing accounts."""


POST_CREATION_EXEMPT_USERNAMES = frozenset({'BJBenny', 'admin'})


def _is_exempt_publisher(request):
    user = request.user
    return (
        user.is_authenticated
        and user.get_username() in POST_CREATION_EXEMPT_USERNAMES
    )


def post_creation_user_rate(group, request):
    """Keep the normal user quota unless this authenticated account is exempt."""
    return None if _is_exempt_publisher(request) else '5/h'


def post_creation_ip_rate(group, request):
    """Exempt the same accounts even when their IP's shared quota is exhausted."""
    return None if _is_exempt_publisher(request) else '20/h'
