from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Safely get a value from a dictionary in templates.
    Usage: {{ my_dict|get_item:some_id }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def category_icon(category_name):
    """
    Get the appropriate icon for a category name.
    Usage: {{ category.name|category_icon }}
    """
    if not category_name:
        return "fas fa-tag"
    
    icon_map = {
        "وسایل نقلیه": "fas fa-car",
        "مسکن": "fas fa-home",
        "کار و خدمات": "fas fa-briefcase",
        "اوقات فراغت": "fas fa-gamepad",
        "غذا و رستوران": "fas fa-utensils",
        "سلامت و رفاه": "fas fa-heart",
        "وسایل منزل": "fas fa-couch",
        "حقوقی و مالی": "fas fa-gavel",
    }
    return icon_map.get(str(category_name), "fas fa-tag")


