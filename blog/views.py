from django.db.models import Count, Q
from django.shortcuts import (
    render,
    get_object_or_404,
    reverse,
    redirect,
)
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from ratelimit.decorators import ratelimit
from django.utils.text import slugify
import json

from .models import Post, Comment, Favorite, Category, Like
from .forms import CommentForm, PostForm
from .utils import track_page_view, determine_comment_approval
from .decorators import site_verified_required
from ads.models import FavoriteAd
from django.utils import timezone


class PostList(generic.ListView):
    """
    A view that displays a list of published blog posts.

    This view inherits from Django's generic ListView and displays posts
    that have been published (status=1). It includes a count of approved
    comments for each post.
    """
    template_name = "blog/index.html"
    paginate_by = 24

    def get_queryset(self):
        """
        Returns a queryset of published posts with comment counts.
        Posts are ordered by creation date (newest first).
        Includes all posts (including pinned) for correct pagination count.
        """
        return Post.objects.filter(status=1, is_deleted=False).select_related('category').annotate(
            comment_count=Count('comments', filter=Q(comments__approved=True))
        ).order_by('-created_on')
    
    def get_context_data(self, **kwargs):
        """
        Add categories and popular posts to the context for display in template.
        Also reorders posts so pinned posts appear in the second slot of each row.
        """
        # Ensure object_list is set before calling super()
        if not hasattr(self, 'object_list'):
            self.object_list = self.get_queryset()
        # Base context (includes pagination from Django's ListView)
        # This gives us page_obj with correct pagination info for ALL posts
        context = super().get_context_data(**kwargs)

        # Get the paginated page object from Django's ListView
        page_obj = context.get('page_obj')
        if not page_obj:
            # Fallback if pagination didn't work
            page_size = self.paginate_by
            page_number = int(self.request.GET.get('page', 1))
            paginator = Paginator(self.get_queryset(), page_size)
            page_obj = paginator.get_page(page_number)
            context['page_obj'] = page_obj
            context['is_paginated'] = page_obj.has_other_pages()

        page_size = self.paginate_by
        page_number = page_obj.number
        rows_per_page = page_size // 4  # 6 rows for 24 items
        row_start = (page_number - 1) * rows_per_page + 1
        row_end = row_start + rows_per_page - 1

        # Get posts from the current page (already paginated by Django)
        page_posts = list(page_obj.object_list)
        
        # On page 2+, exclude pinned posts from display (they only appear on page 1)
        # On page 1, we'll handle pinned posts separately
        if page_number == 1:
            # Separate pinned and regular posts from the current page
            regular_posts = [p for p in page_posts if not p.pinned]
        else:
            # Page 2+: Exclude pinned posts from display
            regular_posts = [p for p in page_posts if not p.pinned]

        # Pinned posts logic: ONLY on page 1, in specified rows
        pinned_by_row = {}
        pinned_fallback = []
        
        # Only process pinned posts on page 1
        if page_number == 1:
            # Fetch pinned posts and map to target rows (if specified)
            pinned_qs = Post.objects.filter(status=1, pinned=True, is_deleted=False).select_related('category', 'author').annotate(
                comment_count=Count('comments', filter=Q(comments__approved=True))
            ).order_by('-created_on')
            
            for p in pinned_qs:
                if p.pinned_row and row_start <= p.pinned_row <= row_end and p.pinned_row not in pinned_by_row:
                    # Pin to specific row on page 1
                    pinned_by_row[p.pinned_row] = p
                elif not p.pinned_row:
                    # No specific row - add to fallback for page 1 only
                    pinned_fallback.append(p)

        # Compose rows of 4, placing pinned (targeted row) into column 1; if missing, use fallback pinned, else regular
        merged = []
        fb_idx = 0
        r_idx = 0
        current_row_number = row_start
        while len(merged) < page_size and (r_idx < len(regular_posts) or (page_number == 1 and (fb_idx < len(pinned_fallback) or current_row_number in pinned_by_row))):
            row = []
            for col in range(4):
                if col == 1:
                    # Column 1: Try pinned post first (only on page 1)
                    if page_number == 1 and current_row_number in pinned_by_row:
                        row.append(pinned_by_row[current_row_number])
                    elif page_number == 1 and fb_idx < len(pinned_fallback):
                        row.append(pinned_fallback[fb_idx])
                        fb_idx += 1
                    else:
                        # Use regular post
                        if r_idx < len(regular_posts):
                            row.append(regular_posts[r_idx])
                            r_idx += 1
                        else:
                            break
                else:
                    # Columns 2, 3, 4: Always use regular posts
                    if r_idx < len(regular_posts):
                        row.append(regular_posts[r_idx])
                        r_idx += 1
                    else:
                        break
            merged.extend(row)
            current_row_number += 1
            if len(merged) >= page_size:
                break

        # Replace object_list with reordered data, but keep the original page_obj for pagination
        # The page_obj from Django's ListView has the correct pagination info for ALL posts
        context['object_list'] = merged
        context['post_list'] = merged
        # page_obj and is_paginated are already set correctly by Django's ListView
        # They reference the full queryset, not our reordered list

        # Categories and expert posts (replaces Popular Posts)
        context['categories'] = Category.objects.all().order_by('name')
        expert_users = User.objects.filter(
            profile__can_publish_without_approval=True
        )
        expert_posts_qs = (
            Post.objects.filter(
                status=1,
                author__in=expert_users,
                is_deleted=False
            )
            .select_related('category', 'author', 'author__profile')
            .annotate(comment_count=Count('comments', filter=Q(comments__approved=True)))
            .order_by('-created_on')
        )
        context['popular_posts'] = expert_posts_qs[:10]
        
        # Featured post for hero section (most recent post from experts content section)
        # Filter out posts with empty/null slugs to prevent NoReverseMatch errors
        featured_post = expert_posts_qs.exclude(slug='').exclude(slug__isnull=True).first()
        context['featured_post'] = featured_post

        return context


