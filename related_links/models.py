from django.db import models
from cloudinary.models import CloudinaryField
from django.utils.text import slugify


class LinkType(models.TextChoices):
    PODCAST = 'podcast', '🎧 پادکست'
    VIDEO = 'video', '🎬 فیلم / ویدئو'
    RADIO = 'radio', '📻 رادیو'
    WEBSITE = 'website', '🌐 وب‌سایت'
    FILE = 'file', '📂 فایل آموزشی'
    SOCIAL = 'social', '📱 شبکه‌های اجتماعی'


class RelatedLink(models.Model):
    """Model for admin-managed related links with filtering by type."""
    
    title = models.CharField(max_length=200, verbose_name='عنوان')
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='نامک')
    link_type = models.CharField(
        max_length=20,
        choices=LinkType.choices,
        default=LinkType.WEBSITE,
        verbose_name='نوع لینک'
    )
    description = models.TextField(blank=True, verbose_name='توضیحات')
    source_name = models.CharField(max_length=200, blank=True, verbose_name='نام منبع')
    url = models.URLField(verbose_name='لینک')
    cover_image = CloudinaryField(
        'cover_image',
        blank=True,
        null=True,
        help_text='تصویر کاور اختیاری'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    created_on = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_on = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'لینک مرتبط'
        verbose_name_plural = 'لینک‌های مرتبط'
        ordering = ['order', '-created_on']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Auto-generate slug from title, ensuring uniqueness."""
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            slug = base_slug
            counter = 1
            while RelatedLink.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_button_label(self):
        """Get CTA button label based on link type."""
        labels = {
            LinkType.PODCAST: 'گوش دادن',
            LinkType.RADIO: 'گوش دادن',
            LinkType.VIDEO: 'تماشا',
            LinkType.WEBSITE: 'مشاهده',
            LinkType.FILE: 'مشاهده',
            LinkType.SOCIAL: 'مشاهده',
        }
        return labels.get(self.link_type, 'مشاهده')

