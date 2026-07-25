from django.db import models


class AIJobType(models.TextChoices):
    POST = 'post', 'Post'
    AD = 'ad', 'Ad'


class AIJobStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class AIGenerationTask(models.TextChoices):
    """Extendable task identifiers for ContentGenerationService."""

    POST_GENERATION = 'post_generation', 'Post generation'
    AD_GENERATION = 'ad_generation', 'Ad generation'
    REWRITE = 'rewrite', 'Rewrite'
    SUMMARY = 'summary', 'Summary'
    TRANSLATION = 'translation', 'Translation'
    SEO = 'seo', 'SEO'