@ratelimit(key='ip', rate='20/m', method='POST', block=True)
def post_detail(request, slug):
    """
    View function for displaying a single blog post and its comments.
    
    This view handles both displaying the post and processing new comments.
    It shows approved comments to all users and unapproved comments to
    the comment author. It also tracks whether the post is in the user's
    favorites.
    """
    # Allow access to soft-deleted posts for author and staff
    queryset = Post.objects.filter(status=1).select_related('category', 'author')
    post = get_object_or_404(queryset, slug=slug)
    
    # Check if post is soft-deleted
    is_owner_or_staff = (
        request.user.is_authenticated and 
        (request.user == post.author or request.user.is_staff)
    )
    
    # If soft-deleted and user is not owner/staff, show placeholder
    if post.is_deleted and not is_owner_or_staff:
        return render(
            request,
            'blog/post_deleted.html',
            {'post': post},
        )
    
    # Track page view (only for GET requests)
    # Wrap in try-except to prevent tracking errors from breaking the page
    if request.method == 'GET':
        try:
            track_page_view(request, post=post)
        except Exception as e:
            # Log the error but don't break the page view
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error tracking page view for post {post.slug}: {e}", exc_info=True)
    
    # Filter comments: show approved comments + user's own unapproved comments
    if request.user.is_authenticated:
        comments = post.comments.filter(
            Q(approved=True) | Q(author=request.user)
        ).order_by("-created_on")
    else:
        comments = post.comments.filter(approved=True).order_by("-created_on")
    
    # Count only approved comments for display
    comment_count = post.comments.filter(approved=True).count()
    comment_form = CommentForm()
    # Determine if current user has already favorited this post
    is_favorited = False
    is_liked = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(
            user=request.user,
            post=post,
        ).exists()
        is_liked = Like.objects.filter(
            user=request.user,
            post=post,
        ).exists()

    if request.method == "POST":
        # Require authentication before accepting comments
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {
                        'status': 'error',
                        'message': 'Authentication required to comment.'
                    },
                    status=401
                )
            messages.error(request, 'Please log in to comment.')
            return redirect('account_login')
        
        # Require site verification for comments
        # Ensure user has a profile (create if missing)
        if not hasattr(request.user, 'profile'):
            from .models import UserProfile
            UserProfile.objects.get_or_create(user=request.user)
        
        # Check site verification
        if not request.user.profile.is_site_verified:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {
                        'status': 'error',
                        'message': 'Please complete your account setup before commenting.'
                    },
                    status=403
                )
            messages.warning(request, 'لطفاً ابتدا تنظیمات حساب کاربری خود را تکمیل کنید.')
            return redirect('complete_setup')

        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.post = post
            
            # Determine approval status based on trust and link detection
            approved, moderation_reason = determine_comment_approval(
                request.user, comment.body
            )
            comment.approved = approved
            comment.moderation_reason = moderation_reason
            
            comment.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'id': comment.id,
                    'author': comment.author.username,
                    'created_on': comment.created_on.strftime(
                        '%B %d, %Y %H:%M'
                    ),
                    'body': comment.body,
                    'post_slug': post.slug,
                    'approved': comment.approved,
                })

            # Context-aware success message
            if comment.approved:
                messages.add_message(
                    request, messages.SUCCESS,
                    'نظر شما با موفقیت ثبت شد!'
                )
            else:
                if comment.moderation_reason == 'contains_link':
                    messages.add_message(
                        request, messages.INFO,
                        'نظر شما ثبت شد و در انتظار بررسی است. '
                        'نظرات حاوی لینک نیاز به تایید مدیر دارند.'
                    )
                else:
                    messages.add_message(
                        request, messages.INFO,
                        'نظر شما ثبت شد و در انتظار بررسی است. '
                        'پس از تایید ۵ نظر، نظرات بعدی شما به صورت خودکار تایید می‌شوند.'
                    )
            return redirect('post_detail', slug=post.slug)

    # Get expert posts for sidebar (replaces Popular Posts)
    # Filter users with profiles that have can_publish_without_approval=True
    # Use profile__isnull=False to ensure we only get users with profiles
    try:
        expert_users = User.objects.filter(
            profile__isnull=False,
            profile__can_publish_without_approval=True
        ).select_related('profile')
        
        expert_posts = (
            Post.objects.filter(
                status=1,
                author__in=expert_users,
                is_deleted=False
            )
            .select_related('category', 'author')
            .order_by('-created_on')[:10]
        )
    except Exception as e:
        # If there's any error (database connection, missing profile, etc.),
        # fall back to empty queryset to prevent 500 error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching expert posts: {e}", exc_info=True)
        expert_posts = Post.objects.none()

    # Get related posts (3 max) from the same category, excluding current post
    related_posts = []
    if post.category:
        related_posts = (
            Post.objects.filter(
                status=1,
                category=post.category,
                is_deleted=False
            )
            .exclude(id=post.id)
            .select_related('category', 'author')
            .annotate(comment_count=Count('comments', filter=Q(comments__approved=True)))
            .order_by('-created_on')[:3]
        )

    # Flag to hide pending messages on published posts
    hide_pending_messages = post.status == 1

    # Calculate reading time and generate TOC
    # Wrap in try-except to prevent errors from breaking the page
    # Ensure content_with_anchors is always set, even if there's an error
    content_with_anchors = post.content or ''
    reading_time_minutes = 1
    toc_items = []
    show_toc = False
    
    try:
        from .utils import compute_reading_time, build_toc_and_anchors, should_show_toc
        
        # Ensure post.content is not None
        post_content = post.content or ''
        
        reading_time_minutes = compute_reading_time(post_content)
        toc_items, content_with_anchors = build_toc_and_anchors(post_content)
        show_toc = should_show_toc(post_content, toc_items)
    except Exception as e:
        # If TOC/reading time calculation fails, fall back to original content
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating reading time/TOC for post {post.slug}: {e}", exc_info=True)
        # Keep default values set above

    # Select template based on category
    if post.category and post.category.slug == 'photo-gallery':
        template_name = 'blog/post_detail_photo.html'
    else:
        template_name = 'blog/post_detail.html'

    return render(
        request,
        template_name,
        {
            "post": post,
            "comments": comments,
            "comment_count": comment_count,
            "comment_form": comment_form,
            "related_posts": related_posts,
            "is_favorited": is_favorited,
            "is_liked": is_liked,
            "popular_posts": expert_posts,
            "hide_pending_messages": hide_pending_messages,
            "reading_time_minutes": reading_time_minutes,
            "toc_items": toc_items if show_toc else [],
            "content_with_anchors": content_with_anchors,
            "show_toc": show_toc,
        },
    )


