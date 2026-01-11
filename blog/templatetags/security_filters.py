from django import template
from django.utils.safestring import mark_safe
from blog.utils import sanitize_html

register = template.Library()


@register.filter(name='sanitize')
def sanitize_filter(value):
    """
    Template filter to sanitize HTML content.
    Use this instead of |safe for user-generated content.
    Returns safe HTML that has been sanitized to prevent XSS attacks.
    """
    if not value:
        return ''
    # Sanitize the HTML (removes dangerous tags/attributes)
    cleaned = sanitize_html(value)
    # Mark as safe so Django doesn't escape it again
    # This is safe because bleach.clean() has already removed dangerous content
    return mark_safe(cleaned)

