from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_http_methods, require_POST
from ratelimit.decorators import ratelimit

from blog.decorators import site_verified_required
from community.constants import DiscussionStatus
from community.exceptions import CommunityDomainError
from community.forms import DiscussionCreateForm, ReplyCreateForm
from community.permissions import can_close, can_create_discussion, can_reply
from community.selectors.categories import (
    get_category_by_slug,
    list_active_categories_with_discussion_counts,
)
from community.selectors.discussions import (
    get_discussion_by_slug,
    list_closed_discussions,
    list_discussions,
    list_discussions_by_category,
    list_open_discussions,
)
from community.selectors.replies import list_public_replies
from community.selectors.stats import get_community_home_stats
from ads.selectors.related import get_related_ads
from experts.selectors.related import get_related_experts
from related_links.selectors.related import get_related_links
from community.services.discussions import close_discussion, create_discussion
from community.services.replies import create_reply


def _paginate(request, queryset):
    page_size = getattr(settings, 'COMMUNITY_LIST_PAGE_SIZE', 12)
    paginator = Paginator(queryset, page_size)
    return paginator.get_page(request.GET.get('page'))


def _create_discussion_url(user) -> str:
    if not getattr(user, 'is_authenticated', False):
        params = urlencode({'next': reverse('community:discussion_create')})
        return f"{reverse('account_login')}?{params}"
    if can_create_discussion(user):
        return reverse('community:discussion_create')
    return reverse('complete_setup')


def _show_verification_prompt(user, discussion) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    if discussion.is_deleted or discussion.status != DiscussionStatus.OPEN:
        return False
    profile = getattr(user, 'profile', None)
    return profile is None or not profile.is_site_verified


def community_home(request):
    return redirect('community:discussion_list')


@require_http_methods(['GET'])
def discussion_list(request):
    sort = request.GET.get('sort', 'active')
    status = request.GET.get('status', 'all')
    category_slug = request.GET.get('category', '').strip()

    selected_category = None
    if category_slug:
        try:
            selected_category = get_category_by_slug(category_slug)
            queryset = list_discussions_by_category(selected_category)
        except Exception:
            queryset = list_discussions()
    elif status == 'open':
        queryset = list_open_discussions()
    elif status == 'closed':
        queryset = list_closed_discussions()
    else:
        queryset = list_discussions()

    if selected_category and status == 'open':
        queryset = queryset.filter(status=DiscussionStatus.OPEN)
    elif selected_category and status == 'closed':
        queryset = queryset.filter(status=DiscussionStatus.CLOSED)

    if sort == 'newest':
        queryset = queryset.order_by('-created_on')

    page_obj = _paginate(request, queryset)
    search_query = request.GET.get('q', '').strip()
    return render(
        request,
        'community/discussion_list.html',
        {
            'page_obj': page_obj,
            'discussions': page_obj.object_list,
            'categories': list_active_categories_with_discussion_counts(),
            'selected_category': selected_category,
            'sort': sort,
            'status': status,
            'create_discussion_url': _create_discussion_url(request.user),
            'community_home_stats': get_community_home_stats(),
            'show_search_guidance': not search_query,
        },
    )


@require_http_methods(['GET'])
def discussion_detail(request, slug):
    try:
        discussion = get_discussion_by_slug(slug)
    except Exception as exc:
        raise Http404('Discussion not found.') from exc

    replies = list_public_replies(discussion)
    related_ads = get_related_ads(discussion, limit=3)
    related_experts = get_related_experts(discussion, limit=3)
    related_useful_links = get_related_links(discussion, limit=3)
    return render(
        request,
        'community/discussion_detail.html',
        {
            'discussion': discussion,
            'replies': replies,
            'related_ads': related_ads,
            'related_experts': related_experts,
            'related_useful_links': related_useful_links,
            'reply_form': ReplyCreateForm(),
            'can_reply': can_reply(request.user, discussion),
            'can_close': can_close(request.user, discussion),
            'is_closed': discussion.status == DiscussionStatus.CLOSED,
            'show_verification_prompt': _show_verification_prompt(
                request.user,
                discussion,
            ),
        },
    )


@login_required
@site_verified_required
@ratelimit(
    key='user',
    rate=settings.COMMUNITY_RATE_LIMIT_DISCUSSIONS_USER,
    method='POST',
    block=True,
)
@require_http_methods(['GET', 'POST'])
def discussion_create(request):
    if request.method == 'POST':
        form = DiscussionCreateForm(request.POST)
        if form.is_valid():
            discussion = create_discussion(
                author=request.user,
                category=form.cleaned_data['category'],
                title=form.cleaned_data['title'],
                body=form.cleaned_data['body'],
            )
            messages.success(request, 'بحث شما با موفقیت ایجاد شد.')
            return redirect('community:discussion_detail', slug=discussion.slug)
    else:
        form = DiscussionCreateForm()

    return render(
        request,
        'community/discussion_create.html',
        {'form': form},
    )


@login_required
@site_verified_required
@ratelimit(
    key='user',
    rate=settings.COMMUNITY_RATE_LIMIT_REPLIES_USER,
    method='POST',
    block=True,
)
@require_POST
def discussion_reply(request, slug):
    try:
        discussion = get_discussion_by_slug(slug)
    except Exception as exc:
        raise Http404('Discussion not found.') from exc

    if not can_reply(request.user, discussion):
        messages.error(request, 'امکان ثبت پاسخ برای این بحث وجود ندارد.')
        return redirect('community:discussion_detail', slug=slug)

    form = ReplyCreateForm(request.POST)
    if not form.is_valid():
        for error in form.errors.get('body', []):
            messages.error(request, error)
        return redirect('community:discussion_detail', slug=slug)

    try:
        reply = create_reply(
            discussion=discussion,
            author=request.user,
            body=form.cleaned_data['body'],
        )
    except CommunityDomainError as exc:
        messages.error(request, str(exc))
        return redirect('community:discussion_detail', slug=slug)

    if reply.approved:
        messages.success(request, 'پاسخ شما ثبت شد.')
    else:
        messages.info(
            request,
            'پاسخ شما ثبت شد و پس از بررسی نمایش داده می‌شود.',
        )
    return redirect('community:discussion_detail', slug=slug)


@login_required
@require_POST
def discussion_close(request, slug):
    try:
        discussion = get_discussion_by_slug(slug)
    except Exception as exc:
        raise Http404('Discussion not found.') from exc

    if not can_close(request.user, discussion):
        messages.error(request, 'شما اجازه بستن این بحث را ندارید.')
        return redirect('community:discussion_detail', slug=slug)

    try:
        close_discussion(discussion, closed_by=request.user)
    except CommunityDomainError as exc:
        messages.error(request, str(exc))
        return redirect('community:discussion_detail', slug=slug)

    messages.success(request, 'بحث بسته شد و پاسخ جدید پذیرفته نمی‌شود.')
    return redirect('community:discussion_detail', slug=slug)
