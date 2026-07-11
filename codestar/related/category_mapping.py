"""Shared helpers for namespace-aware category mapping lookups."""

from __future__ import annotations

from codestar.related.sources import RelatedContentSource


def mapped_values_for_source(
    source: RelatedContentSource,
    *,
    community_map: dict[str, list[str]],
    blog_map: dict[str, list[str]],
) -> list[str]:
    """Return mapped values for a source category slug and namespace."""
    slug = source.category_slug or ''
    if source.namespace == 'blog':
        return list(blog_map.get(slug, []))
    return list(community_map.get(slug, []))
