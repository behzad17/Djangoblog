from .models import Comment, Post, Category
from django import forms
from django.core.exceptions import ValidationError


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
    
    class Meta:
        """Meta options for PostForm."""
        model = Post
        fields = ('title', 'excerpt', 'content', 'featured_image', 'category', 'external_url')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
        }


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
