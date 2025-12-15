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


