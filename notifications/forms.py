from django import forms

from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    """Account settings form for Peyvand notification preferences."""

    class Meta:
        model = NotificationPreference
        fields = (
            'askme_emails',
            'ad_emails',
            'favorite_notifications',
            'weekly_digest',
        )
        labels = {
            'askme_emails': 'ایمیل پاسخ متخصص (پرسش و پاسخ)',
            'ad_emails': 'ایمیل‌های مربوط به آگهی',
            'favorite_notifications': 'اعلان علاقه‌مندی به آگهی',
            'weekly_digest': 'خبرنامه هفتگی',
        }
        help_texts = {
            'askme_emails': 'وقتی یک متخصص به سوال شما پاسخ دهد.',
            'ad_emails': 'تایید، رد، ارتقا به Pro و هشدار انقضای آگهی.',
            'favorite_notifications': 'فقط درون‌برنامه‌ای؛ وقتی آگهی شما به علاقه‌مندی‌ها اضافه شود.',
            'weekly_digest': 'خلاصه هفتگی فعالیت پیوند؛ فقط ایمیل.',
        }
        widgets = {
            'askme_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ad_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'favorite_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'weekly_digest': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