@site_verified_required
@login_required
def comment_edit(request, slug, comment_id):
    """
    View function for editing a comment.

    This view handles both GET and POST requests for editing comments.
    It ensures that only the comment author can edit their comments.
    Re-checks approval status if comment was previously approved.
    """
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user == comment.author:
        if request.method == "POST":
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                try:
                    data = json.loads(request.body)
                    new_body = data.get('body')
                    comment.body = new_body
                    
                    # Re-check approval if comment was previously approved
                    if comment.approved:
                        approved, moderation_reason = determine_comment_approval(
                            request.user, new_body
                        )
                        if not approved:
                            comment.approved = False
                            comment.moderation_reason = moderation_reason
                            comment.reviewed_by = None  # Reset review
                            comment.reviewed_at = None
                    
                    comment.save()
                    return JsonResponse({
                        'status': 'success',
                        'body': comment.body,
                        'approved': comment.approved,
                    })
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid request data'
                    }, status=400)
            else:
                form = CommentForm(request.POST, instance=comment)
                if form.is_valid():
                    comment = form.save(commit=False)
                    new_body = comment.body
                    
                    # Re-check approval if comment was previously approved
                    if comment.approved:
                        approved, moderation_reason = determine_comment_approval(
                            request.user, new_body
                        )
                        if not approved:
                            comment.approved = False
                            comment.moderation_reason = moderation_reason
                            comment.reviewed_by = None  # Reset review
                            comment.reviewed_at = None
                    
                    comment.save()
                    return redirect('post_detail', slug=slug)
        else:
            form = CommentForm(instance=comment)
        return render(request, 'blog/comment_edit.html', {
            'form': form,
            'slug': slug,
            'comment': comment
        })
    messages.error(request, 'You can only edit your own comments!')
    return redirect('post_detail', slug=slug)


