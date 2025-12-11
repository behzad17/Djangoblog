"""
Forms for the Ask Me Q&A system.
"""

from django import forms
from .models import Question


class QuestionForm(forms.ModelForm):
    """Form for submitting a question to a moderator."""
    
    class Meta:
        model = Question
        fields = ('question_text',)
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Ask your question here...',
                'required': True
            })
        }
        labels = {
            'question_text': 'Your Question'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['question_text'].required = True


class AnswerForm(forms.ModelForm):
    """Form for moderators to answer questions."""
    
    class Meta:
        model = Question
        fields = ('answer_text',)
        widgets = {
            'answer_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Provide your answer here...',
                'required': True
            })
        }
        labels = {
            'answer_text': 'Your Answer'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['answer_text'].required = True

