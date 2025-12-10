from allauth.account.forms import SignupForm
from captcha.fields import CaptchaField


class CaptchaSignupForm(SignupForm):
    """
    Custom signup form that adds a CAPTCHA to reduce bot signups.
    """

    captcha = CaptchaField()

    def save(self, request):
        user = super().save(request)
        return user

