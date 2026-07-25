from django.test import SimpleTestCase

from content_ai.schemas import (
    AdGenerationRequest,
    GenerationResult,
    PostGenerationRequest,
)


class RequestSchemaTests(SimpleTestCase):
    def test_post_generation_request_defaults(self):
        request = PostGenerationRequest()
        self.assertEqual(request.title, '')
        self.assertEqual(request.source, '')
        self.assertEqual(request.language, '')
        self.assertEqual(request.category, '')
        self.assertEqual(request.context, '')
        self.assertEqual(request.instructions, '')

    def test_post_generation_request_fields(self):
        request = PostGenerationRequest(
            title='Title',
            source='rss',
            language='sv',
            category='news',
            context='ctx',
            instructions='keep formal',
        )
        self.assertEqual(request.title, 'Title')
        self.assertEqual(request.language, 'sv')
        self.assertEqual(request.instructions, 'keep formal')

    def test_ad_generation_request_fields(self):
        request = AdGenerationRequest(
            business_name='Cafe',
            category='food',
            language='fa',
            city='Stockholm',
            description='Lunch',
            target_audience='locals',
            instructions='short',
        )
        self.assertEqual(request.business_name, 'Cafe')
        self.assertEqual(request.city, 'Stockholm')
        self.assertEqual(request.target_audience, 'locals')


class ResponseSchemaTests(SimpleTestCase):
    def test_generation_result_creation(self):
        result = GenerationResult(
            success=True,
            content='Hello',
            metadata={'k': 'v'},
            warnings=['note'],
            provider='mock',
        )
        self.assertTrue(result.success)
        self.assertEqual(result.content, 'Hello')
        self.assertEqual(result.metadata, {'k': 'v'})
        self.assertEqual(result.warnings, ['note'])
        self.assertEqual(result.provider, 'mock')

    def test_generation_result_default_collections(self):
        result = GenerationResult(success=False, content='')
        self.assertEqual(result.metadata, {})
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.provider, '')
        self.assertIsNone(result.telemetry)
