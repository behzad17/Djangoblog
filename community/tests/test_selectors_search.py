from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.test import TestCase

from community.models import CommunityCategory
from community.selectors.discussions import _public_discussions_queryset
from community.selectors.search import search_discussions
from community.services.discussions import create_discussion

User = get_user_model()


class SearchSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='searchauthor',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='جستجو',
            slug='search-cat',
        )
        cls.matching = create_discussion(
            author=cls.author,
            category=cls.category,
            title='کلمه fallbackmatch',
            body='متن بحث برای جستجو',
        )
        create_discussion(
            author=cls.author,
            category=cls.category,
            title='بحث دیگر',
            body='بدون تطابق',
        )

    def test_icontains_search_finds_partial_match(self):
        results = list(search_discussions('fallbackmatch'))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, self.matching.pk)

    @patch('community.selectors.search.connection')
    def test_postgresql_fts_returns_results_when_matches_exist(self, mock_connection):
        mock_connection.vendor = 'postgresql'
        fts_queryset = MagicMock()
        fts_queryset.exists.return_value = True
        fts_queryset.__iter__.return_value = iter([self.matching])

        base_queryset = _public_discussions_queryset()

        def fake_annotate(*args, **kwargs):
            annotated = MagicMock()
            annotated.filter.return_value.order_by.return_value = fts_queryset
            return annotated

        with patch.object(
            QuerySet,
            'annotate',
            side_effect=fake_annotate,
        ):
            results = list(search_discussions('fallbackmatch'))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, self.matching.pk)
        fts_queryset.exists.assert_called_once()

    @patch('community.selectors.search.connection')
    def test_postgresql_fallback_finds_low_rank_partial_match(self, mock_connection):
        mock_connection.vendor = 'postgresql'
        fts_queryset = MagicMock()
        fts_queryset.exists.return_value = False

        def fake_annotate(self, *args, **kwargs):
            annotated = MagicMock()
            annotated.filter.return_value.order_by.return_value = fts_queryset
            return annotated

        with patch.object(QuerySet, 'annotate', fake_annotate):
            results = list(search_discussions('fallbackmatch'))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, self.matching.pk)

    @patch('community.selectors.search.connection')
    def test_postgresql_fts_does_not_duplicate_fallback_results(self, mock_connection):
        mock_connection.vendor = 'postgresql'
        fts_queryset = _public_discussions_queryset().filter(pk=self.matching.pk)
        fts_queryset = fts_queryset.annotate(
            rank=MagicMock(),
        )
        # When FTS finds a match, return it directly without also running fallback.
        with patch.object(
            QuerySet,
            'annotate',
            return_value=MagicMock(
                filter=MagicMock(
                    return_value=MagicMock(
                        order_by=MagicMock(
                            return_value=_public_discussions_queryset().filter(
                                pk=self.matching.pk,
                            ),
                        ),
                    ),
                ),
            ),
        ):
            fts_results = _public_discussions_queryset().filter(pk=self.matching.pk)
            with patch.object(QuerySet, 'annotate') as mock_annotate:
                mock_annotate.return_value.filter.return_value.order_by.return_value = (
                    fts_results
                )
                results = list(search_discussions('fallbackmatch'))

        self.assertEqual(len(results), 1)
        pks = [discussion.pk for discussion in results]
        self.assertEqual(len(pks), len(set(pks)))