@site_verified_required
@login_required
def comment_delete(request, slug, comment_id):
    """
    View function for deleting a comment.

    This view allows users to delete their own comments. Only the original
    author can delete their comments.
    """
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author == request.user:
        comment.delete()
        messages.add_message(
            request,
            messages.SUCCESS,
            'Your comment was deleted successfully!'
        )
    else:
        messages.add_message(
            request, messages.ERROR,
            'You can only delete your own comments!'
        )

    return HttpResponseRedirect(reverse('post_detail', args=[slug]))


@login_required
def add_to_favorites(request, post_id):
    """
    View function for adding or removing a post from favorites.

    This view toggles the favorite status of a post for the current user.
    If the post is already favorited, it will be removed from favorites.
    If not, it will be added to favorites.
    """
    post = get_object_or_404(Post, id=post_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user, post=post
    )

    if not created:
        favorite.delete()  # delete if a post is saved before

    return redirect(
        request.META.get('HTTP_REFERER', 'favorites')
    )


@login_required
def favorite_posts(request):
    """
    View function for displaying a user's favorite posts and ads.

    This view shows all posts and ads that the current user has marked as favorites.
    The view requires user authentication.
    """
    # Get favorite posts
    favorites = Favorite.objects.filter(user=request.user).select_related('post', 'post__category', 'post__author')
    favorite_posts = [favorite.post for favorite in favorites if favorite.post.status == 1 and not favorite.post.is_deleted]
    
    # Annotate posts with comment count
    posts_with_counts = []
    for post in favorite_posts:
        post.comment_count = post.comments.filter(approved=True).count()
        post.like_count = post.like_count()
        posts_with_counts.append(post)
    
    # Get favorite ads (only visible/approved ads)
    favorite_ads_queryset = FavoriteAd.objects.filter(
        user=request.user
    ).select_related('ad', 'ad__category')
    
    # Filter to only visible ads (using the same logic as _visible_ads_queryset)
    from django.utils import timezone
    today = timezone.now().date()
    favorite_ads = []
    for fav_ad in favorite_ads_queryset:
        ad = fav_ad.ad
        if (ad.is_active and ad.is_approved and ad.url_approved and
            (ad.start_date is None or ad.start_date <= today) and
            (ad.end_date is None or ad.end_date >= today)):
            favorite_ads.append(ad)
    
    return render(
        request,
        'blog/favorites.html',
        {
            'favorites': favorites,
            'favorite_posts': posts_with_counts,
            'favorite_ads': favorite_ads,
        },
    )


