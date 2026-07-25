from django.urls import path

from content_ai.editorial_studio.views import (
    editorial_studio,
    editorial_studio_import,
)
from content_ai.studio.views import ai_studio, studio_api
from content_ai.views import sandbox
from content_ai.workspace.views import editorial_workspace, workspace_api

app_name = 'content_ai'

urlpatterns = [
    path('sandbox/', sandbox, name='sandbox'),
    path('workspace/', editorial_workspace, name='editorial_workspace'),
    path(
        'workspace/api/<slug:action>/',
        workspace_api,
        name='workspace_api',
    ),
    path('studio/', ai_studio, name='ai_studio'),
    path(
        'studio/api/<slug:action>/',
        studio_api,
        name='studio_api',
    ),
    path(
        'editorial-studio/',
        editorial_studio,
        name='editorial_studio',
    ),
    path(
        'editorial-studio/import/',
        editorial_studio_import,
        name='editorial_studio_import',
    ),
]
