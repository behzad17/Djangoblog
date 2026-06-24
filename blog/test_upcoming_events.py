from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Category, Post
from blog.utils import get_upcoming_events


class GetUpcomingEventsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="eventauthor",
            password="password123",
            email="author@test.com",
        )
        self.events_category = Category.objects.create(
            name="Events",
            slug="events-announcements",
        )
        self.other_category = Category.objects.create(
            name="Other",
            slug="other-category",
        )
        self.today = timezone.localdate()

    def _create_event(self, title, start_offset_days, slug, category=None):
        return Post.objects.create(
            title=title,
            slug=slug,
            author=self.user,
            content="Event content",
            status=1,
            category=category or self.events_category,
            event_start_date=self.today + timedelta(days=start_offset_days),
            event_location="Stockholm",
        )

    def test_returns_future_events_ordered_by_start_date(self):
        later = self._create_event("Later Event", 10, "later-event")
        sooner = self._create_event("Sooner Event", 2, "sooner-event")
        today_event = self._create_event("Today Event", 0, "today-event")

        results = get_upcoming_events()

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].pk, today_event.pk)
        self.assertEqual(results[1].pk, sooner.pk)
        self.assertEqual(results[2].pk, later.pk)

    def test_excludes_past_events_and_non_event_category(self):
        self._create_event("Past Event", -3, "past-event")
        Post.objects.create(
            title="Wrong Category",
            slug="wrong-category",
            author=self.user,
            content="Content",
            status=1,
            category=self.other_category,
            event_start_date=self.today + timedelta(days=3),
        )

        self.assertEqual(get_upcoming_events(), [])

    def test_limits_to_five_events(self):
        for index in range(7):
            self._create_event(
                f"Event {index}",
                index + 1,
                f"event-{index}",
            )

        self.assertEqual(len(get_upcoming_events()), 5)


class UpcomingEventsHomepageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="homepageauthor",
            password="password123",
        )
        self.events_category = Category.objects.create(
            name="Events",
            slug="events-announcements",
        )
        Post.objects.create(
            title="جشن تابستانی ایرانیان",
            slug="summer-party",
            author=self.user,
            content="Event content",
            status=1,
            category=self.events_category,
            event_start_date=timezone.localdate() + timedelta(days=5),
            event_location="Göteborg",
        )

    def test_homepage_renders_upcoming_events_section(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "رویدادهای پیش رو")
        self.assertContains(response, "مشاهده همه رویدادها")
        self.assertContains(response, "جشن تابستانی ایرانیان")
        self.assertContains(response, "Göteborg")

    def test_homepage_hides_section_when_no_upcoming_events(self):
        Post.objects.all().delete()

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "رویدادهای پیش رو")
