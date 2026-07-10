from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from community.models import CommunityCategory, Discussion

DISCUSSION_TITLE_MAX_LENGTH = 200
DISCUSSION_BODY_MIN_LENGTH = 10
DISCUSSION_BODY_MAX_LENGTH = 10000

TITLE_WIDGET_ATTRS = {
    'class': 'form-control',
    'placeholder': _('عنوان بحث یا سؤال خود را بنویسید'),
    'aria-label': _('عنوان بحث'),
    'autocomplete': 'off',
    'maxlength': str(DISCUSSION_TITLE_MAX_LENGTH),
}

BODY_WIDGET_ATTRS = {
    'class': 'form-control',
    'placeholder': _('جزئیات بحث، سؤال یا درخواست خود را بنویسید'),
    'aria-label': _('متن بحث'),
    'autocomplete': 'off',
    'rows': 8,
}

CATEGORY_WIDGET_ATTRS = {
    'class': 'form-select',
    'aria-label': _('دسته‌بندی'),
}


def _active_category_queryset():
    return CommunityCategory.objects.filter(is_active=True).order_by(
        'display_order',
        'name',
    )


class DiscussionCreateForm(forms.ModelForm):
    """Form for creating a new community discussion."""

    category = forms.ModelChoiceField(
        queryset=CommunityCategory.objects.none(),
        label=_('دسته‌بندی'),
        help_text=_('موضوع بحث خود را انتخاب کنید.'),
        widget=forms.Select(attrs=CATEGORY_WIDGET_ATTRS),
        empty_label=_('-- انتخاب دسته‌بندی --'),
    )

    class Meta:
        model = Discussion
        fields = ('title', 'category', 'body')
        labels = {
            'title': _('عنوان'),
            'body': _('متن بحث'),
        }
        help_texts = {
            'title': _('عنوانی کوتاه و واضح بنویسید.'),
            'body': _('هرچه بیشتر توضیح دهید، پاسخ‌های بهتری دریافت می‌کنید.'),
        }
        widgets = {
            'title': forms.TextInput(attrs=TITLE_WIDGET_ATTRS),
            'body': forms.Textarea(attrs=BODY_WIDGET_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = _active_category_queryset()

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if not title:
            raise ValidationError(_('عنوان الزامی است.'))
        if len(title) > DISCUSSION_TITLE_MAX_LENGTH:
            raise ValidationError(
                _('عنوان نباید بیشتر از %(max)s کاراکتر باشد.'),
                params={'max': DISCUSSION_TITLE_MAX_LENGTH},
            )
        return title

    def clean_body(self):
        body = (self.cleaned_data.get('body') or '').strip()
        if not body:
            raise ValidationError(_('متن بحث الزامی است.'))
        if len(body) < DISCUSSION_BODY_MIN_LENGTH:
            raise ValidationError(
                _('متن بحث باید حداقل %(min)s کاراکتر باشد.'),
                params={'min': DISCUSSION_BODY_MIN_LENGTH},
            )
        if len(body) > DISCUSSION_BODY_MAX_LENGTH:
            raise ValidationError(
                _('متن بحث نباید بیشتر از %(max)s کاراکتر باشد.'),
                params={'max': DISCUSSION_BODY_MAX_LENGTH},
            )
        return body

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category is None:
            raise ValidationError(_('انتخاب دسته‌بندی الزامی است.'))
        if not category.is_active:
            raise ValidationError(_('دسته‌بندی انتخاب‌شده فعال نیست.'))
        return category


class DiscussionUpdateForm(DiscussionCreateForm):
    """Form for updating an existing community discussion."""

    class Meta(DiscussionCreateForm.Meta):
        pass
