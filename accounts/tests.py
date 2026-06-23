from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from allauth.account.models import EmailAddress

from accounts.forms import PeyvandResetPasswordForm


@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="optional",
    ACCOUNT_PREVENT_ENUMERATION=True,
    DEFAULT_FROM_EMAIL="noreply@test.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SITE_ID=1,
)
class PeyvandResetPasswordFormTests(TestCase):
    def setUp(self):
        from django.contrib.sites.models import Site

        Site.objects.update_or_create(
            id=1,
            defaults={"domain": "testserver", "name": "Peyvand"},
        )
        self.factory = RequestFactory()
        self.client = Client()
        self.reset_url = reverse("account_reset_password")
        self.done_url = reverse("account_reset_password_done")

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="resetuser",
            email="existing@test.com",
            password="password123",
        )
        EmailAddress.objects.create(
            user=self.user,
            email="existing@test.com",
            verified=True,
            primary=True,
        )

    def _post_password_reset(self, email):
        return self.client.post(self.reset_url, {"email": email})

    def test_existing_user_sends_password_reset_email(self):
        response = self._post_password_reset("existing@test.com")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.done_url)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("existing@test.com", mail.outbox[0].to)
        self.assertIn("password reset", mail.outbox[0].body.lower())

    def test_unknown_email_sends_no_email(self):
        response = self._post_password_reset("unknown@test.com")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.done_url)
        self.assertEqual(len(mail.outbox), 0)

    def test_both_cases_redirect_to_same_success_page(self):
        existing_response = self._post_password_reset("existing@test.com")
        mail.outbox.clear()
        unknown_response = self._post_password_reset("unknown@test.com")

        self.assertEqual(existing_response.status_code, 302)
        self.assertEqual(unknown_response.status_code, 302)
        self.assertEqual(existing_response["Location"], self.done_url)
        self.assertEqual(unknown_response["Location"], self.done_url)

    def test_unknown_email_shows_no_validation_error(self):
        response = self.client.get(self.reset_url)
        csrf_token = response.context["csrf_token"]

        response = self.client.post(
            self.reset_url,
            {"email": "unknown@test.com", "csrfmiddlewaretoken": csrf_token},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.done_url)

    def test_form_save_skips_unknown_account_mail_directly(self):
        request = self.factory.post(self.reset_url)
        form = PeyvandResetPasswordForm(data={"email": "unknown@test.com"})
        self.assertTrue(form.is_valid())

        form.save(request)

        self.assertEqual(len(mail.outbox), 0)
