from django import template

register = template.Library()


# Icon mapping: slug (lowercase) -> Bootstrap Icons class
CATEGORY_ICON_MAP = {
    'skills-learning': 'bi bi-mortarboard',
    'careers-economy': 'bi bi-briefcase',
    'stories-experiences': 'bi bi-journal-text',
    'photo-gallery': 'bi bi-images',
    'events-announcements': 'bi bi-calendar-event',
    'zbn-o-rtbt': 'bi bi-chat-dots',
    'slmt-ron-dr-mhgrt': 'bi bi-people-heart',
    'platform-updates': 'bi bi-newspaper',
    'public-services': 'bi bi-compass',
    'law-integration': 'bi bi-shield-check',
    'life-in-social': 'bi bi-people',
    'guide-questions': 'bi bi-question-circle',
    'personalities': 'bi bi-person-badge',
}

# Color mapping: slug (lowercase) -> hex pastel color
CATEGORY_COLOR_MAP = {
    'skills-learning': '#E8F3FF',
    'careers-economy': '#EAF7F1',
    'stories-experiences': '#FFF4E8',
    'photo-gallery': '#F3EEFF',
    'events-announcements': '#FFF0E1',
    'zbn-o-rtbt': '#E9F7FA',
    'slmt-ron-dr-mhgrt': '#EFEAFF',
    'platform-updates': '#F1F3F5',
    'public-services': '#EEF7FA',
    'law-integration': '#EAF0FF',
    'life-in-social': '#ECF8F1',
    'guide-questions': '#FFF9E6',
    'personalities': '#FCEEF3',
}

# Fallbacks
ICON_FALLBACK = 'bi bi-grid-3x3-gap'
COLOR_FALLBACK = '#F5F7FA'


@register.filter
def category_icon(category):
    """
    Get Bootstrap Icons class for a category based on its slug.
    Case-insensitive lookup with fallback.
    
    Usage: {{ category|category_icon }}
    Returns: Bootstrap Icons class string (e.g., "bi bi-mortarboard")
    """
    if not category or not hasattr(category, 'slug'):
        return ICON_FALLBACK
    
    slug = str(category.slug).lower().strip()
    return CATEGORY_ICON_MAP.get(slug, ICON_FALLBACK)


@register.filter
def category_color(category):
    """
    Get pastel color hex code for a category based on its slug.
    Case-insensitive lookup with fallback.
    
    Usage: {{ category|category_color }}
    Returns: Hex color string (e.g., "#E8F3FF")
    """
    if not category or not hasattr(category, 'slug'):
        return COLOR_FALLBACK
    
    slug = str(category.slug).lower().strip()
    return CATEGORY_COLOR_MAP.get(slug, COLOR_FALLBACK)


@register.filter
def category_color_index(category):
    """
    Generate a deterministic color index (0-11) for a category based on its slug.
    This ensures each category always gets the same color.
    
    DEPRECATED: Use category_color instead for semantic colors.
    Kept for backward compatibility.
    
    Usage: {{ category|category_color_index }}
    """
    if not category or not hasattr(category, 'slug'):
        return 0
    
    # Simple hash: sum of character codes in slug, then modulo 12
    slug = str(category.slug)
    hash_value = sum(ord(c) for c in slug)
    
    # Add category ID if available for more uniqueness
    if hasattr(category, 'id'):
        hash_value += category.id
    
    return hash_value % 12

