from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import strip_tags

from ads.models import Ad
from blog.models import Post

from .email import build_site_url

User = get_user_model()

EVENTS_CATEGORY_SLUG = 'events-announcements'
FEATURED_LIMIT = 3

SUMMARY_SPECS = (
    ('new_articles', '📰', '{count} مقاله جدید'),
    ('new_events', '📅', '{count} رویداد جدید'),
    ('new_businesses', '🏢', '{count} کسب‌وکار جدید'),
    ('new_pro_ads', '⭐', '{count} آگهی ویژه جدید'),
)


def get_weekly_digest_period():
    """Return the 7-day window ending at the start of today (local time)."""
    from django.utils import timezone

    period_end = timezone.localdate()
    period_start = period_end - timedelta(days=7)
    return period_start, period_end


def _period_datetimes(period_start, period_end):
    from django.utils import timezone

    start_dt = timezone.make_aware(datetime.combine(period_start, datetime.min.time()))
    end_exclusive = period_end + timedelta(days=1)
    end_dt = timezone.make_aware(datetime.combine(end_exclusive, datetime.min.time()))
    return start_dt, end_dt


def _published_posts_in_period(start_dt, end_dt):
    return Post.objects.filter(
        status=1,
        is_deleted=False,
        created_on__gte=start_dt,
        created_on__lt=end_dt,
    ).exclude(slug='').exclude(slug__isnull=True)


def build_weekly_digest_stats(period_start, period_end):
    """Aggregate Peyvand activity counts for the weekly digest email."""
    start_dt, end_dt = _period_datetimes(period_start, period_end)
    published_posts = _published_posts_in_period(start_dt, end_dt)

    return {
        'new_articles': published_posts.exclude(
            category__slug=EVENTS_CATEGORY_SLUG
        ).count(),
        'new_events': published_posts.filter(
            category__slug=EVENTS_CATEGORY_SLUG
        ).count(),
        'new_businesses': Ad.objects.filter(
            is_approved=True,
            is_active=True,
            created_on__gte=start_dt,
            created_on__lt=end_dt,
        ).count(),
        'new_pro_ads': Ad.objects.filter(
            plan='pro',
            is_approved=True,
            is_active=True,
            updated_on__gte=start_dt,
            updated_on__lt=end_dt,
        ).count(),
        'period_start': period_start,
        'period_end': period_end,
    }


def build_weekly_digest_summary_lines(stats):
    """Return non-zero summary rows for the digest email."""
    lines = []
    for key, emoji, label_template in SUMMARY_SPECS:
        count = stats.get(key, 0)
        if count > 0:
            lines.append({
                'emoji': emoji,
                'text': label_template.format(count=count),
            })
    return lines


def _is_valid_thumbnail(url):
    return bool(url) and 'placeholder' not in url


def _absolute_media_url(url):
    if not url:
        return None
    if url.startswith('http'):
        return url
    return build_site_url(url)


def _truncate_one_line(text, limit=110):
    text = ' '.join((text or '').split())
    if len(text) <= limit:
        return text
    return f'{text[: limit - 1].rstrip()}…'


def _post_description(post):
    if post.excerpt.strip():
        return _truncate_one_line(post.excerpt.strip())
    if post.category.slug == EVENTS_CATEGORY_SLUG and post.event_location.strip():
        return _truncate_one_line(post.event_location.strip())
    return _truncate_one_line(strip_tags(post.content))


def _ad_description(ad):
    parts = []
    if ad.city:
        parts.append(ad.city.strip())
    if ad.category_id:
        parts.append(ad.category.name)
    return _truncate_one_line(' — '.join(parts) if parts else ad.title)


def _safe_image_url(image_field):
    if not image_field:
        return ''
    try:
        return getattr(image_field, 'url', '') or ''
    except (ValueError, AttributeError):
        return ''


def _post_featured_item(post):
    image_url = _safe_image_url(post.featured_image)
    thumbnail_url = None
    if _is_valid_thumbnail(image_url):
        thumbnail_url = _absolute_media_url(image_url)

    return {
        'title': post.title,
        'description': _post_description(post),
        'url': build_site_url(reverse('post_detail', args=[post.slug])),
        'thumbnail_url': thumbnail_url,
    }


def _ad_featured_item(ad):
    image_url = _safe_image_url(ad.image)
    thumbnail_url = _absolute_media_url(image_url) if _is_valid_thumbnail(image_url) else None

    return {
        'title': ad.title,
        'description': _ad_description(ad),
        'url': build_site_url(reverse('ads:ad_detail', args=[ad.slug])),
        'thumbnail_url': thumbnail_url,
    }


