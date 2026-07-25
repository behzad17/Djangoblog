from django.urls import path

from content_ai.views import sandbox

app_name = 'content_ai'

urlpatterns = [
    path('sandbox/', sandbox, name='sandbox'),
]
