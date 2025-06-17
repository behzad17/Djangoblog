from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from .models import Post, Comment, Favorite
from .forms import CommentForm

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
        """
        return Post.objects.filter(status=1).annotate(
            comment_count=Count('comments', filter=Q(comments__approved=True))
        )

#  `post_detail`
def post_detail(request, slug):
    """
    View function for displaying a single blog post and its comments.
    
    This view handles both displaying the post and processing new comments.
    It shows approved comments to all users and unapproved comments to
    the comment author. It also tracks whether the post is in the user's
    favorites.
    """
    queryset = Post.objects.filter(status=1)
    post = get_object_or_404(queryset, slug=slug)
    if request.user.is_authenticated:
        comments = post.comments.filter(
            Q(approved=True) | Q(author=request.user)
        ).order_by("-created_on")
    else:
        comments = post.comments.filter(approved=True).order_by("-created_on")

    comment_count = comments.count()
    is_favorite = Favorite.objects.filter(
        user=request.user, post=post
    ).exists() if request.user.is_authenticated else False

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Comment submitted and awaiting approval'
            )
    else:
        comment_form = CommentForm()

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "comment_count": comment_count,
            "comment_form": comment_form,
            "is_favorite": is_favorite,
        },
    )    

def comment_edit(request, slug, comment_id):
    """
    View function for editing an existing comment.
    
    This view allows users to edit their own comments. The edited comment
    will need to be re-approved by an admin. Only the original author
    can edit their comments.
    """
    queryset = Post.objects.filter(status=1)
    post = get_object_or_404(queryset, slug=slug)
    comment = get_object_or_404(Comment, pk=comment_id)

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST, instance=comment)

        if comment_form.is_valid() and comment.author == request.user:
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.approved = False
            comment.save()
            messages.add_message(request, messages.SUCCESS, 'Comment Updated!')
        else:
            messages.add_message(
                request, messages.ERROR,
                'Error updating comment!'
            )

        return HttpResponseRedirect(reverse('post_detail', args=[slug]))

    else:  # Handle GET request for displaying the edit form
        comment_form = CommentForm(instance=comment)

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "comment_form": comment_form,  # Pass the form to the template
            "comments": post.comments.filter(approved=True).order_by(
                "-created_on"
            ),  # Ensure comments are still displayed
            "comment_count": post.comments.filter(approved=True).count(),
            "is_editing": True,  # A flag to indicate that we are in edit mode
            "comment_to_edit": comment,  # The specific comment being edited
        },
    )

def comment_delete(request, slug, comment_id):
    """
    View function for deleting a comment.
    
    This view allows users to delete their own comments. Only the original
    author can delete their comments.
    """
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author == request.user:
        comment.delete()
        messages.add_message(request, messages.SUCCESS, 'Comment deleted!')
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

    return redirect(request.META.get('HTTP_REFERER', 'favorites'))

@login_required
def favorite_posts(request):
    """
    View function for displaying a user's favorite posts.
    
    This view shows all posts that the current user has marked as favorites.
    The view requires user authentication.
    """
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'blog/favorites.html', {'favorites': favorites})

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

    return redirect(request.META.get('HTTP_REFERER', 'favorites'))         
     