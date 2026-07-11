"""Normalize Community discussions and Blog posts for related-content selectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RelatedContentSource:
    """Category slug, searchable text, and mapping namespace for related content."""

    category_slug: str | None
    title: str
    body: str
    namespace: str


def related_content_source(obj: Any) -> RelatedContentSource:
    """
    Build a related-content source from a Discussion, Post, or source dataclass.

    Blog post ``content`` is stripped to plain text for keyword matching.
    """
    if isinstance(obj, RelatedContentSource):
        return obj

    from blog.models import Post
    from community.models import Discussion

    if isinstance(obj, Post):
        namespace = 'blog'
    elif isinstance(obj, Discussion):
        namespace = 'community'
    else:
        namespace = 'community'

    category = getattr(obj, 'category', None)
    category_slug = getattr(category, 'slug', None) if category else None
    title = getattr(obj, 'title', '') or ''

    body = getattr(obj, 'body', None)
    if body is None:
        body = getattr(obj, 'content', '') or ''
        if body and isinstance(obj, Post):
            from blog.utils import html_to_plain_text

            body = html_to_plain_text(body)
    else:
        body = body or ''

    return RelatedContentSource(
        category_slug=category_slug,
        title=title,
        body=body,
        namespace=namespace,
    )
