from django.test import TestCase

from community.forms.reply import (
    REPLY_BODY_MAX_LENGTH,
    REPLY_BODY_MIN_LENGTH,
    ReplyCreateForm,
)


class ReplyCreateFormTests(TestCase):
    def _valid_data(self, **overrides):
        data = {'body': 'پاسخ معتبر با طول کافی'}
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = ReplyCreateForm(data=self._valid_data())
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['body'], 'پاسخ معتبر با طول کافی')

    def test_missing_body(self):
        form = ReplyCreateForm(data=self._valid_data(body=''))
        self.assertFalse(form.is_valid())
        self.assertIn('body', form.errors)

    def test_body_min_length(self):
        form = ReplyCreateForm(
            data=self._valid_data(body='a' * (REPLY_BODY_MIN_LENGTH - 1)),
        )
        self.assertFalse(form.is_valid())
        self.assertIn('body', form.errors)

    def test_body_max_length(self):
        form = ReplyCreateForm(
            data=self._valid_data(body='a' * (REPLY_BODY_MAX_LENGTH + 1)),
        )
        self.assertFalse(form.is_valid())
        self.assertIn('body', form.errors)

    def test_strips_whitespace(self):
        form = ReplyCreateForm(
            data=self._valid_data(body='  پاسخ معتبر با طول کافی  '),
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['body'], 'پاسخ معتبر با طول کافی')

    def test_widget_has_bootstrap_class(self):
        form = ReplyCreateForm()
        self.assertIn(
            'form-control',
            form.fields['body'].widget.attrs['class'],
        )
        self.assertIn('aria-label', form.fields['body'].widget.attrs)

    def test_only_body_field_exposed(self):
        form = ReplyCreateForm()
        self.assertEqual(list(form.fields.keys()), ['body'])