@login_required
def remove_from_favorites(request, post_id):
    """
    View function for removing a post from favorites.

    This view removes a specific post from the current user's favorites.
    The view requires user authentication.
    """
    post = get_object_or_404(Post, id=post_id)
    favorite = Favorite.objects.filter(user=request.user, post=post)

    if favorite.exists():
        favorite.delete()

    return redirect(
        request.META.get('HTTP_REFERER', 'favorites')
    )


@login_required
def like_post(request, post_id):
    """
    View function for liking or unliking a post.
    
    This view toggles the like status of a post for the current user.
    If the post is already liked, it will be unliked.
    If not, it will be liked.
    """
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(
        user=request.user, 
        post=post
    )
    
    if not created:
        like.delete()
        messages.success(request, 'Post unliked')
    else:
        messages.success(request, 'Post liked')
    
    return redirect('post_detail', slug=post.slug)


@ratelimit(key='user', rate='5/h', method='POST', block=True)
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
@site_verified_required
@login_required
def create_post(request):
    """
    View function for creating a new blog post.

    This view handles both GET and POST requests for creating new posts.
    It automatically sets the author to the current user and generates
    a slug from the title. The view requires user authentication.
    """
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # Generate unique slug
            base_slug = slugify(post.title)
            # Ensure slug is never empty (fallback to post ID or timestamp)
            if not base_slug:
                base_slug = f"post-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            post.slug = slug
            
            # Check if user has expert access (can publish without approval)
            is_expert = (
                hasattr(request.user, 'profile') and
                request.user.profile.can_publish_without_approval
            )
            
            # Set status based on expert access
            if is_expert:
                post.status = 1  # Published for experts
            else:
                post.status = 0  # Draft for regular users
            
            # URL approval defaults to False - admin must approve
            if post.external_url:
                post.url_approved = False
            post.save()
            
            # Show appropriate message based on expert status
            url_message = ''
            if post.external_url:
                url_message = ' If you added an external URL, it will also be reviewed and approved by an administrator before being displayed.'
            
            if is_expert:
                messages.add_message(
                    request, messages.SUCCESS,
                    '<div class="success-post-alert">'
                    '<i class="fas fa-check-circle me-2"></i>'
                    '<strong>Post Published Successfully!</strong><br>'
                    'Your post has been published and is now visible to all users.'
                    + url_message +
                    '</div>'
                )
            else:
                messages.add_message(
                    request, messages.WARNING,
                    '<div class="pending-post-alert">'
                    '<i class="fas fa-clock me-2"></i>'
                    '<strong>Post Created Successfully!</strong><br>'
                    'Your post has been saved as a draft and is pending for review. '
                    'An administrator will review and publish it soon. You will be notified once it\'s published.'
                    + url_message +
                    '</div>'
                )
            return redirect('home')
    else:
        form = PostForm()

    return render(
        request,
        'blog/create_post.html',
        {'form': form},
    )


