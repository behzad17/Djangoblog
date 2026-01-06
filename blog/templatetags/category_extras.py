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
    # Mental health - heart with pulse (health/wellness icon)
    'slmt-ron-dr-mhgrt': 'bi bi-heart-pulse',
    'platform-updates': 'bi bi-newspaper',
    'public-services': 'bi bi-compass',
    'law-integration': 'bi bi-shield-check',
    'life-in-social': 'bi bi-people',
    'guide-questions': 'bi bi-question-circle',
    'personalities': 'bi bi-person-badge',
}

# Color mapping: slug (lowercase) -> {bg: hex, accent: hex}
# Distinct palette with soft pastel backgrounds and stronger accent colors
CATEGORY_COLOR_MAP = {
    'skills-learning': {'bg': '#DDEEFF', 'accent': '#2F80ED'},
    'careers-economy': {'bg': '#DDF7E8', 'accent': '#27AE60'},
    'stories-experiences': {'bg': '#FFE9D6', 'accent': '#F2994A'},
    'photo-gallery': {'bg': '#E9E1FF', 'accent': '#8E44AD'},
    'events-announcements': {'bg': '#FFE2DD', 'accent': '#EB5757'},
    'zbn-o-rtbt': {'bg': '#D9FBFF', 'accent': '#00A3C4'},
    'slmt-ron-dr-mhgrt': {'bg': '#E6E0FF', 'accent': '#6C5CE7'},
    'platform-updates': {'bg': '#E6ECF2', 'accent': '#34495E'},
    'public-services': {'bg': '#DDF3F7', 'accent': '#0E7490'},
    'law-integration': {'bg': '#DDE4FF', 'accent': '#1D4ED8'},
    'life-in-social': {'bg': '#DFF7E3', 'accent': '#16A34A'},
    'guide-questions': {'bg': '#FFF2C9', 'accent': '#F59E0B'},
    'personalities': {'bg': '#FFE0F0', 'accent': '#D63384'},
}

# Fallbacks
ICON_FALLBACK = 'bi bi-grid-3x3-gap'
BG_FALLBACK = '#EEF2F7'
ACCENT_FALLBACK = '#64748B'


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
    Get background color hex code for a category based on its slug.
    Case-insensitive lookup with fallback.
    
    DEPRECATED: Use category_bg instead.
    Kept for backward compatibility.
    
    Usage: {{ category|category_color }}
    Returns: Hex color string (e.g., "#DDEEFF")
    """
    return category_bg(category)


@register.filter
def category_bg(category):
    """
    Get background color hex code for a category based on its slug.
    Case-insensitive lookup with fallback.
    
    Usage: {{ category|category_bg }}
    Returns: Hex color string (e.g., "#DDEEFF")
    """
    if not category or not hasattr(category, 'slug'):
        return BG_FALLBACK
    
    slug = str(category.slug).lower().strip()
    color_data = CATEGORY_COLOR_MAP.get(slug, {})
    if isinstance(color_data, dict):
        return color_data.get('bg', BG_FALLBACK)
    return BG_FALLBACK


@register.filter
def category_accent(category):
    """
    Get accent color hex code for a category based on its slug.
    Case-insensitive lookup with fallback.
    
    Usage: {{ category|category_accent }}
    Returns: Hex color string (e.g., "#2F80ED")
    """
    if not category or not hasattr(category, 'slug'):
        return ACCENT_FALLBACK
    
    slug = str(category.slug).lower().strip()
    color_data = CATEGORY_COLOR_MAP.get(slug, {})
    if isinstance(color_data, dict):
        return color_data.get('accent', ACCENT_FALLBACK)
    return ACCENT_FALLBACK


@register.filter
def category_color_index(category):
    """
    Generate a deterministic color index (0-11) for a category slug.
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

