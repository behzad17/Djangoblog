from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from django.db import models, transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ratelimit.decorators import ratelimit
from blog.decorators import site_verified_required
from notifications.dispatchers import notify_ad_favorited

from .models import AdCategory, Ad, FavoriteAd, AdComment
from .forms import AdForm, AdCommentForm, AdFilterForm, ProRequestForm
from .gallery import get_detail_image_context, process_gallery_submission
from .signals import notify_admin_pro_request
from ads.selectors.visibility import list_visible_ads as _visible_ads_queryset

SOCIAL_URL_FIELDS = ('instagram_url', 'telegram_url', 'website_url')


def pro_ads_landing(request):
    """Marketing page for Peyvand Pro ads (UI only)."""
    return render(request, 'ads/pro_landing.html')


def ad_category_list(request):
    """
    Dedicated advertisements landing page showing all ad categories and counts.
    """
    categories = AdCategory.objects.all().order_by("display_order", "name")
    # Prefetch visible ads to show counts efficiently
    visible_ads = _visible_ads_queryset()
    counts = {cat.id: 0 for cat in categories}
    for ad in visible_ads:
        if ad.category_id in counts:
            counts[ad.category_id] += 1
    
    # Detect active category from query params
    active_category_slug = request.GET.get('category') or request.GET.get('cat')

    return render(
        request,
        "ads/ads_home.html",
        {
            "categories": categories,
            "ad_counts": counts,
            "active_category_slug": active_category_slug,
        },
    )


