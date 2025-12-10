"""
URL configuration for codestar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from ratelimit.decorators import ratelimit
from allauth.account import views as allauth_views


urlpatterns = [
    path("about/", include("about.urls"), name="about-urls"),
    # Rate-limit login and signup endpoints (5 requests per minute per IP)
    path(
        "accounts/login/",
        ratelimit(key="ip", rate="5/m", block=True)(allauth_views.login),
        name="account_login",
    ),
    path(
        "accounts/signup/",
        ratelimit(key="ip", rate="5/m", block=True)(allauth_views.signup),
        name="account_signup",
    ),
    path("accounts/", include("allauth.urls")),
    path("captcha/", include("captcha.urls")),
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    path("", include("blog.urls"), name="blog-urls"),
]
