"""Persist EditorialDraft objects as unpublished Blog posts.

AI must never publish. This layer only creates Draft status Posts.
"""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.utils import timezone

from blog.models import Post
from content_ai.editorial.drafts import EditorialDraft


class BlogDraftPersistenceError(Exception):
    """Raised when an EditorialDraft cannot be stored as a Blog draft."""


class BlogDraftPersistenceService:
    """
    Maps an in-memory ``EditorialDraft`` onto the existing Blog ``Post`` model.

    Always creates ``status=0`` (Draft). Never publishes, notifies, or indexes
    beyond what the existing Blog ``Post.save()`` / signals already do for drafts.
    """

    DRAFT_STATUS = 0

    def create_blog_draft(self, editorial_draft, author, category):
        """
        Create an unpublished Blog ``Post`` from ``editorial_draft``.

        Slug generation is delegated to ``Post.save()``.
        """
        if not isinstance(editorial_draft, EditorialDraft):
            raise BlogDraftPersistenceError(
                'editorial_draft must be an EditorialDraft instance.'
            )
        if author is None:
            raise BlogDraftPersistenceError('author is required.')
        if category is None:
            raise BlogDraftPersistenceError('category is required.')

        title = self._unique_title(
            (editorial_draft.title or '').strip() or 'Untitled AI draft'
        )
        content = editorial_draft.body or ''
        excerpt = editorial_draft.summary or ''

        # Blog Post has no dedicated language/metadata fields; map only
        # existing columns. Language and AI metadata remain on EditorialDraft.
        post = Post(
            title=title,
            content=content,
            excerpt=excerpt,
            author=author,
            category=category,
            status=self.DRAFT_STATUS,
        )

        try:
            with transaction.atomic():
                post.save()
        except IntegrityError as exc:
            raise BlogDraftPersistenceError(
                f'Could not create Blog draft: {exc}'
            ) from exc

        if post.status != self.DRAFT_STATUS:
            raise BlogDraftPersistenceError(
                'Blog draft was not saved with Draft status.'
            )
        return post

    def _unique_title(self, base_title: str) -> str:
        """Ensure title uniqueness required by the Blog Post model."""
        candidate = base_title[:200]
        if not Post.objects.filter(title=candidate).exists():
            return candidate

        stamp = timezone.now().strftime('%Y%m%d%H%M%S')
        suffix = f' ({stamp})'
        max_base = 200 - len(suffix)
        candidate = f'{base_title[:max_base]}{suffix}'
        if not Post.objects.filter(title=candidate).exists():
            return candidate

        # Extremely unlikely collision within the same second.
        for index in range(2, 50):
            suffix = f' ({stamp}-{index})'
            max_base = 200 - len(suffix)
            candidate = f'{base_title[:max_base]}{suffix}'
            if not Post.objects.filter(title=candidate).exists():
                return candidate
        raise BlogDraftPersistenceError(
            'Could not allocate a unique Blog draft title.'
        )
