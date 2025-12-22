from .models import Comment, Post, Category
from django import forms
from django.core.exceptions import ValidationError
from .utils import sanitize_html


class PostForm(forms.ModelForm):
    """
    A form for creating and editing blog posts.
    
    This form allows users to create new blog posts with title, content,
    excerpt, and featured image. It uses Summernote for rich text editing.
    Note: Status field is excluded - only admins can publish posts.
    Category is mandatory for all posts.
    """
    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by('name'),
        required=True,
        empty_label="-- Select a Category --",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Category',
        help_text='Please select a category for your post (required)'
    )
    
    external_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com (optional - requires admin approval)'
        }),
        label='External URL',
        help_text='Optional: Add an external URL. It will be reviewed and approved by admin before being displayed.'
    )
    
    # Event date fields (optional, required only for Events category)
    event_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_event_start_date'
        }),
        label='Event Start Date',
        help_text='Required for Events category'
    )
    event_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_event_end_date'
        }),
        label='Event End Date',
        help_text='Required for Events category'
    )
    
    class Meta:
        """Meta options for PostForm."""
        model = Post
        fields = ('title', 'excerpt', 'content', 'featured_image', 'category', 'external_url', 'event_start_date', 'event_end_date')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """Validate event dates are required for Events category and end date is after start date."""
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        event_start_date = cleaned_data.get('event_start_date')
        event_end_date = cleaned_data.get('event_end_date')
        
        # Validate dates are required for Events category
        if category and category.slug == 'events-announcements':
            if not event_start_date:
                raise ValidationError({
                    'event_start_date': 'Start date is required for Events category.'
                })
            if not event_end_date:
                raise ValidationError({
                    'event_end_date': 'End date is required for Events category.'
                })
            # Validate end date is after or equal to start date
            if event_start_date and event_end_date:
                if event_end_date < event_start_date:
                    raise ValidationError({
                        'event_end_date': 'End date must be on or after start date.'
                    })
        
        # Sanitize HTML content to prevent XSS
        if 'content' in cleaned_data and cleaned_data.get('content'):
            cleaned_data['content'] = sanitize_html(cleaned_data['content'])
        
        # Sanitize excerpt if it contains HTML
        if 'excerpt' in cleaned_data and cleaned_data.get('excerpt'):
            cleaned_data['excerpt'] = sanitize_html(cleaned_data['excerpt'])
        
        return cleaned_data
    
    def clean_featured_image(self):
        """Validate uploaded image file size and type."""
        image = self.cleaned_data.get('featured_image')
        if image:
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if hasattr(image, 'size') and image.size > max_size:
                raise ValidationError('Image file too large. Maximum size is 5MB.')
            
            # Check file type by content type
            if hasattr(image, 'content_type'):
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
                if image.content_type not in allowed_types:
                    raise ValidationError('Invalid file type. Only JPEG, PNG, WebP, and GIF images are allowed.')
            
            # Check file extension as additional validation
            if hasattr(image, 'name'):
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
                file_ext = image.name.lower()
                if not any(file_ext.endswith(ext) for ext in allowed_extensions):
                    raise ValidationError('Invalid file extension. Only .jpg, .jpeg, .png, .webp, and .gif files are allowed.')
        
        return image


class CommentForm(forms.ModelForm):
    """
    A form for creating and editing comments.
    
    This form is used for both creating new comments and editing existing ones.
    It includes a textarea widget for the comment body with custom styling.
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
        """Meta options for CommentForm."""
        model = Comment
        fields = ('body', 'honeypot')
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5, 'style': 'height:100px;'})
        }

    def clean_honeypot(self):
        data = self.cleaned_data.get('honeypot')
        if data:
            raise ValidationError("Bot detected.")
        return data
    
    def clean_body(self):
        """Sanitize comment body to prevent XSS."""
        body = self.cleaned_data.get('body')
        if body:
            # Comments are plain text, but sanitize just in case
            # Use bleach to strip any HTML tags
            from .utils import sanitize_html
            body = sanitize_html(body)
        return body
