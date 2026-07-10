from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from community.models import Reply

REPLY_BODY_MIN_LENGTH = 5
REPLY_BODY_MAX_LENGTH = 5000

REPLY_BODY_WIDGET_ATTRS = {
    'class': 'form-control',
    'placeholder': _('پاسخ خود را بنویسید'),
    'aria-label': _('متن پاسخ'),
    'autocomplete': 'off',
    'rows': 5,
}


class ReplyCreateForm(forms.ModelForm):
    """Form for creating a reply to a community discussion."""

    class Meta:
        model = Reply
        fields = ('body',)
        labels = {
            'body': _('پاسخ'),
        }
        help_texts = {
            'body': _('پاسخ خود را شفاف و مفید بنویسید.'),
        }
        widgets = {
            'body': forms.Textarea(attrs=REPLY_BODY_WIDGET_ATTRS),
        }

    def clean_body(self):
        body = (self.cleaned_data.get('body') or '').strip()
        if not body:
            raise ValidationError(_('متن پاسخ الزامی است.'))
        if len(body) < REPLY_BODY_MIN_LENGTH:
            raise ValidationError(
                _('پاسخ باید حداقل %(min)s کاراکتر باشد.'),
                params={'min': REPLY_BODY_MIN_LENGTH},
            )
        if len(body) > REPLY_BODY_MAX_LENGTH:
            raise ValidationError(
                _('پاسخ نباید بیشتر از %(max)s کاراکتر باشد.'),
                params={'max': REPLY_BODY_MAX_LENGTH},
            )
        return body