def _editorial_posts_queryset(start_dt, end_dt):
    expert_users = User.objects.filter(profile__can_publish_without_approval=True)
    return (
        _published_posts_in_period(start_dt, end_dt)
        .filter(author__in=expert_users)
        .exclude(category__slug=EVENTS_CATEGORY_SLUG)
        .select_related('category', 'author')
        .order_by('-created_on')
    )


def _event_posts_queryset(start_dt, end_dt):
    return (
        _published_posts_in_period(start_dt, end_dt)
        .filter(category__slug=EVENTS_CATEGORY_SLUG)
        .select_related('category')
        .order_by('-created_on')
    )


def _business_ads_queryset(start_dt, end_dt):
    return (
        Ad.objects.filter(
            is_approved=True,
            is_active=True,
            created_on__gte=start_dt,
            created_on__lt=end_dt,
        )
        .select_related('category')
        .order_by('-created_on')
    )


def _featured_pro_ads_queryset(start_dt, end_dt):
    return (
        Ad.objects.filter(
            plan='pro',
            is_approved=True,
            is_active=True,
            updated_on__gte=start_dt,
            updated_on__lt=end_dt,
        )
        .select_related('category')
        .order_by('-updated_on')
    )


def build_weekly_digest_featured_items(period_start, period_end, limit=FEATURED_LIMIT):
    """Pick up to three digest highlights by editorial → events → businesses → pro ads."""
    start_dt, end_dt = _period_datetimes(period_start, period_end)
    buckets = (
        _editorial_posts_queryset(start_dt, end_dt),
        _event_posts_queryset(start_dt, end_dt),
        _business_ads_queryset(start_dt, end_dt),
        _featured_pro_ads_queryset(start_dt, end_dt),
    )

    featured_items = []
    seen_keys = set()

    for bucket in buckets:
        for item in bucket:
            if isinstance(item, Post):
                key = ('post', item.pk)
                payload = _post_featured_item(item)
            else:
                key = ('ad', item.pk)
                payload = _ad_featured_item(item)

            if key in seen_keys:
                continue
            seen_keys.add(key)
            featured_items.append(payload)
            if len(featured_items) >= limit:
                return featured_items

    return featured_items


def build_weekly_digest_cta(stats):
    weekly_url = build_site_url(reverse('weekly_highlights'))
    if stats.get('new_articles', 0) > 0:
        return weekly_url, f"مشاهده همه {stats['new_articles']} مقاله"
    return weekly_url, 'مشاهده همه تازه‌های این هفته'


def _article_posts_queryset(start_dt, end_dt):
    return (
        _published_posts_in_period(start_dt, end_dt)
        .exclude(category__slug=EVENTS_CATEGORY_SLUG)
        .select_related('category', 'author')
        .order_by('-created_on')
    )


def build_weekly_digest_lists(period_start, period_end):
    """Return weekly content lists for the public highlights page."""
    start_dt, end_dt = _period_datetimes(period_start, period_end)
    return {
        'articles': list(_article_posts_queryset(start_dt, end_dt)),
        'events': list(_event_posts_queryset(start_dt, end_dt)),
        'businesses': list(_business_ads_queryset(start_dt, end_dt)),
        'pro_ads': list(_featured_pro_ads_queryset(start_dt, end_dt)),
    }


def build_weekly_digest_email_context(period_start, period_end):
    stats = build_weekly_digest_stats(period_start, period_end)
    cta_url, cta_text = build_weekly_digest_cta(stats)
    return {
        'summary_lines': build_weekly_digest_summary_lines(stats),
        'featured_items': build_weekly_digest_featured_items(period_start, period_end),
        'cta_url': cta_url,
        'cta_text': cta_text,
        'period_start': period_start,
        'period_end': period_end,
        **stats,
    }


def build_weekly_digest_page_context(period_start, period_end):
    stats = build_weekly_digest_stats(period_start, period_end)
    lists = build_weekly_digest_lists(period_start, period_end)
    return {
        'summary_lines': build_weekly_digest_summary_lines(stats),
        'featured_items': build_weekly_digest_featured_items(period_start, period_end),
        'period_start': period_start,
        'period_end': period_end,
        **stats,
        **lists,
    }


def get_weekly_digest_recipients(user_id=None):
    """Return active users opted in to the weekly digest."""
    queryset = User.objects.filter(
        is_active=True,
        notification_preferences__weekly_digest=True,
    ).exclude(email='')

    if user_id is not None:
        queryset = queryset.filter(pk=user_id)

    return queryset.select_related('notification_preferences').order_by('id')


def is_weekly_digest_send_day(for_date=None):
    """Return True when the weekly digest is allowed to send (Friday, local time)."""
    from django.utils import timezone

    target_date = for_date or timezone.localdate()
    return target_date.weekday() == 4
