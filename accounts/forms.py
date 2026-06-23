from allauth.account.forms import ResetPasswordForm, SignupForm
from captcha.fields import CaptchaField


class CaptchaSignupForm(SignupForm):
    """
    Custom signup form that adds a CAPTCHA to reduce bot signups.
    """

    captcha = CaptchaField()

    def save(self, request):
        user = super().save(request)
        return user


class PeyvandResetPasswordForm(ResetPasswordForm):
    """
    Password reset form that suppresses emails for unknown addresses while
    preserving enumeration-safe UX (same success redirect either way).
    """

    def save(self, request, **kwargs):
        email = self.cleaned_data["email"]
        if self.users:
            self._send_password_reset_mail(
                request, email, self.users, **kwargs
            )
        return email
