"""Persist EditorialDraft objects as unpublished Blog posts.

AI must never publish. This layer only creates/updates Draft status Posts.
"""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from blog.models import Category, Post
from content_ai.editorial.drafts import EditorialDraft


class BlogDraftPersistenceError(Exception):
    """Raised when an EditorialDraft cannot be stored as a Blog draft."""


class BlogDraftPersistenceService:
    """
    Maps an in-memory ``EditorialDraft`` onto the existing Blog ``Post`` model.

    Always uses ``status=0`` (Draft). Never publishes, notifies, or indexes
    beyond what the existing Blog ``Post.save()`` / signals already do for drafts.
    """

    DRAFT_STATUS = 0
    DEFAULT_CATEGORY_SLUG = 'news'
    DEFAULT_CATEGORY_NAME = 'News'

    def create_blog_draft(
        self,
        editorial_draft,
        author,
        category=None,
        *,
        source_url: str = '',
    ):
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
        category = category or self.resolve_category(
            (editorial_draft.metadata or {}).get('category') or ''
        )
        if category is None:
            raise BlogDraftPersistenceError('category is required.')

        title = self._unique_title(
            (editorial_draft.title or '').strip() or 'Untitled AI draft'
        )
        content = self._compose_content(editorial_draft)
        excerpt = self._excerpt_for(editorial_draft)

        post = Post(
            title=title,
            content=content,
            excerpt=excerpt,
            author=author,
            category=category,
            status=self.DRAFT_STATUS,
            external_url=(source_url or '').strip() or None,
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

    def update_blog_draft(
        self,
        post: Post,
        editorial_draft,
        *,
        category=None,
        source_url: str | None = None,
    ) -> Post:
        """Update an existing Draft ``Post`` in place. Never publishes."""
        if not isinstance(post, Post):
            raise BlogDraftPersistenceError('post must be a Blog Post.')
        if not isinstance(editorial_draft, EditorialDraft):
            raise BlogDraftPersistenceError(
                'editorial_draft must be an EditorialDraft instance.'
            )
        if post.status != self.DRAFT_STATUS:
            raise BlogDraftPersistenceError(
                'Only Draft posts can be updated from Editorial Workspace.'
            )
        if post.is_deleted:
            raise BlogDraftPersistenceError(
                'Cannot update a deleted Blog draft.'
            )

        title = self._unique_title(
            (editorial_draft.title or '').strip() or post.title or 'Untitled AI draft',
            exclude_pk=post.pk,
        )
        post.title = title
        post.content = self._compose_content(editorial_draft)
        post.excerpt = self._excerpt_for(editorial_draft)
        post.status = self.DRAFT_STATUS
        if category is not None:
            post.category = category
        if source_url is not None:
            post.external_url = (source_url or '').strip() or None

        try:
            with transaction.atomic():
                post.save()
        except IntegrityError as exc:
            raise BlogDraftPersistenceError(
                f'Could not update Blog draft: {exc}'
            ) from exc
        return post

    def resolve_category(self, name_or_slug: str = '') -> Category:
        """Resolve a category by slug/name, or create/get a default News category."""
        raw = (name_or_slug or '').strip()
        if raw:
            slug = slugify(raw, allow_unicode=True) or raw
            category = (
                Category.objects.filter(slug__iexact=slug).first()
                or Category.objects.filter(name__iexact=raw).first()
            )
            if category is not None:
                return category
        category = (
            Category.objects.filter(slug=self.DEFAULT_CATEGORY_SLUG).first()
            or Category.objects.filter(name__iexact=self.DEFAULT_CATEGORY_NAME).first()
            or Category.objects.order_by('id').first()
        )
        if category is not None:
            return category
        category, _ = Category.objects.get_or_create(
            slug=self.DEFAULT_CATEGORY_SLUG,
            defaults={'name': self.DEFAULT_CATEGORY_NAME},
        )
        return category

    def _compose_content(self, editorial_draft: EditorialDraft) -> str:
        lead = (getattr(editorial_draft, 'lead', '') or '').strip()
        body = (editorial_draft.body or '').strip()
        if lead and body:
            if body.startswith(lead):
                return body
            return f'{lead}\n\n{body}'
        return body or lead

    def _excerpt_for(self, editorial_draft: EditorialDraft) -> str:
        summary = (editorial_draft.summary or '').strip()
        if summary:
            return summary
        lead = (getattr(editorial_draft, 'lead', '') or '').strip()
        return lead[:500]

    def _unique_title(self, base_title: str, *, exclude_pk=None) -> str:
        """Ensure title uniqueness required by the Blog Post model."""
        candidate = base_title[:200]
        qs = Post.objects.all()
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.filter(title=candidate).exists():
            return candidate

        stamp = timezone.now().strftime('%Y%m%d%H%M%S')
        suffix = f' ({stamp})'
        max_base = 200 - len(suffix)
        candidate = f'{base_title[:max_base]}{suffix}'
        if not qs.filter(title=candidate).exists():
            return candidate

        for index in range(2, 50):
            suffix = f' ({stamp}-{index})'
            max_base = 200 - len(suffix)
            candidate = f'{base_title[:max_base]}{suffix}'
            if not qs.filter(title=candidate).exists():
                return candidate
        raise BlogDraftPersistenceError(
            'Could not allocate a unique Blog draft title.'
        )
