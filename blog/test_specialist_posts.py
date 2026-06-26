from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Category, Post, UserProfile
from blog.utils import EVENTS_CATEGORY_SLUG, get_specialist_posts_queryset


class SpecialistPostsQueryTests(TestCase):
    def setUp(self):
        self.moderator = User.objects.create_user(
            username="moderator",
            password="password123",
            email="mod@test.com",
        )
        UserProfile.objects.update_or_create(
            user=self.moderator,
            defaults={"can_publish_without_approval": True},
        )
        self.events_category = Category.objects.create(
            name="Events",
            slug=EVENTS_CATEGORY_SLUG,
        )
        self.article_category = Category.objects.create(
            name="Legal",
            slug="legal-financial",
        )
        self.today = timezone.localdate()

    def test_excludes_event_posts_by_moderator(self):
        Post.objects.create(
            title="Moderator Event",
            slug="moderator-event",
            author=self.moderator,
            content="Event content",
            status=1,
            category=self.events_category,
            event_start_date=self.today + timedelta(days=3),
            event_location="Stockholm",
        )

        slugs = list(get_specialist_posts_queryset().values_list("slug", flat=True))

        self.assertNotIn("moderator-event", slugs)

    def test_includes_normal_moderator_articles(self):
        Post.objects.create(
            title="Moderator Article",
            slug="moderator-article",
            author=self.moderator,
            content="Article content",
            status=1,
            category=self.article_category,
        )

        slugs = list(get_specialist_posts_queryset().values_list("slug", flat=True))

        self.assertEqual(slugs, ["moderator-article"])


class SpecialistPostsHomepageTests(TestCase):
    def setUp(self):
        import cloudinary

        cloudinary.config(
            cloud_name="test",
            api_key="test",
            api_secret="test",
            secure=True,
        )

        self.moderator = User.objects.create_user(
            username="homepage-mod",
            password="password123",
        )
        UserProfile.objects.update_or_create(
            user=self.moderator,
            defaults={"can_publish_without_approval": True},
        )
        self.events_category = Category.objects.create(
            name="Events",
            slug=EVENTS_CATEGORY_SLUG,
        )
        self.article_category = Category.objects.create(
            name="Legal",
            slug="legal-financial",
        )

    def test_homepage_shows_article_not_event_in_specialist_section(self):
        Post.objects.create(
            title="رویداد مدیر",
            slug="mod-event",
            author=self.moderator,
            content="Event content",
            status=1,
            category=self.events_category,
            event_start_date=timezone.localdate() + timedelta(days=4),
            event_location="Malmö",
        )
        Post.objects.create(
            title="مقاله تخصصی مدیر",
            slug="mod-article",
            author=self.moderator,
            content="Article content",
            status=1,
            category=self.article_category,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "مطالب تخصصی")
        self.assertContains(response, "مقاله تخصصی مدیر")
        self.assertContains(response, "رویدادهای پیش رو")
        self.assertContains(response, "رویداد مدیر")

        specialist_html = response.content.decode("utf-8").split("مطالب تخصصی", 1)[1]
        self.assertIn("مقاله تخصصی مدیر", specialist_html)
        self.assertNotIn("رویداد مدیر", specialist_html.split("رویدادهای پیش رو")[0])
