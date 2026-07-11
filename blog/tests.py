from django.test import TestCase

from blog.utils import html_to_plain_text


class HtmlToPlainTextTests(TestCase):
    def test_preserves_word_boundaries_between_block_elements(self):
        self.assertEqual(
            html_to_plain_text('<p>مالیات</p><p>سوئد</p>'),
            'مالیات سوئد',
        )

    def test_preserves_word_boundaries_between_inline_elements(self):
        self.assertEqual(
            html_to_plain_text('مالیات<strong>سوئد</strong>'),
            'مالیات سوئد',
        )

    def test_preserves_spaces_inside_paragraphs(self):
        self.assertEqual(
            html_to_plain_text('<p>به دنبال <strong>مالیات</strong> هستم.</p>'),
            'به دنبال مالیات هستم.',
        )
