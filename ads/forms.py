from django import forms
from django.core.exceptions import ValidationError
from PIL import Image
from .models import Ad, AdCategory


class AdForm(forms.ModelForm):
    """Form for creating/editing ads by users."""
    
    class Meta:
        model = Ad
        fields = ['title', 'category', 'image', 'target_url', 'city', 'start_date', 'end_date']
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
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شهر'
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
            'city': 'شهر',
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
    
    def clean_image(self):
        """Validate uploaded image file size and type."""
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if hasattr(image, 'size') and image.size > max_size:
                raise ValidationError('Image file size must be 5MB or less.')
            
            # Verify it's a valid image using Pillow
            try:
                image.seek(0)
                img = Image.open(image)
                img.verify()
                # verify() closes the file, so reopen it for Django to use
                image.seek(0)
                img = Image.open(image)
                img.load()
                image.seek(0)
            except Exception:
                raise ValidationError('Please upload a valid image file.')
        
        return image

