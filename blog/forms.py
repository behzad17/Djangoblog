from .models import Comment, Post
from django import forms


class PostForm(forms.ModelForm):
    """
    A form for creating and editing blog posts.
    
    This form allows users to create new blog posts with title, content,
    excerpt, and featured image. It uses Summernote for rich text editing.
    """
    class Meta:
        """Meta options for PostForm."""
        model = Post
        fields = ('title', 'excerpt', 'content', 'featured_image', 'status')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    """
    A form for creating and editing comments.
    
    This form is used for both creating new comments and editing existing ones.
    It includes a textarea widget for the comment body with custom styling.
    """
    class Meta:
        """Meta options for CommentForm."""
        model = Comment
        fields = ('body',)
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5, 'style': 'height:100px;'})
        }
