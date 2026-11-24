import re
import unicodedata

from codestar.city_search import CITY_ALIASES
from codestar.search_text import normalize_search_text

from ads.config.subcategories import SUBCATEGORIES


EXTRA_CITY_ALIASES = (
    ("Borås", "بوروس", "بوراس"),
    ("Uppsala", "اوپسالا", "اپسالا"),
    ("Solna", "سولنا", "سلنا"),
    ("Mölndal", "مولندال", "ملندال"),
    ("Sollentuna", "سولنتونا"),
    ("Lund", "لوند", "لند"),
    ("Helsingborg", "هلسینگبورگ", "هلسینگبوری"),
    ("Linköping", "لینشوپینگ", "لینکوپینگ"),
    ("Norrköping", "نورشوپینگ", "نورکوپینگ"),
    ("Jönköping", "یونشوپینگ", "یونکوپینگ"),
    ("Västerås", "وستروس", "وستراس"),
    ("Örebro", "اوربرو"),
    ("Umeå", "اومئو", "اومه‌او", "اومیا"),
    ("Karlstad", "کارلستاد"),
    ("Eskilstuna", "اسکیلستونا"),
    ("Halmstad", "هالمستاد"),
    ("Södertälje", "سودرتلیه", "سودرتالیه"),
    ("Sundsvall", "سوندسوال"),
    ("Växjö", "وکشو"),
    ("Bollebygd", "بوله‌بیگد", "بولبیگد"),
)
CITY_SEPARATOR = re.compile(r"[/,،;|]")


def city_key(value):
    folded = unicodedata.normalize("NFKD", normalize_search_text(value))
    return "".join(char for char in folded if not unicodedata.combining(char))


CITY_NAMES = {
    city_key(alias): names[0]
    for names in (*CITY_ALIASES.values(), *EXTRA_CITY_ALIASES)
    for alias in names
}


def city_parts(value):
    value = value.strip()
    return [part.strip() for part in CITY_SEPARATOR.split(value) if part.strip()]


def matching_cities(value, available):
    if not value:
        return available
    needle = city_key(value)
    canonical = CITY_NAMES.get(needle)
    return [
        city for city in available
        if city_key(city) == needle
        or any(CITY_NAMES.get(city_key(part), city_key(part)) == (canonical or needle)
               for part in city_parts(city))
    ]


def filter_directory(ads, query, city):
    available = list(ads.exclude(city="").order_by().values_list("city", flat=True).distinct())
    choices = sorted(
        {CITY_NAMES.get(city_key(part), part) for value in available for part in city_parts(value)},
        key=city_key,
    )
    if city:
        ads = ads.filter(city__in=matching_cities(city, available))
    if query:
        terms = [normalize_search_text(word) for word in query.split()]
        matches = []
        candidates = ads.order_by().values_list(
            "pk", "title", "category__slug", "category__name", "subcategory",
        )
        for pk, title, category_slug, category, subcategory in candidates.iterator():
            service = SUBCATEGORIES.get(category_slug, {}).get(subcategory, "")
            text = normalize_search_text(f"{title} {category} {service}")
            if all(term in text for term in terms):
                matches.append(pk)
        ads = ads.filter(pk__in=matches)
    return ads, choices
