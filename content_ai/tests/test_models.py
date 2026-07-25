from django.contrib.auth import get_user_model
from django.test import TestCase

from content_ai.constants import AIJobStatus, AIJobType
from content_ai.models import AIJob

User = get_user_model()


class AIJobModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='aijobuser',
            password='password123',
        )

    def test_create_ai_job_with_defaults(self):
        job = AIJob.objects.create(
            job_type=AIJobType.POST,
            created_by=self.user,
        )
        self.assertEqual(job.job_type, AIJobType.POST)
        self.assertEqual(job.status, AIJobStatus.PENDING)
        self.assertEqual(job.provider, '')
        self.assertEqual(job.model_name, '')
        self.assertEqual(job.prompt_version, '')
        self.assertEqual(job.created_by, self.user)
        self.assertIsNone(job.started_at)
        self.assertIsNone(job.completed_at)
        self.assertIsNotNone(job.created_at)
        self.assertIsNotNone(job.updated_at)

    def test_str_includes_id_type_and_status(self):
        job = AIJob.objects.create(job_type=AIJobType.AD)
        self.assertEqual(
            str(job),
            f'AIJob {job.pk} ({AIJobType.AD}/{AIJobStatus.PENDING})',
        )

    def test_job_type_choices(self):
        self.assertEqual(AIJobType.POST, 'post')
        self.assertEqual(AIJobType.AD, 'ad')
        self.assertEqual(
            set(AIJobType.values),
            {'post', 'ad'},
        )

    def test_status_choices(self):
        self.assertEqual(AIJobStatus.PENDING, 'pending')
        self.assertEqual(AIJobStatus.RUNNING, 'running')
        self.assertEqual(AIJobStatus.COMPLETED, 'completed')
        self.assertEqual(AIJobStatus.FAILED, 'failed')
        self.assertEqual(
            set(AIJobStatus.values),
            {'pending', 'running', 'completed', 'failed'},
        )

    def test_status_can_be_updated(self):
        job = AIJob.objects.create(job_type=AIJobType.POST)
        job.status = AIJobStatus.RUNNING
        job.save(update_fields=['status', 'updated_at'])
        job.refresh_from_db()
        self.assertEqual(job.status, AIJobStatus.RUNNING)

    def test_default_ordering_is_newest_first(self):
        older = AIJob.objects.create(job_type=AIJobType.POST)
        newer = AIJob.objects.create(job_type=AIJobType.AD)
        jobs = list(AIJob.objects.all())
        self.assertEqual(jobs[0], newer)
        self.assertEqual(jobs[1], older)
