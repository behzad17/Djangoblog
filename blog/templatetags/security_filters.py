from django import template
from blog.utils import sanitize_html

register = template.Library()


@register.filter(name='sanitize')
def sanitize_filter(value):
    """
    Template filter to sanitize HTML content.
    Use this instead of |safe for user-generated content.
    """
    if not value:
        return ''
    return sanitize_html(value)

