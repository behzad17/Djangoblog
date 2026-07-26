from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from unittest.mock import MagicMock

from blog.models import Category, Post
from content_ai.editorial import EditorialDraft
from content_ai.editorial.persistence import BlogDraftPersistenceError
from content_ai.editorial.publisher import (
    EditorialDraftPublisher,
    EditorialDraftPublisherError,
)
from content_ai.telemetry import AIExecutionTelemetry

User = get_user_model()


@override_settings(ADMIN_NOTIFICATION_ENABLED=False)
class EditorialDraftPublisherTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='aipublisherauthor',
            password='password123',
        )
        self.category = Category.objects.create(
            name='Publisher Category',
            slug='publisher-category',
        )
        self.publisher = EditorialDraftPublisher()
        self.draft = EditorialDraft(
            title='Publisher Housing Draft',
            body='Publisher body content for the blog draft.',
            summary='Publisher summary',
            language='fa',
            metadata={
                'provider': 'mock',
                'success': True,
                'task': 'post_generation',
            },
            telemetry=AIExecutionTelemetry(
                provider='mock',
                model='mock',
                success=True,
                duration_ms=2.0,
            ),
        )

    def test_publish_to_blog_creates_draft(self):
        post = self.publisher.publish_to_blog(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertIsInstance(post, Post)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())
        self.assertEqual(post.title, 'Publisher Housing Draft')
        self.assertEqual(post.content, self.draft.body)
        self.assertEqual(post.excerpt, self.draft.summary)
        self.assertTrue(post.slug)

    def test_draft_status_only(self):
        post = self.publisher.publish_to_blog(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertEqual(post.status, 0)
        self.assertNotEqual(post.status, 1)
        self.assertFalse(post.is_deleted)

    def test_author_and_category_mapping(self):
        post = self.publisher.publish_to_blog(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertEqual(post.author_id, self.author.id)
        self.assertEqual(post.category_id, self.category.id)

    def test_metadata_mapping(self):
        """
        Summary → excerpt, body → content. Language/AI metadata stay on the
        EditorialDraft because Blog Post has no matching columns.
        """
        post = self.publisher.publish_to_blog(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertEqual(post.excerpt, 'Publisher summary')
        self.assertEqual(post.content, self.draft.body)
        self.assertFalse(hasattr(post, 'language'))
        self.assertEqual(self.draft.language, 'fa')
        self.assertEqual(self.draft.metadata.get('provider'), 'mock')

    def test_requires_author(self):
        with self.assertRaises(EditorialDraftPublisherError):
            self.publisher.publish_to_blog(
                self.draft,
                author=None,
                category=self.category,
            )

    def test_rejects_non_editorial_draft(self):
        with self.assertRaises(EditorialDraftPublisherError):
            self.publisher.publish_to_blog(
                {'title': 'not a draft'},
                author=self.author,
                category=self.category,
            )

    def test_wraps_persistence_errors(self):
        persistence = MagicMock()
        persistence.create_blog_draft.side_effect = BlogDraftPersistenceError(
            'persistence failed'
        )
        publisher = EditorialDraftPublisher(persistence_service=persistence)
        with self.assertRaises(EditorialDraftPublisherError) as ctx:
            publisher.publish_to_blog(
                self.draft,
                author=self.author,
                category=self.category,
            )
        self.assertIn('persistence failed', str(ctx.exception))

    def test_delegates_to_persistence_service(self):
        expected = MagicMock(spec=Post)
        persistence = MagicMock()
        persistence.create_blog_draft.return_value = expected
        publisher = EditorialDraftPublisher(persistence_service=persistence)

        result = publisher.publish_to_blog(
            self.draft,
            author=self.author,
            category=self.category,
            source_url='https://example.se/a',
        )

        self.assertIs(result, expected)
        persistence.create_blog_draft.assert_called_once_with(
            self.draft,
            author=self.author,
            category=self.category,
            source_url='https://example.se/a',
        )