def ad_list_by_category(request, category_slug):
    """
    List all visible ads for a specific category with pagination.
    Each category has its own dedicated URL.
    
    Pagination: 39 ads per page
    Page 1: Featured ads first (positions 1-39), then normal ads to fill remaining slots
    Page 2+: Only normal ads (featured ads excluded)
    """
    category = get_object_or_404(AdCategory, slug=category_slug)
    all_ads = _visible_ads_queryset().filter(category=category)
    
    # Get filter parameters
    selected_city = request.GET.get('city', '')
    sort_order = request.GET.get('sort', 'newest')
    
    # Apply city filter if provided
    if selected_city:
        all_ads = all_ads.filter(city__iexact=selected_city)
    
    # Get unique cities for dropdown (from ads in this category)
    available_cities = Ad.objects.filter(
        is_active=True,
        is_approved=True,
        category=category
    ).exclude(city__isnull=True).exclude(city='').values_list('city', flat=True).distinct().order_by('city')
    
    # Create filter form
    filter_form = AdFilterForm(
        initial={
            'city': selected_city,
            'sort': sort_order,
        },
        city_choices=list(available_cities)
    )
    
    # Note: Sort order is handled by _visible_ads_queryset() which orders by featured status first,
    # then by priority, then by created_on. For "oldest" sort, we'd need to modify the ordering,
    # but since featured ads should always appear first, we'll keep the current behavior
    # and only change the created_on ordering for non-featured ads if needed.
    # For simplicity, we'll keep the default ordering (newest first) for now.
    # If sort_order == 'oldest', we could reverse the created_on order, but this would
    # conflict with featured ads logic. We'll implement a simpler approach:
    # - Keep featured ads first (always)
    # - For normal ads, apply sort order
    
    # Separate featured and normal ads
    featured_ads = [ad for ad in all_ads if ad.is_currently_featured]
    normal_ads = [ad for ad in all_ads if not ad.is_currently_featured]
    
    # Apply sort to normal ads if requested (featured ads always stay first)
    if sort_order == 'oldest':
        # Sort normal ads by oldest first (reverse created_on order)
        normal_ads = sorted(normal_ads, key=lambda x: x.created_on)
    
    # Get page number
    page_number = request.GET.get('page', 1)
    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1
    
    ads_per_page = 39
    
    if page_number == 1:
        # Page 1: Featured ads first (up to 39), then fill with normal ads
        page_ads = []
        
        # Add featured ads (up to 39)
        featured_count = min(len(featured_ads), ads_per_page)
        page_ads.extend(featured_ads[:featured_count])
        
        # Fill remaining slots with normal ads
        remaining_slots = ads_per_page - len(page_ads)
        if remaining_slots > 0:
            page_ads.extend(normal_ads[:remaining_slots])
        
        # Calculate pagination for normal ads (excluding featured)
        # Total normal ads that need pagination (skip the ones shown on page 1)
        normal_ads_for_pagination = normal_ads[remaining_slots:]
        
        # Create paginator for remaining normal ads - Django Paginator handles unlimited pages automatically
        # It will create as many pages as needed (no limit - supports 2x39, 3x39, 4x39, etc.)
        paginator = Paginator(normal_ads_for_pagination, ads_per_page)
        total_pages = 1 + paginator.num_pages  # Page 1 + remaining pages (unlimited)
        
        context = {
            "category": category,
            "ads": page_ads,
            "page_obj": None,  # Custom pagination, not using page_obj
            "is_paginated": total_pages > 1,
            "has_previous": False,
            "has_next": paginator.num_pages > 0,
            "previous_page_number": None,
            "next_page_number": 2 if paginator.num_pages > 0 else None,
            "current_page": 1,
            "total_pages": total_pages,
            "filter_form": filter_form,
            "selected_city": selected_city,
            "sort_order": sort_order,
        }
    else:
        # Page 2+: Only normal ads
        # Skip the normal ads that were shown on page 1
        featured_count = min(len(featured_ads), ads_per_page)
        remaining_slots = ads_per_page - featured_count
        normal_ads_for_pagination = normal_ads[remaining_slots:]
        
        # Paginate normal ads - Django Paginator automatically handles unlimited pages
        # It will create as many pages as needed based on total ads (no limit)
        paginator = Paginator(normal_ads_for_pagination, ads_per_page)
        
        # Adjust page number (page 2 in URL = page 1 in paginator, page 3 = paginator page 2, etc.)
        paginator_page_number = page_number - 1
        
        try:
            page_obj = paginator.page(paginator_page_number)
        except EmptyPage:
            # Page number is out of range, redirect to last valid page
            page_obj = paginator.page(paginator.num_pages)
            paginator_page_number = paginator.num_pages
            page_number = 1 + paginator.num_pages  # Adjust page_number to match
        except PageNotAnInteger:
            # Invalid page number, show first page of normal ads (page 2)
            page_obj = paginator.page(1)
            paginator_page_number = 1
            page_number = 2  # Adjust page_number to match
        
        # Total pages = 1 (page 1 with featured) + paginator pages
        total_pages = 1 + paginator.num_pages
        
        context = {
            "category": category,
            "ads": list(page_obj.object_list),
            "page_obj": page_obj,
            "is_paginated": total_pages > 1,
            "has_previous": page_number > 1,
            "has_next": page_number < total_pages,
            "previous_page_number": page_number - 1 if page_number > 1 else None,
            "next_page_number": page_number + 1 if page_number < total_pages else None,
            "current_page": page_number,
            "total_pages": total_pages,
            "filter_form": filter_form,
            "selected_city": selected_city,
            "sort_order": sort_order,
        }
    
    return render(request, "ads/ads_by_category.html", context)


