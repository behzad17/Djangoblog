"""Shared search normalization for Persian and Latin text."""

from django.db.models import CharField, F, Q, Value
from django.db.models.functions import Replace

REPLACEMENTS = (('ي', 'ی'), ('ك', 'ک'), ('\u200c', ''), (' ', ''))


def normalize_search_text(value):
    for source, target in REPLACEMENTS:
        value = value.replace(source, target)
    return value.casefold()


def search_matches(queryset, fields, query):
    """Return normalized substring predicates in field order."""
    needle = normalize_search_text(query)
    aliases = {}
    matches = []
    for index, field in enumerate(fields):
        expression = F(field)
        for source, target in REPLACEMENTS:
            expression = Replace(expression, Value(source), Value(target), output_field=CharField())
        alias = f'section_search_{index}'
        aliases[alias] = expression
        matches.append(Q(**{f'{alias}__icontains': needle}))
    return queryset.alias(**aliases), matches
