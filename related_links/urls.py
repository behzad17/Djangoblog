from django.urls import path
from . import views

app_name = 'related_links'

urlpatterns = [
    path('', views.links_list, name='links_list'),
]

