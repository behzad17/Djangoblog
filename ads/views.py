from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from ratelimit.decorators import ratelimit
from blog.decorators import site_verified_required
from .models import AdCategory, Ad, FavoriteAd
from .forms import AdForm


def _visible_ads_queryset():
    """
    Base queryset for ads that should be visible on the site.
    Featured ads appear first, then ordered by newest.
    """
    today = timezone.now().date()
    now = timezone.now()
    qs = Ad.objects.filter(
        is_active=True,
        is_approved=True,
        url_approved=True,
    )
    # Apply date filters only when set
    qs = qs.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today),
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today),
    )
    # Order by: featured first (only if featured_until is in future or null), then newest
    # Annotate to check if featured status is currently active
    from django.db.models import Case, When, BooleanField, Q
    qs = qs.annotate(
        is_currently_featured=Case(
            When(
                Q(is_featured=True) & (Q(featured_until__isnull=True) | Q(featured_until__gt=now)),
                then=True
            ),
            default=False,
            output_field=BooleanField()
        )
    ).order_by('-is_currently_featured', '-created_on')
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

    return render(
        request,
        "ads/ads_home.html",
        {
            "categories": categories,
            "ad_counts": counts,
        },
    )


def ad_list_by_category(request, category_slug):
    """
    List all visible ads for a specific category.
    Each category has its own dedicated URL.
    """
    category = get_object_or_404(AdCategory, slug=category_slug)
    ads = _visible_ads_queryset().filter(category=category)
    context = {
        "category": category,
        "ads": ads,
    }
    return render(request, "ads/ads_by_category.html", context)


def ad_detail(request, slug):
    """
    Detail page for a single ad.

    Each ad has its own slug-based URL. Only visible if the ad is currently
    active, approved, and within its date range.
    """
    ad = get_object_or_404(_visible_ads_queryset(), slug=slug)
    
    # Determine if current user has already favorited this ad
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = FavoriteAd.objects.filter(
            user=request.user,
            ad=ad,
        ).exists()
    
    context = {
        "ad": ad,
        "is_favorited": is_favorited,
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


# Create your views here.
