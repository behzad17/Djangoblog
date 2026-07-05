from django import template

register = template.Library()


@register.filter
def link_type_label(link):
    """Return the resource type label for display in list rows."""
    if link.resource_type_id:
        return link.resource_type.name_fa
    return ''


@register.filter
def category_hero_subtitle(category):
    """Return hero subtitle from admin description or a generic fallback."""
    description = (category.description or '').strip()
    if description:
        return description
    return f'منابع و لینک\u200cهای مفید مرتبط با {category.name_fa} در سوئد.'
