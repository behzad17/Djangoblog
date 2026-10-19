from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from ratelimit.exceptions import Ratelimited

from blog.models import UserProfile
from blog.views import create_post


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'post-creation-rate-limit-tests',
    },
})
class PostCreationRateLimitTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.form_patch = patch('blog.views.PostForm')
        self.form = self.form_patch.start()
        self.addCleanup(self.form_patch.stop)
        self.form.return_value.is_valid.return_value = False
        self.render_patch = patch(
            'blog.views.render', return_value=HttpResponse('form')
        )
        self.render_patch.start()
        self.addCleanup(self.render_patch.stop)
        self.category_patch = patch('blog.views.Category.objects.filter')
        self.category_patch.start()
        self.addCleanup(self.category_patch.stop)
        self.clock_patch = patch('ratelimit.core.time.time', return_value=1000000)
        self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)
        self.addCleanup(cache.clear)

    def user(self, username, pk=1, **kwargs):
        user = User(username=username, pk=pk, **kwargs)
        user.profile = UserProfile(user=user, is_site_verified=True)
        return user

    def request(self, user, ip='192.0.2.1', **data):
        request = self.factory.post('/create-post/', data, REMOTE_ADDR=ip)
        request.user = user
        return request

    def test_named_publishers_can_exceed_both_quotas(self):
        for username in ('BJBenny', 'admin'):
            with self.subTest(username=username):
                cache.clear()
                for _ in range(25):
                    response = create_post(self.request(self.user(username)))
                    self.assertEqual(response.status_code, 200)

    def test_other_users_remain_limited_including_staff(self):
        for staff in (False, True):
            with self.subTest(staff=staff):
                cache.clear()
                user = self.user('other-editor', is_staff=staff)
                for _ in range(5):
                    self.assertEqual(create_post(self.request(user)).status_code, 200)
                with self.assertRaises(Ratelimited):
                    create_post(self.request(user))

    def test_ip_quota_still_blocks_others_but_not_named_publishers(self):
        for pk in range(1, 21):
            user = self.user(f'reader-{pk}', pk=pk)
            self.assertEqual(create_post(self.request(user)).status_code, 200)
        with self.assertRaises(Ratelimited):
            create_post(self.request(self.user('another-reader', pk=21)))
        for pk, username in enumerate(('BJBenny', 'admin'), start=22):
            self.assertEqual(
                create_post(self.request(self.user(username, pk=pk))).status_code,
                200,
            )

    def test_posted_username_cannot_claim_exemption(self):
        user = self.user('ordinary-user')
        for _ in range(5):
            create_post(self.request(user, username='BJBenny'))
        with self.assertRaises(Ratelimited):
            create_post(self.request(user, username='admin'))

    def test_exemption_does_not_bypass_site_verification(self):
        user = self.user('BJBenny')
        user.profile.is_site_verified = False
        with patch('blog.decorators.messages.warning'):
            response = create_post(self.request(user))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/complete-setup/', response.url)
        self.form.assert_not_called()

    def test_anonymous_user_cannot_publish(self):
        response = create_post(self.request(AnonymousUser(), username='BJBenny'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.form.assert_not_called()
