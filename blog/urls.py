from . import views
from django.urls import path

urlpatterns = [
    path('', views.PostList.as_view(), name='home'),
    path('category/<slug:category_slug>/', views.category_posts, name='category_posts'),
    path('create-post/', views.create_post, name='create_post'),
    path('favorites/', views.favorite_posts, name='favorites'),
    path('add-to-favorites/<int:post_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove-from-favorites/<int:post_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('complete-setup/', views.complete_setup, name='complete_setup'),
    path('<slug:slug>/', views.post_detail, name='post_detail'),
    path('<slug:slug>/edit/', views.edit_post, name='edit_post'),
    path('<slug:slug>/delete/', views.delete_post, name='delete_post'),
    path('<slug:slug>/edit_comment/<int:comment_id>/', views.comment_edit, name='comment_edit'),
    path('<slug:slug>/delete_comment/<int:comment_id>', views.comment_delete, name='comment_delete'),
]
