from django.urls import path

from community.views.health import health_check

app_name = 'community'

urlpatterns = [
    path('health/', health_check, name='health'),
]
