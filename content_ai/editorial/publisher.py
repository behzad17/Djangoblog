"""Bridge from the AI editorial domain to the Blog domain.

Despite the name, this publisher never publishes. It only creates Blog drafts.
Human editors remain responsible for publication.
"""

from __future__ import annotations

from content_ai.editorial.drafts import EditorialDraft
from content_ai.editorial.persistence import (
    BlogDraftPersistenceError,
    BlogDraftPersistenceService,
)


class EditorialDraftPublisherError(Exception):
    """Raised when an EditorialDraft cannot be published to the Blog as a draft."""


class EditorialDraftPublisher:
    """
    Reusable bridge: ``EditorialDraft`` → Blog ``Post`` (Draft only).

    Delegates persistence to ``BlogDraftPersistenceService`` so Blog creation
    rules (slug generation, uniqueness, Draft status) stay in one place.
    """

    def __init__(self, persistence_service=None):
        self._persistence = persistence_service or BlogDraftPersistenceService()

    def publish_to_blog(self, draft, *, author, category=None, source_url=''):
        """
        Convert ``draft`` into an unpublished Blog ``Post``.

        Always results in Draft status. Never publishes, notifies, or indexes
        beyond existing Blog draft ``save()`` behaviour.
        """
        if not isinstance(draft, EditorialDraft):
            raise EditorialDraftPublisherError(
                'draft must be an EditorialDraft instance.'
            )
        if author is None:
            raise EditorialDraftPublisherError('author is required.')

        try:
            return self._persistence.create_blog_draft(
                draft,
                author=author,
                category=category,
                source_url=source_url,
            )
        except BlogDraftPersistenceError as exc:
            raise EditorialDraftPublisherError(str(exc)) from exc
