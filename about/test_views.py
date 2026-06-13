from django.test import TestCase
from django.urls import reverse

from .models import CollaborateRequest


class TestCollaborateView(TestCase):

    def test_successful_collaboration_request_submission(self):
        """Test for a user requesting a collaboration"""
        post_data = {
            'name': 'test name',
            'email': 'test@email.com',
            'message': 'test message'
        }
        response = self.client.post(reverse('about'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CollaborateRequest.objects.count(), 1)
        request = CollaborateRequest.objects.get()
        self.assertEqual(request.name, 'test name')
        self.assertEqual(request.email, 'test@email.com')
        self.assertEqual(request.message, 'test message')
        self.assertContains(
            response,
            'Collaboration request received! I endeavour to respond within 2 working days.',
        )
