from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404, reverse, redirect 
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from .models import Post, Comment, Favorite
from .forms import CommentForm

class PostList(generic.ListView):
    template_name = "blog/index.html"
    paginate_by = 8

    def get_queryset(self):
        return Post.objects.filter(status=1).annotate(comment_count=Count('comments', filter=Q(comments__approved=True)))

#  `post_detail`
def post_detail(request, slug):
    queryset = Post.objects.filter(status=1)
    post = get_object_or_404(queryset, slug=slug)
    #comments = post.comments.filter(approved=True).order_by("-created_on")
    if request.user.is_authenticated:
        comments = post.comments.filter(Q(approved=True) | Q(author=request.user)).order_by("-created_on")
    else:
        comments = post.comments.filter(approved=True).order_by("-created_on")

    comment_count = comments.count()
    is_favorite = Favorite.objects.filter(user=request.user, post=post).exists() if request.user.is_authenticated else False

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            messages.add_message(request, messages.SUCCESS, 'Comment submitted and awaiting approval')
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
    view to edit comments
    """
    if request.method == "POST":

        queryset = Post.objects.filter(status=1)
        post = get_object_or_404(queryset, slug=slug)
        comment = get_object_or_404(Comment, pk=comment_id)
        comment_form = CommentForm(data=request.POST, instance=comment)

        if comment_form.is_valid() and comment.author == request.user:
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.approved = False
            comment.save()
            messages.add_message(request, messages.SUCCESS, 'Comment Updated!')
        else:
            messages.add_message(request, messages.ERROR, 'Error updating comment!')

    return HttpResponseRedirect(reverse('post_detail', args=[slug]))

def comment_delete(request, slug, comment_id):
    """
    view to delete comment
    """
    queryset = Post.objects.filter(status=1)
    post = get_object_or_404(queryset, slug=slug)
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author == request.user:
        comment.delete()
        messages.add_message(request, messages.SUCCESS, 'Comment deleted!')
    else:
        messages.add_message(request, messages.ERROR, 'You can only delete your own comments!')

    return HttpResponseRedirect(reverse('post_detail', args=[slug]))

@login_required
def add_to_favorites(request, post_id):
    """
    add or delete a post from Favorites
    """
    post = get_object_or_404(Post, id=post_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, post=post)

    if not created:
        favorite.delete()  # delete if a post is saved before

    return redirect(request.META.get('HTTP_REFERER', 'favorites'))

@login_required
def favorite_posts(request):
    """
    show pots list
    """
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'blog/favorites.html', {'favorites': favorites})

@login_required
def remove_from_favorites(request, post_id):
    """ 
    remove a favorite
    """
    post = get_object_or_404(Post, id=post_id)
    favorite = Favorite.objects.filter(user=request.user, post=post)

    if favorite.exists():
        favorite.delete()

    return redirect(request.META.get('HTTP_REFERER', 'favorites'))         
     