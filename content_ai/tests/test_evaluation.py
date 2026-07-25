import uuid

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from content_ai.evaluation.admin import AIGenerationFeedbackAdmin
from content_ai.evaluation.constants import AIFeedbackRating, AIFeedbackReason
from content_ai.evaluation.models import AIGenerationFeedback
from content_ai.evaluation.services import FeedbackService, FeedbackValidationError

User = get_user_model()


class FeedbackServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='feedbackeditor',
            password='password123',
            is_staff=True,
        )
        self.service = FeedbackService()
        self.generation_id = uuid.uuid4()

    def test_create_feedback(self):
        feedback = self.service.create_feedback(
            generation_id=self.generation_id,
            prompt_task='post_generation',
            prompt_version='v1',
            provider='mock',
            model_name='mock',
            language='sv',
            rating=AIFeedbackRating.GOOD,
            reasons=[AIFeedbackReason.TOO_LONG, AIFeedbackReason.GRAMMAR],
            comment='Slightly long',
            created_by=self.user,
        )
        self.assertEqual(feedback.generation_id, self.generation_id)
        self.assertEqual(feedback.rating, AIFeedbackRating.GOOD)
        self.assertEqual(
            feedback.reasons,
            [AIFeedbackReason.TOO_LONG, AIFeedbackReason.GRAMMAR],
        )
        self.assertEqual(feedback.comment, 'Slightly long')
        self.assertFalse(feedback.accepted)
        self.assertFalse(feedback.regenerated)

    def test_accepted_feedback(self):
        feedback = self.service.create_feedback(
            generation_id=self.generation_id,
            prompt_task='post_generation',
            rating=AIFeedbackRating.EXCELLENT,
            accepted=True,
            created_by=self.user,
        )
        self.assertTrue(feedback.accepted)
        self.assertFalse(feedback.regenerated)

    def test_regenerated_feedback(self):
        feedback = self.service.create_feedback(
            generation_id=self.generation_id,
            prompt_task='post_generation',
            rating=AIFeedbackRating.NEEDS_IMPROVEMENT,
            regenerated=True,
            reasons=[AIFeedbackReason.WRONG_TONE],
            created_by=self.user,
        )
        self.assertTrue(feedback.regenerated)
        self.assertFalse(feedback.accepted)

    def test_invalid_rating_rejected(self):
        with self.assertRaises(FeedbackValidationError):
            self.service.create_feedback(
                generation_id=self.generation_id,
                prompt_task='post_generation',
                rating='amazing',
            )

    def test_invalid_reason_rejected(self):
        with self.assertRaises(FeedbackValidationError):
            self.service.create_feedback(
                generation_id=self.generation_id,
                prompt_task='post_generation',
                rating=AIFeedbackRating.GOOD,
                reasons=['not-a-reason'],
            )

    def test_invalid_generation_id(self):
        with self.assertRaises(FeedbackValidationError):
            self.service.create_feedback(
                generation_id='not-a-uuid',
                prompt_task='post_generation',
                rating=AIFeedbackRating.GOOD,
            )


class FeedbackAdminRegistrationTests(SimpleTestCase):
    def test_feedback_admin_registered(self):
        self.assertIn(AIGenerationFeedback, site._registry)
        self.assertIsInstance(
            site._registry[AIGenerationFeedback],
            AIGenerationFeedbackAdmin,
        )


@override_settings(
    CONTENT_AI_PROVIDER='mock',
    ADMIN_NOTIFICATION_ENABLED=False,
)
class AdminAssistantFeedbackEndpointTests(TestCase):
    def setUp(self):
        import cloudinary

        cloudinary.config(cloud_name='test', api_key='test', api_secret='test')
        self.client = Client()
        self.staff = User.objects.create_user(
            username='feedbackstaff',
            password='password123',
            is_staff=True,
        )
        for codename in ('add_post', 'change_post', 'view_post'):
            perm = Permission.objects.get(
                content_type__app_label='blog',
                codename=codename,
            )
            self.staff.user_permissions.add(perm)
        self.feedback_url = reverse('admin:blog_post_ai_assistant_feedback')
        self.client.force_login(self.staff)

    def _payload(self, **overrides):
        data = {
            'generation_id': str(uuid.uuid4()),
            'prompt_task': 'post_generation',
            'prompt_version': 'v1',
            'provider': 'mock',
            'model': 'mock',
            'language': 'sv',
            'rating': AIFeedbackRating.GOOD,
            'reasons': [AIFeedbackReason.FORMATTING],
            'comment': 'ok',
            'accepted': True,
            'regenerated': False,
            'post_id': '',
            'action': 'use_draft',
        }
        data.update(overrides)
        return data

    def test_feedback_endpoint_creates_row(self):
        import json

        before = AIGenerationFeedback.objects.count()
        response = self.client.post(
            self.feedback_url,
            data=json.dumps(self._payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AIGenerationFeedback.objects.count(), before + 1)
        row = AIGenerationFeedback.objects.latest('created_at')
        self.assertTrue(row.accepted)
        self.assertEqual(row.rating, AIFeedbackRating.GOOD)
        self.assertEqual(row.created_by_id, self.staff.id)

    def test_feedback_endpoint_requires_permission(self):
        import json

        bare = User.objects.create_user(
            username='barefeedback',
            password='password123',
            is_staff=True,
        )
        self.client.force_login(bare)
        response = self.client.post(
            self.feedback_url,
            data=json.dumps(self._payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_add_form_includes_feedback_ui(self):
        response = self.client.get(reverse('admin:blog_post_add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editorial Feedback')
        self.assertContains(response, self.feedback_url)
        self.assertContains(response, '👎 Reject')
