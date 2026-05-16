"""
HTML + plain-text email builder for admin bulk user messages.
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_admin_bulk_email(subject, message, recipient_email):
    """
    Send one admin bulk message as multipart (plain + RTL HTML).

    ``message`` is plain text from the admin compose form; templates handle
    line breaks and escaping for the HTML part.
    """
    context = {
        'subject': subject,
        'message': message,
        'site_name': 'پیوند | Peyvand',
    }
    text_content = render_to_string('emails/admin_bulk_message.txt', context)
    html_content = render_to_string('emails/admin_bulk_message.html', context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.attach_alternative(html_content, 'text/html')
    email.send()
