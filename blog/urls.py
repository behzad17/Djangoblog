from . import views
from . import views_search
from django.urls import path

urlpatterns = [
    path('', views.PostList.as_view(), name='home'),
    path('search/', views_search.search_posts, name='search'),
    path('category/<slug:category_slug>/', views.category_posts, name='category_posts'),
    path('create-post/', views.create_post, name='create_post'),
    path('favorites/', views.favorite_posts, name='favorites'),
    path('add-to-favorites/<int:post_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove-from-favorites/<int:post_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('complete-setup/', views.complete_setup, name='complete_setup'),
    # Use str instead of slug to allow Unicode characters (Persian/Farsi)
    path('<str:slug>/', views.post_detail, name='post_detail'),
    path('<str:slug>/edit/', views.edit_post, name='edit_post'),
    path('<str:slug>/delete/', views.delete_post, name='delete_post'),
    path('<str:slug>/edit_comment/<int:comment_id>/', views.comment_edit, name='comment_edit'),
    path('<str:slug>/delete_comment/<int:comment_id>', views.comment_delete, name='comment_delete'),
]
