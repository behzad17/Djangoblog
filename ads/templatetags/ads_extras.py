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
    try:
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
        category_str = str(category_name).strip()
        return icon_map.get(category_str, "fas fa-tag")
    except Exception:
        return "fas fa-tag"


