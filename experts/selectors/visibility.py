from django.db.models import Count, QuerySet

from askme.models import Moderator


def list_publicly_visible_experts() -> QuerySet[Moderator]:
    """
    Return experts eligible for public directory and related-content surfaces.

    Visibility is limited to publication rules only (currently ``is_active``).
    Presentation concerns such as placeholder images or display names are
    handled in templates, not in the selector.
    """
    return (
        Moderator.objects.filter(is_active=True)
        .select_related('user')
        .annotate(display_question_count=Count('questions'))
        .order_by('expert_title', 'user__username')
    )
