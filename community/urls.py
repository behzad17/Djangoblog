from django.urls import path

from community.views.discussions import (
    community_home,
    discussion_close,
    discussion_create,
    discussion_detail,
    discussion_list,
    discussion_reply,
)
from community.views.health import health_check
from community.views.search import community_search

app_name = 'community'

urlpatterns = [
    path('', community_home, name='home'),
    path('discussions/', discussion_list, name='discussion_list'),
    path('discussions/create/', discussion_create, name='discussion_create'),
    path('discussions/<str:slug>/', discussion_detail, name='discussion_detail'),
    path('discussions/<str:slug>/reply/', discussion_reply, name='discussion_reply'),
    path('discussions/<str:slug>/close/', discussion_close, name='discussion_close'),
    path('search/', community_search, name='search'),
    path('health/', health_check, name='health'),
]
