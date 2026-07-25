from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from blog.models import Category, Post
from content_ai.editorial import (
    BlogDraftPersistenceError,
    BlogDraftPersistenceService,
    EditorialDraft,
)
from content_ai.telemetry import AIExecutionTelemetry

User = get_user_model()


@override_settings(ADMIN_NOTIFICATION_ENABLED=False)
class BlogDraftPersistenceServiceTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='aidraftauthor',
            password='password123',
        )
        self.category = Category.objects.create(
            name='AI Draft Category',
            slug='ai-draft-category',
        )
        self.service = BlogDraftPersistenceService()
        self.draft = EditorialDraft(
            title='AI Housing Draft',
            body='Generated body content for the blog draft.',
            summary='Short summary',
            language='sv',
            metadata={
                'provider': 'mock',
                'success': True,
                'task': 'post_generation',
            },
            telemetry=AIExecutionTelemetry(
                provider='mock',
                model='mock',
                success=True,
                duration_ms=1.0,
            ),
        )

    def test_create_blog_draft_success(self):
        post = self.service.create_blog_draft(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertIsInstance(post, Post)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())
        self.assertEqual(post.title, 'AI Housing Draft')
        self.assertEqual(post.content, self.draft.body)
        self.assertEqual(post.excerpt, self.draft.summary)
        self.assertTrue(post.slug)

    def test_draft_status_only(self):
        post = self.service.create_blog_draft(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertEqual(post.status, 0)
        self.assertNotEqual(post.status, 1)
        self.assertFalse(post.is_deleted)

    def test_correct_author_and_category(self):
        post = self.service.create_blog_draft(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertEqual(post.author_id, self.author.id)
        self.assertEqual(post.category_id, self.category.id)

    def test_metadata_mapping_uses_existing_fields_only(self):
        """
        Blog Post has no language/metadata columns; summary maps to excerpt,
        body to content, title to title. AI metadata stays on EditorialDraft.
        """
        post = self.service.create_blog_draft(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertEqual(post.excerpt, 'Short summary')
        self.assertEqual(post.content, self.draft.body)
        self.assertFalse(hasattr(post, 'language'))
        self.assertEqual(self.draft.language, 'sv')
        self.assertEqual(self.draft.metadata.get('provider'), 'mock')

    def test_unique_title_collision_gets_suffix(self):
        Post.objects.create(
            title='AI Housing Draft',
            slug='existing-ai-housing-draft',
            author=self.author,
            category=self.category,
            content='existing',
            status=0,
        )
        post = self.service.create_blog_draft(
            self.draft,
            author=self.author,
            category=self.category,
        )
        self.assertNotEqual(post.title, 'AI Housing Draft')
        self.assertTrue(post.title.startswith('AI Housing Draft'))
        self.assertEqual(post.status, 0)

    def test_requires_author_and_category(self):
        with self.assertRaises(BlogDraftPersistenceError):
            self.service.create_blog_draft(
                self.draft,
                author=None,
                category=self.category,
            )
        with self.assertRaises(BlogDraftPersistenceError):
            self.service.create_blog_draft(
                self.draft,
                author=self.author,
                category=None,
            )
