"""
Views for the Ask Me Q&A system.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from ratelimit.decorators import ratelimit
from blog.decorators import site_verified_required
from .models import Moderator, Question
from .forms import QuestionForm, AnswerForm


def ask_me(request):
    """
    Display list of all active moderators.
    Public view - anyone can see moderators, but only authenticated users can ask questions.
    """
    try:
        moderators = Moderator.objects.filter(is_active=True).select_related('user')
    except Exception:
        moderators = []
    
    # Count answered questions for notification badge (only for authenticated users)
    answered_count = 0
    if request.user.is_authenticated:
        try:
            answered_count = Question.objects.filter(
                user=request.user,
                answered=True
            ).count()
        except Exception:
            answered_count = 0
    
    return render(
        request,
        'askme/ask_me.html',
        {
            'moderators': moderators,
            'answered_count': answered_count
        }
    )


@ratelimit(key='user', rate='10/h', method='POST', block=True)
@ratelimit(key='ip', rate='20/h', method='POST', block=True)
@site_verified_required
@login_required
def ask_question(request, moderator_id):
    """
    Handle question submission via AJAX or form POST.
    Only authenticated users can ask questions.
    """
    moderator = get_object_or_404(Moderator, id=moderator_id, is_active=True)
    
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            question.moderator = moderator
            question.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Your question has been submitted successfully! The moderator will respond soon.'
                })
            
            messages.success(request, 'Your question has been submitted successfully! The moderator will respond soon.')
            return redirect('ask_me')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
    
    # GET request - return form (for modal or separate page)
    form = QuestionForm()
    return render(
        request,
        'askme/question_form.html',
        {'form': form, 'moderator': moderator}
    )


@login_required
def answer_question(request, question_id):
    """
    Allow moderator to answer a question.
    Only the assigned moderator can answer their questions.
    """
    question = get_object_or_404(Question, id=question_id)
    
    # Check if user is the assigned moderator
    if not hasattr(request.user, 'moderator_profile') or \
       request.user.moderator_profile != question.moderator:
        messages.error(request, 'You are not authorized to answer this question.')
        return redirect('ask_me')
    
    if request.method == "POST":
        form = AnswerForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save(commit=False)
            question.answered = True
            question.answered_on = timezone.now()
            question.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Answer submitted successfully!'
                })
            
            messages.success(request, 'Answer submitted successfully!')
            return redirect('moderator_dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
    
    form = AnswerForm(instance=question)
    return render(
        request,
        'askme/answer_form.html',
        {'form': form, 'question': question}
    )


@login_required
def my_questions(request):
    """
    Display all questions asked by the current user.
    Users can only see their own questions.
    """
    questions = Question.objects.filter(
        user=request.user
    ).select_related('moderator', 'moderator__user').order_by('-created_on')
    
    return render(
        request,
        'askme/my_questions.html',
        {'questions': questions}
    )


@login_required
def moderator_dashboard(request):
    """
    Display all questions assigned to the current moderator.
    Moderators can only see questions assigned to them.
    """
    if not hasattr(request.user, 'moderator_profile'):
        messages.error(request, 'You are not a moderator.')
        return redirect('ask_me')
    
    moderator = request.user.moderator_profile
    
    # Get all questions for this moderator
    all_questions = Question.objects.filter(
        moderator=moderator
    ).select_related('user').order_by('-created_on')
    
    # Separate answered and pending
    answered_questions = all_questions.filter(answered=True)
    pending_questions = all_questions.filter(answered=False)
    
    # Statistics
    stats = {
        'total': all_questions.count(),
        'answered': answered_questions.count(),
        'pending': pending_questions.count(),
    }
    
    return render(
        request,
        'askme/moderator_dashboard.html',
        {
            'questions': all_questions,
            'answered_questions': answered_questions,
            'pending_questions': pending_questions,
            'moderator': moderator,
            'stats': stats
        }
    )
