from . import views
from django.urls import path

urlpatterns = [
    path('', views.PostList.as_view(), name='home'),
    path('favorites/', views.favorite_posts, name='favorites'),
    path('add-to-favorites/<int:post_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove-from-favorites/<int:post_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('<slug:slug>/', views.post_detail, name='post_detail'),
    path('<slug:slug>/edit_comment/<int:comment_id>', views.comment_edit, name='comment_edit'),
    path('<slug:slug>/delete_comment/<int:comment_id>', views.comment_delete, name='comment_delete'),          
]
