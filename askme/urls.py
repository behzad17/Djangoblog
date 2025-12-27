"""
URL patterns for the Ask Me Q&A system.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ask_me, name='ask_me'),
    path('expert/<slug:slug>/', views.expert_profile, name='expert_profile'),
    path('moderator/<int:moderator_id>/ask/', views.ask_question, name='ask_question'),
    path('question/<int:question_id>/answer/', views.answer_question, name='answer_question'),
    path('my-questions/', views.my_questions, name='my_questions'),
    path('moderator/dashboard/', views.moderator_dashboard, name='moderator_dashboard'),
]

