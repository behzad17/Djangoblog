"""
URL configuration for accounts app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path("settings/", views.account_settings, name="account_settings"),
]

