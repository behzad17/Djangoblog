"""FeedbackService — validate and persist editorial AI feedback."""

from __future__ import annotations

import uuid

from content_ai.evaluation.constants import (
    AIFeedbackRating,
    VALID_FEEDBACK_REASON_VALUES,
)
from content_ai.evaluation.models import AIGenerationFeedback


class FeedbackValidationError(ValueError):
    """Raised when feedback payload cannot be persisted."""


class FeedbackService:
    """
    Persist structured editorial feedback.

    Hides ORM details from callers. Does not optimise prompts or run analytics.
    """

    def create_feedback(
        self,
        *,
        generation_id,
        prompt_task,
        rating,
        created_by=None,
        prompt_version='',
        provider='',
        model_name='',
        language='',
        reasons=None,
        comment='',
        accepted=False,
        regenerated=False,
        metadata=None,
    ) -> AIGenerationFeedback:
        generation_uuid = self._parse_generation_id(generation_id)
        rating_value = self._parse_rating(rating)
        reason_list = self._parse_reasons(reasons)
        task = (prompt_task or '').strip()
        if not task:
            raise FeedbackValidationError('prompt_task is required.')

        return AIGenerationFeedback.objects.create(
            generation_id=generation_uuid,
            prompt_task=task,
            prompt_version=(prompt_version or '')[:50],
            provider=(provider or '')[:100],
            model_name=(model_name or '')[:100],
            language=(language or '')[:32],
            rating=rating_value,
            reasons=reason_list,
            comment=comment or '',
            accepted=bool(accepted),
            regenerated=bool(regenerated),
            created_by=created_by,
            metadata=dict(metadata or {}),
        )

    def _parse_generation_id(self, generation_id):
        if generation_id is None or generation_id == '':
            raise FeedbackValidationError('generation_id is required.')
        try:
            return uuid.UUID(str(generation_id))
        except (TypeError, ValueError, AttributeError) as exc:
            raise FeedbackValidationError(
                'generation_id must be a valid UUID.'
            ) from exc

    def _parse_rating(self, rating):
        values = {choice.value for choice in AIFeedbackRating}
        if rating not in values:
            raise FeedbackValidationError(
                f'Invalid rating. Expected one of: {", ".join(sorted(values))}.'
            )
        return rating

    def _parse_reasons(self, reasons):
        if reasons is None or reasons == '':
            return []
        if isinstance(reasons, str):
            reasons = [reasons]
        if not isinstance(reasons, (list, tuple)):
            raise FeedbackValidationError('reasons must be a list of codes.')
        cleaned = []
        for item in reasons:
            if not isinstance(item, str):
                raise FeedbackValidationError('Each reason must be a string.')
            code = item.strip()
            if not code:
                continue
            if code not in VALID_FEEDBACK_REASON_VALUES:
                raise FeedbackValidationError(f'Unknown reason code: {code}.')
            if code not in cleaned:
                cleaned.append(code)
        return cleaned
