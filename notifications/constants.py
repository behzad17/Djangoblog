from django.db import models


class NotificationType(models.TextChoices):
    ASKME_SPECIALIST_ANSWER = 'askme_specialist_answer', 'AskMe specialist answer'
    AD_APPROVED = 'ad_approved', 'Ad approved'
    AD_REJECTED = 'ad_rejected', 'Ad rejected'
    AD_PRO = 'ad_pro', 'Ad upgraded to Pro'
    AD_EXPIRING = 'ad_expiring', 'Ad expiring soon'
    AD_FAVORITED = 'ad_favorited', 'Ad favorited'
    WEEKLY_DIGEST = 'weekly_digest', 'Weekly digest'


# In-app copy used by NotificationService callers in later phases.
IN_APP_MESSAGES = {
    NotificationType.ASKME_SPECIALIST_ANSWER: {
        'title': 'پاسخ متخصص دریافت کردید',
        'message': 'یک متخصص به سوال شما پاسخ داد.',
    },
    NotificationType.AD_APPROVED: {
        'title': 'آگهی شما منتشر شد',
        'message': 'آگهی شما تایید شد.',
    },
    NotificationType.AD_REJECTED: {
        'title': 'آگهی شما تایید نشد',
        'message': 'آگهی شما در وضعیت فعلی قابل انتشار نیست.',
    },
    NotificationType.AD_PRO: {
        'title': 'تبریک! آگهی شما Pro شد',
        'message': 'آگهی شما به Pro ارتقا یافت.',
    },
    NotificationType.AD_EXPIRING: {
        'title': 'آگهی شما به زودی منقضی می‌شود',
        'message': '۷ روز تا پایان اعتبار آگهی شما باقی مانده است.',
    },
    NotificationType.AD_FAVORITED: {
        'title': 'علاقه‌مندی جدید',
        'message': 'آگهی شما به فهرست علاقه‌مندی‌های یک کاربر اضافه شد.',
    },
}

EMAIL_TEMPLATES = {
    NotificationType.ASKME_SPECIALIST_ANSWER: 'specialist_answer',
    NotificationType.AD_APPROVED: 'ad_approved',
    NotificationType.AD_REJECTED: 'ad_rejected',
    NotificationType.AD_PRO: 'ad_pro',
    NotificationType.AD_EXPIRING: 'ad_expiring',
    NotificationType.WEEKLY_DIGEST: 'weekly_digest',
}

EMAIL_SUBJECTS = {
    NotificationType.ASKME_SPECIALIST_ANSWER: 'یک متخصص به سوال شما پاسخ داد',
    NotificationType.AD_APPROVED: 'آگهی شما در پیوند تایید شد',
    NotificationType.AD_REJECTED: 'نیاز به بازبینی آگهی شما',
    NotificationType.AD_PRO: 'آگهی شما به Pro ارتقا یافت',
    NotificationType.AD_EXPIRING: 'فقط ۷ روز تا پایان نمایش آگهی شما باقی مانده است',
    NotificationType.WEEKLY_DIGEST: 'آنچه این هفته در پیوند اتفاق افتاد',
}