@login_required
@login_required
def edit_post(request, slug):
    """
    View function for editing a blog post.

    This view allows post authors to edit their own posts.
    It requires user authentication and ensures only the author or staff can edit.
    """
    post = get_object_or_404(Post, slug=slug)
    
    # Check if user is the author or staff
    if request.user != post.author and not request.user.is_staff:
        messages.add_message(
            request, messages.ERROR,
            'You can only edit your own posts!'
        )
        return redirect('post_detail', slug=slug)
    
    # Prevent editing soft-deleted posts (unless staff)
    if post.is_deleted and not request.user.is_staff:
        messages.add_message(
            request, messages.ERROR,
            'Cannot edit a deleted post!'
        )
        return redirect('post_detail', slug=slug)
    
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            
            # Anti-abuse: If post is published/approved (status=1), set to Draft/Pending (status=0)
            # This requires re-approval by admin
            original_status = Post.objects.get(pk=post.pk).status
            if original_status == 1:  # Published
                post.status = 0  # Set to Draft/Pending Review
                needs_review = True
            else:
                needs_review = False
            
            # Check if user has expert access
            is_expert = (
                hasattr(request.user, 'profile') and
                request.user.profile.can_publish_without_approval
            )
            
            # Staff can change status, regular users cannot
            if not request.user.is_staff:
                # For non-staff, preserve status change (already set above if published)
                # Experts can publish without approval, but if editing published post, it goes to draft
                if is_expert and original_status == 0:
                    # Expert editing draft can keep it as draft or publish
                    # But since form doesn't have status field, keep current behavior
                    pass
            # For staff, they can change status via admin, but this form doesn't include status
            
            # Update slug if title changed
            new_slug = slugify(post.title)
            if new_slug != post.slug:
                # Check for slug uniqueness
                base_slug = new_slug
                slug = base_slug
                counter = 1
                while Post.objects.filter(slug=slug).exclude(pk=post.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                post.slug = slug
            
            post.save()
            
            if needs_review:
                messages.add_message(
                    request, messages.SUCCESS,
                    'Your changes were saved and sent for review. The post will be reviewed before being published again.'
                )
            else:
                messages.add_message(
                    request, messages.SUCCESS,
                    'Post updated successfully!'
                )
            
            # Redirect based on status
            if post.status == 1:
                return redirect('post_detail', slug=post.slug)
            else:
                return redirect('home')
    else:
        form = PostForm(instance=post)

    return render(
        request,
        'blog/edit_post.html',
        {'form': form, 'post': post},
    )


@login_required
def delete_post(request, slug):
    """
    View function for soft-deleting a blog post.

    This view allows post authors to soft-delete their own posts.
    It requires user authentication and ensures only the author or staff can delete.
    Uses soft delete (is_deleted=True) instead of hard delete.
    """
    post = get_object_or_404(Post, slug=slug)
    
    # Check if user is the author or staff
    if request.user != post.author and not request.user.is_staff:
        messages.add_message(
            request, messages.ERROR,
            'You can only delete your own posts!'
        )
        return redirect('post_detail', slug=slug)
    
    if request.method == "POST":
        # Soft delete: set flags instead of actually deleting
        post.is_deleted = True
        post.deleted_at = timezone.now()
        post.deleted_by = request.user
        post.save()
        
        messages.add_message(
            request, messages.SUCCESS,
            'Post deleted successfully!'
        )
        return redirect('home')
    
    return render(
        request,
        'blog/delete_post.html',
        {'post': post},
    )


@login_required
def complete_setup(request):
    """
    View for completing site verification setup.
    Users can accept terms and complete their profile to enable write actions.
    """
    if request.method == 'POST':
        # User accepts terms and completes setup
        if hasattr(request.user, 'profile'):
            if not request.user.profile.is_site_verified:
                from django.utils import timezone
                request.user.profile.is_site_verified = True
                request.user.profile.site_verified_at = timezone.now()
                request.user.profile.save()
                messages.success(
                    request,
                    'حساب کاربری شما با موفقیت فعال شد! اکنون می‌توانید پست و نظر ایجاد کنید.'
                )
                return redirect('home')
        else:
            # Create profile if it doesn't exist
            from .models import UserProfile
            from django.utils import timezone
            profile = UserProfile.objects.create(
                user=request.user,
                is_site_verified=True,
                site_verified_at=timezone.now()
            )
            messages.success(
                request,
                'حساب کاربری شما با موفقیت فعال شد! اکنون می‌توانید پست و نظر ایجاد کنید.'
            )
            return redirect('home')
    
    # Check if already verified
    if hasattr(request.user, 'profile') and request.user.profile.is_site_verified:
        messages.info(request, 'حساب کاربری شما قبلاً فعال شده است.')
        return redirect('home')
    
    return render(request, 'blog/complete_setup.html')


def category_posts(request, category_slug):
    """
    View function for displaying posts filtered by category.
    
    This view shows all published posts in a specific category with pagination.
    """
    category = get_object_or_404(Category, slug=category_slug)
    posts = Post.objects.filter(
        category=category,
        status=1,
        is_deleted=False
    ).select_related('category', 'author').annotate(
        comment_count=Count('comments', filter=Q(comments__approved=True))
    ).order_by('-created_on')
    
    # Pagination: 24 posts per page
    paginator = Paginator(posts, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for navigation
    categories = Category.objects.all().order_by('name')
    
    return render(
        request,
        'blog/category_posts.html',
        {
            'category': category,
            'post_list': page_obj,
            'page_obj': page_obj,
            'categories': categories,
            'is_paginated': page_obj.has_other_pages(),
        }
    )
