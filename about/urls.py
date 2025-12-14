from . import views
from django.urls import path

urlpatterns = [
    path('', views.about_me, name='about'),
    path('terms/', views.terms_and_conditions, name='terms'),
    path('member-guide/', views.member_guide, name='member_guide'),
]
