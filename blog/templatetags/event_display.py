"""Presentation helpers for compact event cards."""
import re
from django import template

register = template.Library()


@register.filter
def event_card_city(post):
    city = getattr(post, "event_city", "")
    if city and city.strip():
        return city.strip()
    # Legacy records store city first, followed by a separated venue/address.
    location = (getattr(post, "event_location", "") or "").strip()
    return re.split(r"\s+[—–|]\s*|[,،;\n]", location, maxsplit=1)[0].strip()
