from django import forms
from django.core.exceptions import ValidationError
from PIL import Image
from .models import Ad, AdCategory, AdComment


class AdForm(forms.ModelForm):
    """Form for creating/editing ads by users."""
    
    class Meta:
        model = Ad
        fields = [
            'title', 'category', 'image', 'extra_image_1', 'extra_image_2', 'target_url', 'city', 'address', 'phone',
            'instagram_url', 'telegram_url', 'website_url',
            'start_date', 'end_date'
        ]
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
            'extra_image_1': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'extra_image_2': forms.FileInput(attrs={
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
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'آدرس کامل',
                'rows': 3
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تماس'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/username'
            }),
            'telegram_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://t.me/channel'
            }),
            'website_url': forms.URLInput(attrs={
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
            'extra_image_1': 'تصویر اضافی ۱ (اختیاری)',
            'extra_image_2': 'تصویر اضافی ۲ (اختیاری)',
            'target_url': 'لینک مقصد',
            'city': 'شهر',
            'address': 'آدرس کامل',
            'phone': 'شماره تماس',
            'instagram_url': 'لینک اینستاگرام',
            'telegram_url': 'لینک تلگرام',
            'website_url': 'لینک وب‌سایت',
            'start_date': 'تاریخ شروع (اختیاری)',
            'end_date': 'تاریخ پایان (اختیاری)',
        }
        help_texts = {
            'target_url': 'آدرس وب‌سایتی که با کلیک روی تبلیغ باز می‌شود',
            'extra_image_1': 'تصویر اضافی اول (اختیاری - حداکثر 5MB)',
            'extra_image_2': 'تصویر اضافی دوم (اختیاری - حداکثر 5MB)',
            'address': 'آدرس کامل محل کسب‌وکار یا ارائه خدمات',
            'phone': 'شماره تماس (اختیاری)',
            'instagram_url': 'لینک پروفایل یا صفحه اینستاگرام (اختیاری)',
            'telegram_url': 'لینک کانال یا گروه تلگرام (اختیاری)',
            'website_url': 'لینک وب‌سایت (اختیاری)',
            'start_date': 'تاریخ شروع نمایش تبلیغ (اختیاری)',
            'end_date': 'تاریخ پایان نمایش تبلیغ (اختیاری)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure all categories are available
        self.fields['category'].queryset = AdCategory.objects.all().order_by('name')
        # Make optional fields not required
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False
        # city and address are now required
        self.fields['phone'].required = False
        self.fields['instagram_url'].required = False
        self.fields['telegram_url'].required = False
        self.fields['website_url'].required = False
        self.fields['extra_image_1'].required = False
        self.fields['extra_image_2'].required = False
    
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
    
    def _validate_image_file(self, image):
        """Helper method to validate image file size and type."""
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
    
    def clean_extra_image_1(self):
        """Validate uploaded extra image 1 file size and type."""
        image = self.cleaned_data.get('extra_image_1')
        return self._validate_image_file(image)
    
    def clean_extra_image_2(self):
        """Validate uploaded extra image 2 file size and type."""
        image = self.cleaned_data.get('extra_image_2')
        return self._validate_image_file(image)
    
    def clean_address(self):
        """Sanitize address field by stripping whitespace."""
        address = self.cleaned_data.get('address')
        if address:
            address = address.strip()
        return address
    
    def clean_city(self):
        """Sanitize city field by stripping whitespace."""
        city = self.cleaned_data.get('city')
        if city:
            city = city.strip()
        return city
    
    def clean_phone(self):
        """Sanitize phone field by stripping whitespace."""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
        return phone
    
    def clean_instagram_url(self):
        """Validate Instagram URL format."""
        url = self.cleaned_data.get('instagram_url')
        if url:
            url = url.strip()
            # Basic validation - URLField already validates URL format
            if not url.startswith(('http://', 'https://')):
                raise ValidationError('لینک باید با http:// یا https:// شروع شود.')
        return url
    
    def clean_telegram_url(self):
        """Validate Telegram URL format."""
        url = self.cleaned_data.get('telegram_url')
        if url:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                raise ValidationError('لینک باید با http:// یا https:// شروع شود.')
        return url
    
    def clean_website_url(self):
        """Validate website URL format."""
        url = self.cleaned_data.get('website_url')
        if url:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                raise ValidationError('لینک باید با http:// یا https:// شروع شود.')
        return url


class AdCommentForm(forms.ModelForm):
    """
    A form for creating comments on advertisements.
    
    Ad comments are published immediately (no moderation).
    Includes honeypot field for spam protection and HTML sanitization.
    """
    honeypot = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'tabindex': '-1',
            'aria-hidden': 'true',
            'style': 'position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;'
        })
    )

    class Meta:
        """Meta options for AdCommentForm."""
        model = AdComment
        fields = ('body', 'honeypot')
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 5,
                'style': 'height:100px;',
                'class': 'form-control',
                'placeholder': 'نظر خود را بنویسید...',
                'maxlength': '2000'
            })
        }
        labels = {
            'body': 'نظر'
        }

    def clean_honeypot(self):
        """Detect bot submissions via honeypot field."""
        data = self.cleaned_data.get('honeypot')
        if data:
            raise ValidationError("Bot detected.")
        return data
    
    def clean_body(self):
        """Sanitize comment body to prevent XSS and enforce max length."""
        body = self.cleaned_data.get('body')
        if not body:
            raise ValidationError('نظر نمی‌تواند خالی باشد.')
        
        # Enforce max length (2000 characters)
        if len(body) > 2000:
            raise ValidationError('نظر نمی‌تواند بیشتر از ۲۰۰۰ کاراکتر باشد.')
        
        # Sanitize HTML to prevent XSS
        from blog.utils import sanitize_html
        body = sanitize_html(body)
        
        # Strip whitespace
        body = body.strip()
        
        if not body:
            raise ValidationError('نظر نمی‌تواند خالی باشد.')
        
        return body


class AdFilterForm(forms.Form):
    """
    Form for filtering ads by city and sorting by date.
    Used in ads category listing page.
    """
    city = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='شهر',
    )
    
    sort = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='مرتب‌سازی',
        choices=[
            ('newest', 'جدیدترین'),
            ('oldest', 'قدیمی‌ترین'),
        ],
        initial='newest',
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic city choices."""
        city_choices = kwargs.pop('city_choices', [])
        super().__init__(*args, **kwargs)
        
        # Set city choices (empty option + available cities)
        city_field_choices = [('', 'همه شهرها')]
        city_field_choices.extend([(city, city) for city in city_choices])
        self.fields['city'].choices = city_field_choices


class ProRequestForm(forms.Form):
    """
    Form for requesting Pro upgrade for an ad.
    Only requires phone number.
    """
    phone = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'شماره تماس',
            'type': 'tel',
        }),
        label='شماره تماس',
        help_text='شماره تماس خود را وارد کنید',
    )
    
    def clean_phone(self):
        """Validate and sanitize phone number."""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            # Basic validation - ensure it's not empty after strip
            if not phone:
                raise ValidationError('شماره تماس نمی‌تواند خالی باشد.')
            # Optional: Add format validation (e.g., digits, length)
            # For now, keep it simple
        return phone

