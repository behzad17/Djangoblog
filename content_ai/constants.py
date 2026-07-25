from django.db import models


class AIJobType(models.TextChoices):
    POST = 'post', 'Post'
    AD = 'ad', 'Ad'


class AIJobStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