@ratelimit(key='ip', rate='20/m', method='POST', block=True)
def ad_detail(request, slug):
    """
    Detail page for a single ad.

    Public users (including anonymous visitors) may view visible Pro ads.
    Owners may view their own ads regardless of plan, approval, active status,
    or date window (e.g. Pro request).
    
    Handles both GET (display) and POST (comment submission) requests.
    POST actions require authentication.
    Comments are published immediately (no moderation).
    """
    ad = get_object_or_404(
        Ad.objects.select_related('category', 'owner').prefetch_related('gallery_images'),
        slug=slug,
    )

    is_owner = ad.owner_id == request.user.id
    if not is_owner:
        if ad.plan != 'pro':
            raise Http404(
                "Free ads do not have detail pages. Only Pro ads can be viewed in detail."
            )
        if not _visible_ads_queryset().filter(pk=ad.pk).exists():
            raise Http404("Ad is not currently visible.")
    
    # Increment aggregated view count (only for GET requests)
    # Wrap in try-except to prevent tracking errors from breaking the page
    if request.method == 'GET':
        try:
            from blog.utils import increment_ad_view_count
            increment_ad_view_count(request, ad)
        except Exception as e:
            # Log the error but don't break the page view
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error incrementing view count for ad {ad.slug}: {e}", exc_info=True)
    
    # Determine if current user has already favorited this ad
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = FavoriteAd.objects.filter(
            user=request.user,
            ad=ad,
        ).exists()
    
    # Load comments (exclude deleted ones)
    comments = ad.comments.filter(is_deleted=False).select_related('author').order_by('created_on')
    comment_count = comments.count()
    comment_form = AdCommentForm()
    pro_request_form = ProRequestForm()
    
    # Determine if user can request Pro upgrade
    can_request_pro = False
    if request.user.is_authenticated and ad.owner == request.user:
        if ad.plan == 'free' and not ad.pro_requested:
            can_request_pro = True
    
    # Handle POST request
    if request.method == "POST":
        # Require authentication (already handled by @login_required, but defensive check)
        if not request.user.is_authenticated:
            messages.error(request, 'لطفاً برای این عملیات وارد شوید.')
            return redirect('account_login')
        
        # Check if this is a Pro request or comment
        if 'pro_request' in request.POST:
            # Handle Pro request
            # Check ownership
            if ad.owner != request.user:
                messages.error(request, 'شما اجازه درخواست Pro برای این تبلیغ را ندارید.')
                return redirect('ads:ad_detail', slug=slug)
            
            # Check if already Pro
            if ad.plan == 'pro':
                messages.info(request, 'این تبلیغ قبلاً Pro است.')
                return redirect('ads:ad_detail', slug=slug)
            
            # Check if already requested
            if ad.pro_requested:
                messages.info(request, 'درخواست Pro شما قبلاً ثبت شده است.')
                return redirect('ads:ad_detail', slug=slug)
            
            # Process Pro request form
            pro_request_form = ProRequestForm(data=request.POST)
            if pro_request_form.is_valid():
                ad.pro_requested = True
                ad.pro_request_phone = pro_request_form.cleaned_data['phone']
                ad.pro_requested_at = timezone.now()
                ad.save()
                notify_admin_pro_request(ad)
                messages.success(request, 'درخواست شما ثبت شد، به زودی با شما تماس می‌گیریم.')
                return redirect('ads:ad_detail', slug=slug)
            else:
                # Form has errors, will be displayed in template
                messages.error(request, 'لطفاً خطاهای فرم را برطرف کنید.')
        else:
            # Handle comment form submission
            # Require site verification for comments
            # Ensure user has a profile (create if missing)
            if not hasattr(request.user, 'profile'):
                from blog.models import UserProfile
                UserProfile.objects.get_or_create(user=request.user)

            # Check site verification
            if not request.user.profile.is_site_verified:
                messages.warning(
                    request,
                    'لطفاً ابتدا تنظیمات حساب کاربری خود را تکمیل کنید.'
                )
                return redirect('complete_setup')

            # Process comment form
            comment_form = AdCommentForm(data=request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.author = request.user
                comment.ad = ad
                # No approval needed - publish immediately
                comment.save()

                messages.success(request, 'نظر شما با موفقیت ثبت شد!')
                return redirect('ads:ad_detail', slug=slug)
            else:
                # Form has errors, will be displayed in template
                messages.error(request, 'لطفاً خطاهای فرم را برطرف کنید.')
    
    context = {
        "ad": ad,
        "is_favorited": is_favorited,
        "comments": comments,
        "comment_count": comment_count,
        "comment_form": comment_form,
        "pro_request_form": pro_request_form,
        "can_request_pro": can_request_pro,
    }
    context.update(get_detail_image_context(ad))
    return render(request, "ads/ad_detail.html", context)


@ratelimit(key='user', rate='5/h', method='POST', block=True)
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
@site_verified_required
@login_required
def create_ad(request):
    """
    Allow authenticated users to create ads.
    Ads require admin approval before being visible.
    """
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                ad = form.save(commit=False)
                ad.owner = request.user
                ad.is_approved = False  # Require admin approval
                ad.url_approved = False  # Require URL approval
                ad.is_active = True
                ad.save()
                gallery_errors = process_gallery_submission(ad, request.POST, request.FILES)
            if gallery_errors:
                for error in gallery_errors:
                    messages.error(request, error)
                return render(
                    request,
                    'ads/create_ad.html',
                    {'form': form, 'gallery_images': []},
                )
            messages.success(
                request,
                'تبلیغ شما با موفقیت ایجاد شد! در انتظار تایید مدیر می‌باشد.'
            )
            return redirect('ads:my_ads')
    else:
        # Pre-select category if provided in query string
        initial = {}
        category_slug = request.GET.get('category')
        if category_slug:
            try:
                category = AdCategory.objects.get(slug=category_slug)
                initial['category'] = category
            except AdCategory.DoesNotExist:
                pass
        form = AdForm(initial=initial)
    
    return render(request, 'ads/create_ad.html', {
        'form': form,
        'gallery_images': [],
    })


@site_verified_required
@login_required
def edit_ad(request, slug):
    """
    Allow ad owners to edit their ads.
    Resets approval status if content is changed.
    """
    ad = get_object_or_404(Ad, slug=slug)
    
    # Permission check - only owner can edit
    if ad.owner != request.user:
        messages.error(request, 'شما اجازه ویرایش این تبلیغ را ندارید.')
        return redirect('ads:ads_home')
    
    if request.method == 'POST':
        original_social_urls = {
            field: getattr(ad, field) for field in SOCIAL_URL_FIELDS
        }
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            with transaction.atomic():
                ad = form.save(commit=False)
                social_urls_changed = any(
                    getattr(ad, field) != original_social_urls[field]
                    for field in SOCIAL_URL_FIELDS
                )
                if social_urls_changed:
                    ad.social_urls_approved = False
                approval_reset = ad.is_approved
                if approval_reset:
                    ad.is_approved = False
                    ad.url_approved = False
                ad.save()
                gallery_errors = process_gallery_submission(ad, request.POST, request.FILES)
            if gallery_errors:
                for error in gallery_errors:
                    messages.error(request, error)
                return render(
                    request,
                    'ads/edit_ad.html',
                    {
                        'form': form,
                        'ad': ad,
                        'gallery_images': list(ad.gallery_images.all()),
                    },
                )
            if approval_reset:
                messages.info(
                    request,
                    'تبلیغ به‌روزرسانی شد. در انتظار تایید مجدد مدیر می‌باشد.'
                )
            else:
                messages.success(request, 'تبلیغ با موفقیت به‌روزرسانی شد.')
            return redirect('ads:my_ads')
    else:
        form = AdForm(instance=ad)
    
    return render(request, 'ads/edit_ad.html', {
        'form': form,
        'ad': ad,
        'gallery_images': list(ad.gallery_images.all()),
    })


@login_required
def delete_ad(request, slug):
    """
    Allow ad owners to delete their ads.
    """
    ad = get_object_or_404(Ad, slug=slug)
    
    # Permission check - only owner can delete
    if ad.owner != request.user:
        messages.error(request, 'شما اجازه حذف این تبلیغ را ندارید.')
        return redirect('ads:ads_home')
    
    if request.method == 'POST':
        ad_title = ad.title
        ad.delete()
        messages.success(request, f'تبلیغ "{ad_title}" با موفقیت حذف شد.')
        return redirect('ads:my_ads')
    
    return render(request, 'ads/delete_ad.html', {'ad': ad})


@login_required
def my_ads(request):
    """
    List all ads created by the current user.
    Shows approval status and allows edit/delete.
    """
    from django.contrib import messages
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Use select_related to avoid N+1 queries and ensure related objects are loaded
        # Filter out ads with empty or null slugs to prevent URL generation errors
        ads = (
            Ad.objects.filter(owner=request.user)
            .exclude(slug__isnull=True)
            .exclude(slug='')
            .select_related("category", "owner")
            .order_by("-created_on")
        )
    except Exception as exc:  # Defensive: prevent unexpected DB errors from causing 500
        logger.error("Error loading my_ads for user %s: %s", request.user.id, exc, exc_info=True)
        messages.error(
            request,
            "در بارگذاری لیست تبلیغات شما خطایی رخ داد. لطفاً چند لحظه بعد دوباره تلاش کنید.",
        )
        ads = []

    return render(request, "ads/my_ads.html", {"ads": ads})


@login_required
def add_ad_to_favorites(request, ad_id):
    """
    View function for adding or removing an ad from favorites.

    This view toggles the favorite status of an ad for the current user.
    If the ad is already favorited, it will be removed from favorites.
    If not, it will be added to favorites.
    """
    ad = get_object_or_404(Ad, id=ad_id)
    favorite, created = FavoriteAd.objects.get_or_create(
        user=request.user, ad=ad
    )

    if created:
        notify_ad_favorited(ad, request.user)
    else:
        favorite.delete()  # delete if an ad is saved before

    return redirect(
        request.META.get('HTTP_REFERER', 'ads:ads_home')
    )


@login_required
def remove_ad_from_favorites(request, ad_id):
    """
    View function for removing an ad from favorites.
    
    This view removes the favorite status of an ad for the current user.
    Used from the favorites page to remove ads.
    """
    ad = get_object_or_404(Ad, id=ad_id)
    try:
        favorite = FavoriteAd.objects.get(user=request.user, ad=ad)
        favorite.delete()
        messages.success(request, 'تبلیغ از علاقه‌مندی‌ها حذف شد.')
    except FavoriteAd.DoesNotExist:
        messages.error(request, 'این تبلیغ در علاقه‌مندی‌های شما نیست.')
    
    return redirect('favorites')


@login_required
def delete_ad_comment(request, slug, comment_id):
    """
    View function for deleting (soft delete) an ad comment.
    
    Only the comment author can delete their own comments.
    Uses soft delete (is_deleted=True) instead of hard delete.
    """
    ad = get_object_or_404(
        Ad.objects.select_related('category', 'owner'),
        slug=slug,
    )

    is_owner = ad.owner_id == request.user.id
    if not is_owner:
        if ad.plan != 'pro':
            raise Http404(
                "Free ads do not have detail pages. Only Pro ads can be viewed in detail."
            )
        if not _visible_ads_queryset().filter(pk=ad.pk).exists():
            raise Http404("Ad is not currently visible.")

    comment = get_object_or_404(AdComment, id=comment_id, ad=ad)
    
    # Permission check - only author can delete
    if comment.author != request.user:
        messages.error(request, 'شما اجازه حذف این نظر را ندارید.')
        return redirect('ads:ad_detail', slug=slug)
    
    # Soft delete
    if request.method == "POST":
        comment.is_deleted = True
        comment.save()
        messages.success(request, 'نظر شما با موفقیت حذف شد.')
    else:
        messages.error(request, 'درخواست نامعتبر.')
    
    return redirect('ads:ad_detail', slug=slug)


# Create your views here.
