from django import template

register = template.Library()


@register.filter
def category_color_index(category):
    """
    Generate a deterministic color index (0-11) for a category based on its slug.
    This ensures each category always gets the same color.
    
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

