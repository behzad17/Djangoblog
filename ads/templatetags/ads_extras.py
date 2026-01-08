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


@register.filter
def category_image_path(category):
    """
    Get the full static path for a category image.
    Returns the full path (e.g., 'images/ads-categories/car-naghlie.jpg').
    Usage: {{ category|category_image_path }}
    """
    filename = category_image(category)
    if filename:
        return f'images/ads-categories/{filename}'
    return None


@register.filter
def category_image(category):
    """
    Get the image filename for a category based on slug or name.
    Returns just the filename (e.g., 'car-naghlie.jpg').
    Usage: {{ category|category_image }}
    """
    try:
        if not category:
            return None

        # Map category slug/name to image filename
        # Based on images: car-naghlie.jpg, ghaza-farhang.jpg, etc.
        image_map = {
            # By slug (English)
            'vehicles': 'car-naghlie.jpg',
            'car-naghlie': 'car-naghlie.jpg',
            'housing': 'maskan-zendegi.jpg',
            'maskan': 'maskan-zendegi.jpg',
            'maskan-zendegi': 'maskan-zendegi.jpg',
            'work-services': 'kar-herfeh.jpg',
            'work': 'kar-herfeh.jpg',
            'kar-herfeh': 'kar-herfeh.jpg',
            'leisure': 'oghate-feraghat.jpg',
            'oghate-feraghat': 'oghate-feraghat.jpg',
            'food-restaurant': 'ghaza-farhang.jpg',
            'food': 'ghaza-farhang.jpg',
            'ghaza-farhang': 'ghaza-farhang.jpg',
            'health-welfare': 'salamat-refah.jpg',
            'health': 'salamat-refah.jpg',
            'salamat-refah': 'salamat-refah.jpg',
            'home-appliances': 'khane-vasayel.jpg',
            'home-items': 'khane-vasayel.jpg',
            'khane-vasayel': 'khane-vasayel.jpg',
            'legal-financial': 'hoghooghi-mali.jpg',
            'legal': 'hoghooghi-mali.jpg',
            'hoghooghi-mali': 'hoghooghi-mali.jpg',
            # By name (Persian)
            'وسایل نقلیه': 'car-naghlie.jpg',
            'مسکن': 'maskan-zendegi.jpg',
            'کار و خدمات': 'kar-herfeh.jpg',
            'اوقات فراغت': 'oghate-feraghat.jpg',
            'غذا و رستوران': 'ghaza-farhang.jpg',
            'سلامت و رفاه': 'salamat-refah.jpg',
            'وسایل منزل': 'khane-vasayel.jpg',
            'حقوقی و مالی': 'hoghooghi-mali.jpg',
            # Additional categories (if they exist)
            'زبان و آموزش': 'zaban-amozesh.jpg',
            'language-education': 'zaban-amozesh.jpg',
            'zaban-amozesh': 'zaban-amozesh.jpg',
            'خدمات دیجیتال': 'khademat-digital.jpg',
            'digital-services': 'khademat-digital.jpg',
            'khademat-digital': 'khademat-digital.jpg',
        }

        # Try slug first
        if hasattr(category, 'slug') and category.slug:
            slug_lower = category.slug.lower()
            if slug_lower in image_map:
                return image_map[slug_lower]

        # Try name
        if hasattr(category, 'name') and category.name:
            name_str = str(category.name).strip()
            if name_str in image_map:
                return image_map[name_str]

            # Try partial match on slug keywords
            if hasattr(category, 'slug') and category.slug:
                slug_lower = category.slug.lower()
                for key, value in image_map.items():
                    if key in slug_lower or slug_lower in key:
                        return value

        # Default fallback
        return 'car-naghlie.jpg'
    except Exception:
        return None
