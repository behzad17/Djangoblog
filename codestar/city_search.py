"""Common Swedish place names and their Persian spellings."""

from .search_text import normalize_search_text

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
