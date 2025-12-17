from django import forms
from .models import Ad, AdCategory


class AdForm(forms.ModelForm):
    """Form for creating/editing ads by users."""
    
    class Meta:
        model = Ad
        fields = ['title', 'category', 'image', 'target_url', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان تبلیغ'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'target_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'title': 'عنوان تبلیغ',
            'category': 'دسته‌بندی',
            'image': 'تصویر تبلیغ',
            'target_url': 'لینک مقصد',
            'start_date': 'تاریخ شروع (اختیاری)',
            'end_date': 'تاریخ پایان (اختیاری)',
        }
        help_texts = {
            'target_url': 'آدرس وب‌سایتی که با کلیک روی تبلیغ باز می‌شود',
            'start_date': 'تاریخ شروع نمایش تبلیغ (اختیاری)',
            'end_date': 'تاریخ پایان نمایش تبلیغ (اختیاری)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure all categories are available
        self.fields['category'].queryset = AdCategory.objects.all().order_by('name')
        # Make start_date and end_date optional
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False

