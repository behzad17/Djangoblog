from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ratelimit.decorators import ratelimit
from blog.decorators import site_verified_required
from .models import AdCategory, Ad, FavoriteAd, AdComment
from .forms import AdForm, AdCommentForm


def _visible_ads_queryset():
    """
    Base queryset for ads that should be visible on the site.
    Featured ads appear first, then ordered by newest.
    Only requires is_approved=True (admin approval) to appear in list.
    URL approval is separate and only affects whether the URL is clickable.
    """
    today = timezone.now().date()
    now = timezone.now()
    qs = Ad.objects.filter(
        is_active=True,
        is_approved=True,
    )
    # Apply date filters only when set
    qs = qs.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today),
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today),
    )
    # Order by: featured first (only if featured_until is in future or null), then by priority, then newest
    # Annotate to check if featured status is currently active
    from django.db.models import Case, When, BooleanField, Q, F, Value, IntegerField
    qs = qs.annotate(
        is_currently_featured=Case(
            When(
                Q(is_featured=True) & (Q(featured_until__isnull=True) | Q(featured_until__gt=now)),
                then=True
            ),
            default=False,
            output_field=BooleanField()
        )
    )
    # Order: featured first, then by featured_priority (lower = higher priority), then by created_on
    # Use a large number (999999) for featured ads without priority so they appear after prioritized ones
    qs = qs.annotate(
        priority_value=Case(
            When(
                is_currently_featured=True,
                then=Case(
                    When(featured_priority__isnull=False, then=F('featured_priority')),
                    default=Value(999999, output_field=IntegerField())  # Featured ads without priority go to end
                )
            ),
            default=Value(9999999, output_field=IntegerField())  # Non-featured ads go to very end
        )
    ).order_by('-is_currently_featured', 'priority_value', '-created_on')
    return qs.select_related("category")


def ad_category_list(request):
    """
    Dedicated advertisements landing page showing all ad categories and counts.
    """
    categories = AdCategory.objects.all().order_by("name")
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
    
    # Separate featured and normal ads
    featured_ads = [ad for ad in all_ads if ad.is_currently_featured]
    normal_ads = [ad for ad in all_ads if not ad.is_currently_featured]
    
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
        }
    
    return render(request, "ads/ads_by_category.html", context)


@ratelimit(key='ip', rate='20/m', method='POST', block=True)
@login_required
def ad_detail(request, slug):
    """
    Detail page for a single ad.

    Each ad has its own slug-based URL. Only visible if the ad is currently
    active, approved, and within its date range.
    
    Handles both GET (display) and POST (comment submission) requests.
    Comments are published immediately (no moderation).
    """
    ad = get_object_or_404(
        _visible_ads_queryset().select_related('category', 'owner'),
        slug=slug
    )
    
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
    
    # Handle POST request for comment submission
    if request.method == "POST":
        # Require authentication (already handled by @login_required, but defensive check)
        if not request.user.is_authenticated:
            messages.error(request, 'لطفاً برای ثبت نظر وارد شوید.')
            return redirect('account_login')
        
        # Require site verification for comments
        # Ensure user has a profile (create if missing)
        if not hasattr(request.user, 'profile'):
            from blog.models import UserProfile
            UserProfile.objects.get_or_create(user=request.user)
        
        # Check site verification
        if not request.user.profile.is_site_verified:
            messages.warning(request, 'لطفاً ابتدا تنظیمات حساب کاربری خود را تکمیل کنید.')
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
    }
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
            ad = form.save(commit=False)
            ad.owner = request.user
            ad.is_approved = False  # Require admin approval
            ad.url_approved = False  # Require URL approval
            ad.is_active = True
            ad.save()
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
    
    return render(request, 'ads/create_ad.html', {'form': form})


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
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            ad = form.save(commit=False)
            # Reset approval if content changed (admin needs to review again)
            if ad.is_approved:
                ad.is_approved = False
                ad.url_approved = False
                messages.info(
                    request,
                    'تبلیغ به‌روزرسانی شد. در انتظار تایید مجدد مدیر می‌باشد.'
                )
            else:
                messages.success(request, 'تبلیغ با موفقیت به‌روزرسانی شد.')
            ad.save()
            return redirect('ads:my_ads')
    else:
        form = AdForm(instance=ad)
    
    return render(request, 'ads/edit_ad.html', {'form': form, 'ad': ad})


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
    ads = Ad.objects.filter(owner=request.user).order_by('-created_on')
    return render(request, 'ads/my_ads.html', {'ads': ads})


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

    if not created:
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
    ad = get_object_or_404(_visible_ads_queryset(), slug=slug)
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
