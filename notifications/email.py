"""
Peyvand transactional email helpers for the notifications app.
"""
import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def build_site_url(path: str = '') -> str:
    """Build an absolute site URL for links in emails."""
    path = path or '/'
    if not path.startswith('/'):
        path = f'/{path}'

    try:
        site = Site.objects.get_current()
        site_domain = site.domain
        if not site_domain.startswith('http'):
            protocol = 'https' if not settings.DEBUG else 'http'
            site_url = f'{protocol}://{site_domain}'
        else:
            site_url = site_domain.rstrip('/')
        return f'{site_url}{path}'
    except Exception:
        logger.warning('Could not resolve Site for email URL building', exc_info=True)
        return path


def get_user_display_name(user) -> str:
    if not user:
        return 'کاربر گرامی'
    full_name = user.get_full_name().strip()
    if full_name:
        return full_name
    return user.username or 'کاربر گرامی'


def send_peyvand_email(
    *,
    to: str,
    subject: str,
    template_base: str,
    context: dict | None = None,
) -> bool:
    """
    Send a branded multipart Peyvand email.

    ``template_base`` maps to templates/emails/{template_base}.html and .txt.
    """
    if not to:
        logger.warning('Skipping email send: empty recipient')
        return False

    email_context = {
        'site_name': 'پیوند | Peyvand',
        'site_url': build_site_url('/'),
        'home_url': build_site_url('/'),
        **(context or {}),
    }

    text_content = render_to_string(f'emails/{template_base}.txt', email_context)
    html_content = render_to_string(f'emails/{template_base}.html', email_context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    email.attach_alternative(html_content, 'text/html')
    email.send()
    return True
