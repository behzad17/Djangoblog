from django import template

register = template.Library()

LINK_TYPE_LABELS = {
    'podcast': 'پادکست',
    'video': 'فیلم / ویدئو',
    'radio': 'رادیو',
    'website': 'وب\u200cسایت',
    'file': 'فایل آموزشی',
    'social': 'شبکه\u200cهای اجتماعی',
}


@register.filter
def link_type_label(link):
    """Return a clean type label without emoji."""
    return LINK_TYPE_LABELS.get(link.link_type, link.get_link_type_display())


@register.filter
def category_hero_subtitle(category):
    """Return hero subtitle from admin description or a generic fallback."""
    description = (category.description or '').strip()
    if description:
        return description
    return f'منابع و لینک\u200cهای مفید مرتبط با {category.name_fa} در سوئد.'
