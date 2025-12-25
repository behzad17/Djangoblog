from django.urls import path
from . import views

app_name = "ads"

urlpatterns = [
    path("", views.ad_category_list, name="ads_home"),
    path("category/<slug:category_slug>/", views.ad_list_by_category, name="ads_by_category"),
    path("ad/<slug:slug>/", views.ad_detail, name="ad_detail"),
    # User ad management
    path("create/", views.create_ad, name="create_ad"),
    path("my-ads/", views.my_ads, name="my_ads"),
    path("edit/<slug:slug>/", views.edit_ad, name="edit_ad"),
    path("delete/<slug:slug>/", views.delete_ad, name="delete_ad"),
    # Favorites
    path("add-to-favorites/<int:ad_id>/", views.add_ad_to_favorites, name="add_ad_to_favorites"),
]


