from django.urls import path

from content_ai.api import create_editorial_draft

app_name = 'content_ai_api'

urlpatterns = [
    path(
        'editorial/draft/',
        create_editorial_draft,
        name='editorial_draft',
    ),
]
