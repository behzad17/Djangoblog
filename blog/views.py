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
from ratelimit.decorators import ratelimit
from django.utils.text import slugify
import json

from .models import Post, Comment, Favorite, Category
from .forms import CommentForm, PostForm


class PostList(generic.ListView):
    """
    A view that displays a list of published blog posts.

    This view inherits from Django's generic ListView and displays posts
    that have been published (status=1). It includes a count of approved
    comments for each post.
    """
    template_name = "blog/index.html"
    paginate_by = 8

    def get_queryset(self):
        """
        Returns a queryset of published posts with comment counts.
        Posts are ordered by creation date (newest first).
        """
        return Post.objects.filter(status=1).select_related('category').annotate(
            comment_count=Count('comments', filter=Q(comments__approved=True))
        ).order_by('-created_on')
    
    def get_context_data(self, **kwargs):
        """
        Add categories to the context for display in template.
        """
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('name')
        return context


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def post_detail(request, slug):
    """
    View function for displaying a single blog post and its comments.

    This view handles both displaying the post and processing new comments.
    It shows approved comments to all users and unapproved comments to
    the comment author. It also tracks whether the post is in the user's
    favorites.
    """
    queryset = Post.objects.filter(status=1).select_related('category', 'author')
    post = get_object_or_404(queryset, slug=slug)
    comments = post.comments.all().order_by("-created_on")
    comment_count = post.comments.count()
    comment_form = CommentForm()
    # Determine if current user has already favorited this post
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(
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

        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.post = post
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
                })

            messages.add_message(
                request, messages.SUCCESS,
                'Comment submitted successfully!'
            )
            return redirect('post_detail', slug=post.slug)

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "comment_count": comment_count,
            "comment_form": comment_form,
            "is_favorited": is_favorited,
        },
    )


@login_required
def comment_edit(request, slug, comment_id):
    """
    View function for editing a comment.

    This view handles both GET and POST requests for editing comments.
    It ensures that only the comment author can edit their comments.
    """
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user == comment.author:
        if request.method == "POST":
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                try:
                    data = json.loads(request.body)
                    comment.body = data.get('body')
                    comment.save()
                    return JsonResponse({
                        'status': 'success',
                        'body': comment.body
                    })
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid request data'
                    }, status=400)
            else:
                form = CommentForm(request.POST, instance=comment)
                if form.is_valid():
                    form.save()
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
    View function for displaying a user's favorite posts.

    This view shows all posts that the current user has marked as favorites.
    The view requires user authentication.
    """
    favorites = Favorite.objects.filter(user=request.user)
    return render(
        request,
        'blog/favorites.html',
        {'favorites': favorites},
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
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            post.slug = slug
            # Always set status to Draft (0) - only admins can publish
            post.status = 0
            # URL approval defaults to False - admin must approve
            if post.external_url:
                post.url_approved = False
            post.save()
            
            # Show pending message with better styling
            url_message = ''
            if post.external_url:
                url_message = ' If you added an external URL, it will also be reviewed and approved by an administrator before being displayed.'
            
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
def edit_post(request, slug):
    """
    View function for editing a blog post.

    This view allows post authors to edit their own posts.
    It requires user authentication and ensures only the author can edit.
    """
    post = get_object_or_404(Post, slug=slug)
    
    # Check if user is the author
    if request.user != post.author:
        messages.add_message(
            request, messages.ERROR,
            'You can only edit your own posts!'
        )
        return redirect('post_detail', slug=slug)
    
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            # Preserve original status - users cannot change publication status
            original_status = Post.objects.get(pk=post.pk).status
            post.status = original_status
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
    View function for deleting a blog post.

    This view allows post authors to delete their own posts.
    It requires user authentication and ensures only the author can delete.
    """
    post = get_object_or_404(Post, slug=slug)
    
    # Check if user is the author
    if request.user != post.author:
        messages.add_message(
            request, messages.ERROR,
            'You can only delete your own posts!'
        )
        return redirect('post_detail', slug=slug)
    
    if request.method == "POST":
        post.delete()
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


def category_posts(request, category_slug):
    """
    View function for displaying posts filtered by category.
    
    This view shows all published posts in a specific category.
    """
    category = get_object_or_404(Category, slug=category_slug)
    posts = Post.objects.filter(
        category=category,
        status=1
    ).select_related('category', 'author').annotate(
        comment_count=Count('comments', filter=Q(comments__approved=True))
    ).order_by('-created_on')
    
    # Get all categories for navigation
    categories = Category.objects.all().order_by('name')
    
    return render(
        request,
        'blog/category_posts.html',
        {
            'category': category,
            'post_list': posts,
            'categories': categories,
        }
    )
