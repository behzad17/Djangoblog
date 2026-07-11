"""Read-only query layer for useful links."""

from related_links.selectors.related import get_related_links
from related_links.selectors.visibility import list_publicly_visible_links

__all__ = [
    'get_related_links',
    'list_publicly_visible_links',
]
