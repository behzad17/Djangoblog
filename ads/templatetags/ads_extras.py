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
        # Based on actual database categories and images
        # Priority: exact slug > exact name > keyword match (specific)
        image_map = {
            # Exact slug matches (from database)
            'vehicles': 'car-naghlie.jpg',
            'housing': 'maskan-zendegi.jpg',
            'work-services': 'kar-herfeh.jpg',
            'leisure': 'oghate-feraghat.jpg',
            'food-restaurant': 'ghaza-farhang.jpg',
            'health-welfare': 'salamat-refah.jpg',
            'home-appliances': 'khane-vasayel.jpg',
            'legal-financial': 'hoghooghi-mali.jpg',
            # آموزش، زبان و یادگیری
            'mozsh-zbn-o-dr': 'zaban-amozesh.jpg',
            # فناوری و خدمات دیجیتال
            'fnor-o-khdmt-dgtl': 'khademat-digital.jpg',
            # Exact name matches (Persian - from database)
            # رفت‌ وآمد و وسایل نقلیه
            'رفت‌ وآمد و وسایل نقلیه': 'car-naghlie.jpg',
            # مسکن و زندگی روزمره
            'مسکن و زندگی روزمره': 'maskan-zendegi.jpg',
            # کار و همراهی حرفه‌ای
            'کار و همراهی حرفه‌ای': 'kar-herfeh.jpg',
            # اوقات فراغت و زندگی اجتماعی
            'اوقات فراغت و زندگی اجتماعی': 'oghate-feraghat.jpg',
            # غذا، طعم و فرهنگ
            'غذا، طعم و فرهنگ': 'ghaza-farhang.jpg',
            # سلامت، رفاه و مراقبت
            'سلامت، رفاه و مراقبت': 'salamat-refah.jpg',
            # خانه و وسایل زندگی
            'خانه و وسایل زندگی': 'khane-vasayel.jpg',
            # خدمات حقوقی و مالی سوئد
            'خدمات حقوقی و مالی سوئد': 'hoghooghi-mali.jpg',
            # آموزش، زبان و یادگیری
            'آموزش، زبان و یادگیری': 'zaban-amozesh.jpg',
            # فناوری و خدمات دیجیتال
            'فناوری و خدمات دیجیتال': 'khademat-digital.jpg',
        }

        # Keyword mapping for partial matches (ordered by priority)
        keyword_map = {
            # Vehicles
            'vehicles': 'car-naghlie.jpg',
            'نقلیه': 'car-naghlie.jpg',
            # Housing
            'housing': 'maskan-zendegi.jpg',
            'مسکن': 'maskan-zendegi.jpg',
            # Work
            'work-services': 'kar-herfeh.jpg',
            'work': 'kar-herfeh.jpg',
            'کار': 'kar-herfeh.jpg',
            # Leisure
            'leisure': 'oghate-feraghat.jpg',
            'فراغت': 'oghate-feraghat.jpg',
            # Food
            'food-restaurant': 'ghaza-farhang.jpg',
            'food': 'ghaza-farhang.jpg',
            'غذا': 'ghaza-farhang.jpg',
            # Health
            'health-welfare': 'salamat-refah.jpg',
            'health': 'salamat-refah.jpg',
            'سلامت': 'salamat-refah.jpg',
            # Home
            'home-appliances': 'khane-vasayel.jpg',
            'home': 'khane-vasayel.jpg',
            'خانه': 'khane-vasayel.jpg',
            # Legal
            'legal-financial': 'hoghooghi-mali.jpg',
            'legal': 'hoghooghi-mali.jpg',
            'حقوقی': 'hoghooghi-mali.jpg',
            # Education/Language
            'zaban': 'zaban-amozesh.jpg',
            'amozesh': 'zaban-amozesh.jpg',
            'آموزش': 'zaban-amozesh.jpg',
            'زبان': 'zaban-amozesh.jpg',
            # Digital
            'digital': 'khademat-digital.jpg',
            'دیجیتال': 'khademat-digital.jpg',
            'فناوری': 'khademat-digital.jpg',
        }

        # Try exact slug match first
        if hasattr(category, 'slug') and category.slug:
            slug_lower = category.slug.lower().strip()
            if slug_lower in image_map:
                return image_map[slug_lower]

        # Try exact name match
        if hasattr(category, 'name') and category.name:
            name_str = str(category.name).strip()
            if name_str in image_map:
                return image_map[name_str]

        # Try keyword matching (more specific, check slug first, then name)
        if hasattr(category, 'slug') and category.slug:
            slug_lower = category.slug.lower().strip()
            for keyword, image_file in keyword_map.items():
                if keyword in slug_lower:
                    return image_file

        if hasattr(category, 'name') and category.name:
            name_str = str(category.name).strip()
            for keyword, image_file in keyword_map.items():
                if keyword in name_str:
                    return image_file

        # Default fallback (should not happen if mapping is complete)
        return 'car-naghlie.jpg'
    except Exception:
        return None
