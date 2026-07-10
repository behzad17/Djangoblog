from django.contrib.auth import get_user_model

from django.test import TestCase

from community.forms.discussion import (
    DISCUSSION_BODY_MAX_LENGTH,
    DISCUSSION_BODY_MIN_LENGTH,
    DISCUSSION_TITLE_MAX_LENGTH,
    DiscussionCreateForm,
    DiscussionUpdateForm,
)
from community.models import CommunityCategory
from community.services.discussions import create_discussion

User = get_user_model()


class DiscussionCreateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='formauthor',
            password='password123',
        )
        cls.active_category = CommunityCategory.objects.create(
            name='فعال',
            slug='active-category',
        )
        cls.inactive_category = CommunityCategory.objects.create(
            name='غیرفعال',
            slug='inactive-category',
            is_active=False,
        )

    def _valid_data(self, **overrides):
        data = {
            'title': 'عنوان معتبر',
            'category': self.active_category.pk,
            'body': 'متن بحث با طول کافی برای اعتبارسنجی',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = DiscussionCreateForm(data=self._valid_data())
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['title'], 'عنوان معتبر')
        self.assertEqual(form.cleaned_data['category'], self.active_category)

    def test_missing_title(self):
        form = DiscussionCreateForm(data=self._valid_data(title=''))
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_missing_body(self):
        form = DiscussionCreateForm(data=self._valid_data(body=''))
        self.assertFalse(form.is_valid())
        self.assertIn('body', form.errors)

    def test_missing_category(self):
        form = DiscussionCreateForm(data=self._valid_data(category=''))
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_title_max_length(self):
        form = DiscussionCreateForm(
            data=self._valid_data(title='a' * (DISCUSSION_TITLE_MAX_LENGTH + 1)),
        )
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_body_min_length(self):
        form = DiscussionCreateForm(
            data=self._valid_data(body='a' * (DISCUSSION_BODY_MIN_LENGTH - 1)),
        )
        self.assertFalse(form.is_valid())
        self.assertIn('body', form.errors)

    def test_body_max_length(self):
        form = DiscussionCreateForm(
            data=self._valid_data(body='a' * (DISCUSSION_BODY_MAX_LENGTH + 1)),
        )
        self.assertFalse(form.is_valid())
        self.assertIn('body', form.errors)

    def test_inactive_category_rejected(self):
        form = DiscussionCreateForm(
            data=self._valid_data(category=self.inactive_category.pk),
        )
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_strips_whitespace(self):
        form = DiscussionCreateForm(
            data=self._valid_data(
                title='  عنوان  ',
                body='  متن بحث با طول کافی برای اعتبارسنجی  ',
            ),
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['title'], 'عنوان')
        self.assertEqual(
            form.cleaned_data['body'],
            'متن بحث با طول کافی برای اعتبارسنجی',
        )

    def test_widgets_have_bootstrap_classes(self):
        form = DiscussionCreateForm()
        self.assertIn('form-control', form.fields['title'].widget.attrs['class'])
        self.assertIn('form-control', form.fields['body'].widget.attrs['class'])
        self.assertIn('form-select', form.fields['category'].widget.attrs['class'])

    def test_excludes_slug_status_and_soft_delete_fields(self):
        form = DiscussionCreateForm()
        self.assertNotIn('slug', form.fields)
        self.assertNotIn('status', form.fields)
        self.assertNotIn('is_deleted', form.fields)


class DiscussionUpdateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='updateauthor',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='به‌روزرسانی',
            slug='update-category',
        )
        cls.discussion = create_discussion(
            author=cls.user,
            category=cls.category,
            title='بحث اولیه',
            body='متن اولیه با طول کافی',
        )

    def test_valid_update_form(self):
        form = DiscussionUpdateForm(
            instance=self.discussion,
            data={
                'title': 'عنوان جدید',
                'category': self.category.pk,
                'body': 'متن جدید با طول کافی برای اعتبار',
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['title'], 'عنوان جدید')

    def test_update_form_does_not_expose_protected_fields(self):
        form = DiscussionUpdateForm(instance=self.discussion)
        protected_fields = {'slug', 'status', 'is_deleted', 'deleted_at', 'deleted_by'}
        self.assertTrue(protected_fields.isdisjoint(form.fields.keys()))
