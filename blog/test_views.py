from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from .forms import CommentForm
from .models import Category, Comment, Post, UserProfile

class TestBlogViews(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="myUsername",
            password="myPassword",
            email="test@test.com"
        )
        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={"is_site_verified": True},
        )
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.post = Post(
            title="Blog title",
            author=self.user,
            slug="blog-title",
            excerpt="Blog excerpt",
            content="Blog content",
            status=1,
            category=self.category,
        )
        self.post.save()

    def test_render_post_detail_page_with_comment_form(self):
        response = self.client.get(reverse(
            'post_detail', args=['blog-title']))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Blog title", response.content)
        self.assertIn(b"Blog content", response.content)
        self.assertIsInstance(
            response.context['comment_form'], CommentForm)
        self.assertEqual(response.context['related_useful_links'], [])

    def test_successful_comment_submission(self):
        """Test for posting a comment on a post"""
        self.client.login(
            username="myUsername", password="myPassword")
        post_data = {
            'body': 'This is a test comment.'
        }
        response = self.client.post(
            reverse('post_detail', args=['blog-title']),
            post_data,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        comment = Comment.objects.get(post=self.post, author=self.user)
        self.assertIn('This is a test comment.', comment.body)
        self.assertFalse(comment.approved)
        self.assertContains(
            response,
            'نظر شما ثبت شد و در انتظار بررسی است.',
        )


class PostDetailRelatedContentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        import cloudinary

        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )
        cls.author = User.objects.create_user(
            username='blogrelatedauthor',
            password='password123',
        )
        cls.mapped_category, _ = Category.objects.get_or_create(
            slug='law-integration',
            defaults={'name': 'قانون و ادغام'},
        )
        cls.post = Post.objects.create(
            title='سؤال درباره مهاجرت',
            slug='blog-related-post',
            author=cls.author,
            category=cls.mapped_category,
            content='به دنبال مشاور مهاجرت هستم.',
            status=1,
        )

    def _create_useful_link(self, slug, **kwargs):
        from related_links.models import (
            RelatedLink,
            UsefulLinkCategory,
            UsefulLinkResourceType,
        )

        category = kwargs.pop('category', None) or UsefulLinkCategory.objects.create(
            name_en='Migration',
            name_fa='مهاجرت',
            slug=f'migration-{slug}',
            icon='bi-globe',
            is_active=True,
        )
        resource_type = kwargs.pop('resource_type', None) or UsefulLinkResourceType.objects.create(
            name_en='Website',
            name_fa='وب‌سایت',
            slug=f'website-{slug}',
            icon='bi-globe',
            is_active=True,
        )
        defaults = {
            'title': f'لینک {slug}',
            'slug': slug,
            'category': category,
            'resource_type': resource_type,
            'url': 'https://example.com',
            'short_description': 'راهنمای مهاجرت',
            'is_active': True,
        }
        defaults.update(kwargs)
        return RelatedLink.objects.create(**defaults)

    def _section_index(self, response, marker):
        return response.content.index(marker.encode())

    def test_post_detail_renders_no_related_sections(self):
        response = self.client.get(
            reverse('post_detail', args=[self.post.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'آگهی‌های مرتبط')
        self.assertNotContains(response, 'متخصصان مرتبط')
        self.assertNotContains(response, 'لینک‌های مفید مرتبط')

    def test_post_detail_does_not_render_related_ads(self):
        from ads.models import Ad, AdCategory

        ad_category = AdCategory.objects.create(
            name='خدمات حقوقی',
            slug='legal-financial',
        )
        Ad.objects.create(
            title='مشاور حقوقی',
            slug='blog-related-ad',
            category=ad_category,
            owner=self.author,
            image='test/ad-image',
            target_url='https://example.com',
            city='Stockholm',
            plan='pro',
            is_active=True,
            is_approved=True,
            url_approved=True,
        )

        response = self.client.get(
            reverse('post_detail', args=[self.post.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'آگهی‌های مرتبط')

    def test_post_detail_does_not_render_related_experts(self):
        from askme.models import Moderator

        expert_user = User.objects.create_user(
            username='blogrelatedexpert',
            password='password123',
        )
        Moderator.objects.create(
            user=expert_user,
            expert_title='وکیل مهاجرت',
            complete_name='متخصص حقوقی',
            field_specialty='مهاجرت و اقامت',
            slug='blog-related-expert',
            profile_image='test/expert-image',
            is_active=True,
        )

        response = self.client.get(
            reverse('post_detail', args=[self.post.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'متخصصان مرتبط')

    def test_post_detail_renders_related_useful_links_only(self):
        from related_links.models import UsefulLinkCategory

        UsefulLinkCategory.objects.filter(slug='migration').delete()
        migration_category = UsefulLinkCategory.objects.create(
            name_en='Migration',
            name_fa='مهاجرت',
            slug='migration',
            icon='bi-globe',
            is_active=True,
        )
        self._create_useful_link(
            'blog-related-link',
            category=migration_category,
            title='راهنمای مهاجرت',
        )

        response = self.client.get(
            reverse('post_detail', args=[self.post.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'آگهی‌های مرتبط')
        self.assertNotContains(response, 'متخصصان مرتبط')
        self.assertContains(response, 'لینک‌های مفید مرتبط')
        self.assertEqual(len(response.context['related_useful_links']), 1)

    def test_post_detail_section_order(self):
        from ads.models import Ad, AdCategory
        from askme.models import Moderator
        from related_links.models import UsefulLinkCategory

        Post.objects.create(
            title='پست مرتبط دیگر',
            slug='blog-related-post-2',
            author=self.author,
            category=self.mapped_category,
            content='محتوای پست مرتبط.',
            status=1,
        )
        UsefulLinkCategory.objects.filter(slug='migration').delete()
        migration_category = UsefulLinkCategory.objects.create(
            name_en='Migration',
            name_fa='مهاجرت',
            slug='migration',
            icon='bi-globe',
            is_active=True,
        )
        self._create_useful_link(
            'blog-related-link-order',
            category=migration_category,
            title='راهنمای مهاجرت',
        )
        ad_category = AdCategory.objects.create(
            name='خدمات حقوقی',
            slug='legal-financial-order',
        )
        Ad.objects.create(
            title='مشاور حقوقی',
            slug='blog-related-ad-order',
            category=ad_category,
            owner=self.author,
            image='test/ad-image',
            target_url='https://example.com',
            city='Stockholm',
            plan='pro',
            is_active=True,
            is_approved=True,
            url_approved=True,
        )
        expert_user = User.objects.create_user(
            username='blogrelatedexpertorder',
            password='password123',
        )
        Moderator.objects.create(
            user=expert_user,
            expert_title='وکیل مهاجرت',
            complete_name='متخصص حقوقی',
            field_specialty='مهاجرت و اقامت',
            slug='blog-related-expert-order',
            profile_image='test/expert-image',
            is_active=True,
        )

        response = self.client.get(
            reverse('post_detail', args=[self.post.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'آگهی‌های مرتبط')
        self.assertNotContains(response, 'متخصصان مرتبط')

        body_index = self._section_index(response, 'به دنبال مشاور مهاجرت هستم.')
        comments_index = self._section_index(response, 'نظرات')
        related_posts_index = self._section_index(response, 'پست\u200cهای مرتبط')
        useful_links_index = self._section_index(response, 'لینک\u200cهای مفید مرتبط')

        self.assertLess(body_index, comments_index)
        self.assertLess(comments_index, related_posts_index)
        self.assertLess(related_posts_index, useful_links_index)
