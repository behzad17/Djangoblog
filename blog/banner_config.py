"""
Central registry for static image banner slots (homepage + post detail sidebar).

Cloudinary-backed ads in the ads app are separate — do not register them here.
"""

STATIC_BANNERS = {
    'ad-top': {
        'image': 'ad-top',
        'url': '#',
    },
    'ad-1': {
        'image': 'ad-1',
        'url': '#',
    },
    'ad-2': {
        'image': 'ad-2',
        'url': 'https://www.nordicphoenix.se',
    },
    'ad-3': {
        'image': 'ad-3',
        'url': 'https://www.bokadirekt.se/places/holistic-touch-135389?utm_source=ig&utm_medium=social&utm_content=link_in_bio',
    },
}

POST_DETAIL_SIDEBAR_SLOTS = ('ad-top', 'ad-1', 'ad-2', 'ad-3')


def get_static_banner_url(slot_id):
    banner = STATIC_BANNERS.get(slot_id, {})
    return banner.get('url', '#')


def get_static_banner_image_stem(slot_id):
    banner = STATIC_BANNERS.get(slot_id, {})
    return banner.get('image', slot_id)
