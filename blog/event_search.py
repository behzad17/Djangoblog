from datetime import timedelta

from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from codestar.search_text import normalize_search_text, search_matches
from .templatetags.event_display import event_card_city


CITY_ALIASES = {
    'stockholm': ('Stockholm', 'استکهلم', 'استاکهلم'),
    'göteborg': ('Göteborg', 'Goteborg', 'Gothenburg', 'گوتنبرگ', 'یوتبوری', 'گوتنبورگ'),
    'malmö': ('Malmö', 'Malmo', 'مالمو', 'مالموئه'),
}
CITY_KEYS = {
    normalize_search_text(name): key
    for key, names in CITY_ALIASES.items()
    for name in names
}


def filter_events(posts, params):
    today = timezone.localdate()
    period = params.get('when', '')
    city = params.get('city', '')[:120].strip()
    query = params.get('q', '')[:200].strip()
    if not normalize_search_text(query):
        query = ''
    posts = posts.filter(event_start_date__isnull=False).alias(
        event_finish=Coalesce('event_end_date', 'event_start_date')
    )
    if period == 'archive':
        posts = posts.filter(event_finish__lt=today).order_by('-event_start_date', '-pk')
    else:
        posts = posts.filter(event_finish__gte=today).order_by('event_start_date', 'pk')
        if period == 'week':
            posts = posts.filter(event_start_date__lte=today + timedelta(days=6 - today.weekday()))
        elif period == 'month':
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            posts = posts.filter(event_start_date__lt=next_month)
        else:
            period = ''

    if city:
        normalized = normalize_search_text(city)
        city_key = CITY_KEYS.get(normalized, normalized)
        city_ids = []
        for post in posts.only('pk', 'event_city', 'event_location').select_related(None).iterator():
            candidate = normalize_search_text(event_card_city(post))
            if CITY_KEYS.get(candidate, candidate) == city_key:
                city_ids.append(post.pk)
        posts = posts.filter(pk__in=city_ids)

    if query:
        posts, matches = search_matches(posts, ('title', 'event_city', 'event_location', 'content', 'excerpt'), query)
        condition = Q()
        for match in matches:
            condition |= match
        key = CITY_KEYS.get(normalize_search_text(query))
        if key:
            for alias in CITY_ALIASES[key]:
                # City aliases are stored in either the dedicated or legacy location field.
                condition |= Q(event_city__iexact=alias) | Q(event_location__istartswith=alias)
        posts = posts.filter(condition)

    return posts, {'q': query, 'city': city, 'when': period}
