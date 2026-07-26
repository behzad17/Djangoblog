import re

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

    def test_duplicate_titles_allowed_slugs_stay_unique(self):
        existing = Post.objects.create(
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
        self.assertNotEqual(post.pk, existing.pk)
        self.assertEqual(post.title, 'AI Housing Draft')
        self.assertEqual(existing.title, 'AI Housing Draft')
        self.assertNotEqual(post.slug, existing.slug)
        self.assertFalse(re.search(r'\(\d{14}', post.title))

    def test_save_draft_title_matches_workspace_exactly(self):
        persian = 'نگاهی جامع به قانون اساسی...'
        draft = EditorialDraft(
            title=persian,
            body='بدنه',
            summary='خلاصه',
            language='fa',
        )
        post = self.service.create_blog_draft(
            draft,
            author=self.author,
            category=self.category,
        )
        self.assertEqual(post.title, persian)
        self.assertFalse(re.search(r'\(\d{14}', post.title))

        # Same title on a second draft is allowed; title stays exact.
        again = self.service.create_blog_draft(
            draft,
            author=self.author,
            category=self.category,
        )
        self.assertEqual(again.title, persian)
        self.assertNotEqual(again.slug, post.slug)
        self.assertEqual(Post.objects.filter(title=persian).count(), 2)

    def test_legacy_timestamp_suffix_stripped_on_update(self):
        stamped = Post.objects.create(
            title='نگاهی جامع به قانون اساسی... (20260726184315)',
            slug='legacy-stamped-title',
            author=self.author,
            category=self.category,
            content='old',
            status=0,
        )
        draft = EditorialDraft(
            title='نگاهی جامع به قانون اساسی...',
            body='بدنه جدید',
            summary='خلاصه',
            language='fa',
        )
        result = self.service.update_blog_draft(stamped, draft)
        self.assertEqual(result.title, 'نگاهی جامع به قانون اساسی...')
        self.assertNotIn('20260726184315', result.title)

    def test_requires_author_and_category(self):
        with self.assertRaises(BlogDraftPersistenceError):
            self.service.create_blog_draft(
                self.draft,
                author=None,
                category=self.category,
            )
        # Empty category falls back to default News category.
        post = self.service.create_blog_draft(
            self.draft,
            author=self.author,
            category=None,
        )
        self.assertEqual(post.status, 0)
        self.assertIsNotNone(post.category_id)

    def test_update_blog_draft_preserves_id(self):
        post = self.service.create_blog_draft(
            self.draft,
            author=self.author,
            category=self.category,
        )
        updated_draft = EditorialDraft(
            title='AI Housing Draft Updated',
            lead='Lead paragraph',
            body='Updated body',
            summary='Updated summary',
            language='sv',
        )
        result = self.service.update_blog_draft(
            post,
            updated_draft,
            category=self.category,
            source_url='https://example.se/source',
        )
        self.assertEqual(result.pk, post.pk)
        self.assertEqual(Post.objects.filter(title__startswith='AI Housing Draft').count(), 1)
        result.refresh_from_db()
        self.assertEqual(result.title, 'AI Housing Draft Updated')
        self.assertIn('Lead paragraph', result.content)
        self.assertIn('Updated body', result.content)
        self.assertEqual(result.excerpt, 'Updated summary')
        self.assertEqual(result.status, 0)
        self.assertEqual(result.external_url, 'https://example.se/source')

    def test_update_rejects_published_post(self):
        post = self.service.create_blog_draft(
            self.draft,
            author=self.author,
            category=self.category,
        )
        post.status = 1
        post.save(update_fields=['status'])
        with self.assertRaises(BlogDraftPersistenceError):
            self.service.update_blog_draft(post, self.draft)
