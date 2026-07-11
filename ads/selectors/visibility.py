from django.db.models import BooleanField, Case, F, IntegerField, Q, QuerySet, Value, When
from django.utils import timezone

from ads.models import Ad


def list_visible_ads() -> QuerySet[Ad]:
    """
    Base queryset for ads shown in public listings.

    Requires admin approval and active flag; URL approval is not required here
    because listings may show ads before URL review completes.
    """
    today = timezone.now().date()
    now = timezone.now()
    qs = Ad.objects.filter(
        is_active=True,
        is_approved=True,
    )
    qs = qs.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=today),
        Q(end_date__isnull=True) | Q(end_date__gte=today),
    )
    qs = qs.annotate(
        is_currently_featured=Case(
            When(
                Q(is_featured=True)
                & (Q(featured_until__isnull=True) | Q(featured_until__gt=now)),
                then=True,
            ),
            default=False,
            output_field=BooleanField(),
        )
    )
    qs = qs.annotate(
        priority_value=Case(
            When(
                is_currently_featured=True,
                then=Case(
                    When(
                        featured_priority__isnull=False,
                        then=F('featured_priority'),
                    ),
                    default=Value(999999, output_field=IntegerField()),
                ),
            ),
            default=Value(9999999, output_field=IntegerField()),
        )
    ).order_by('-is_currently_featured', 'priority_value', '-created_on')
    return qs.select_related('category', 'owner')


def list_publicly_visible_ads() -> QuerySet[Ad]:
    """Return ads that are fully visible to the public (including URL approval)."""
    return list_visible_ads().filter(url_approved=True)


def list_publicly_visible_pro_ads() -> QuerySet[Ad]:
    """Return fully visible Pro ads suitable for public detail page links."""
    return list_publicly_visible_ads().filter(plan='pro')
