"""Tests for inactive editorial workflow architecture (RFC-003)."""

from __future__ import annotations

import unittest

from content_ai.config.ai_engine import (
    ENABLE_EDITORIAL_WORKFLOW,
    FEATURE_FLAGS,
)
from content_ai.workflow import (
    ContextError,
    StageExecutionError,
    TransitionError,
    WorkflowContext,
    WorkflowOrchestrator,
    WorkflowState,
    WorkflowValidationError,
    can_transition,
    create_initial_context,
)
from content_ai.workflow.services import DraftService, ResearchService
from content_ai.workflow.services.base import WorkflowStageService


class WorkflowFlagTests(unittest.TestCase):
    def test_workflow_disabled(self):
        self.assertFalse(ENABLE_EDITORIAL_WORKFLOW)
        self.assertFalse(FEATURE_FLAGS['ENABLE_EDITORIAL_WORKFLOW'])


class WorkflowContextTests(unittest.TestCase):
    def test_create_initial_context(self):
        ctx = create_initial_context(
            title='Housing',
            language='fa',
            audience='community',
            prompt_version='v1',
            knowledge_version='kb-1',
        )
        self.assertEqual(ctx.state, WorkflowState.IDEA)
        self.assertEqual(ctx.article_metadata['title'], 'Housing')
        self.assertEqual(ctx.language, 'fa')
        self.assertEqual(ctx.prompt_version, 'v1')

    def test_missing_title_raises(self):
        with self.assertRaises(ContextError):
            create_initial_context(title='')

    def test_context_updates(self):
        ctx = create_initial_context(title='T')
        ctx.add_warning('w')
        ctx.add_error('e')
        ctx.add_note('n')
        self.assertEqual(ctx.warnings, ['w'])
        self.assertEqual(ctx.errors, ['e'])
        self.assertEqual(ctx.editorial_notes, ['n'])

    def test_require_article_metadata(self):
        ctx = WorkflowContext(article_metadata={})
        with self.assertRaises(ContextError):
            ctx.require_article_metadata('title')


class StateTransitionTests(unittest.TestCase):
    def test_allowed_happy_path(self):
        self.assertTrue(can_transition(WorkflowState.IDEA, WorkflowState.RESEARCHING))
        self.assertTrue(
            can_transition(WorkflowState.RESEARCHING, WorkflowState.DRAFTING)
        )
        self.assertTrue(
            can_transition(WorkflowState.APPROVED, WorkflowState.PUBLISHED)
        )

    def test_invalid_transition(self):
        self.assertFalse(
            can_transition(WorkflowState.IDEA, WorkflowState.PUBLISHED)
        )
        orch = WorkflowOrchestrator()
        ctx = create_initial_context(title='T')
        with self.assertRaises(TransitionError):
            orch.transition(ctx, WorkflowState.PUBLISHED)


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.orch = WorkflowOrchestrator()
        self.orch.validate_configuration()

    def test_duplicate_stage_registration(self):
        with self.assertRaises(WorkflowValidationError):
            self.orch.register_stage(ResearchService())

    def test_unknown_stage(self):
        ctx = create_initial_context(title='T')
        with self.assertRaises(WorkflowValidationError):
            self.orch.run_stage(ctx, 'does-not-exist')

    def test_incomplete_configuration(self):
        orch = WorkflowOrchestrator(stages=[])
        with self.assertRaises(WorkflowValidationError):
            orch.validate_configuration()

    def test_run_research_and_draft_stubs(self):
        ctx = create_initial_context(title='Housing news', language='fa')
        ctx = self.orch.run_stage(ctx, 'research')
        self.assertEqual(ctx.state, WorkflowState.RESEARCHING)
        ctx = self.orch.run_stage(ctx, 'drafting')
        self.assertEqual(ctx.state, WorkflowState.DRAFTING)
        self.assertIn('workflow-stub draft', ctx.generated_draft)
        self.assertTrue(ctx.stage_logs)
        self.assertEqual(ctx.stage_logs[-1].stage_name, 'drafting')

    def test_stage_failure_sets_failed(self):
        class Boom(WorkflowStageService):
            name = 'boom'
            entry_state = WorkflowState.IDEA
            success_state = WorkflowState.RESEARCHING

            def run(self, context):
                raise RuntimeError('explode')

        orch = WorkflowOrchestrator(stages=[Boom(), DraftService()])
        # incomplete config but run_stage still works for registered
        ctx = create_initial_context(title='T')
        with self.assertRaises(StageExecutionError):
            orch.run_stage(ctx, 'boom')
        self.assertEqual(ctx.state, WorkflowState.FAILED)

    def test_publishing_requires_draft(self):
        ctx = create_initial_context(title='T')
        ctx.state = WorkflowState.APPROVED
        with self.assertRaises(StageExecutionError):
            self.orch.run_stage(ctx, 'publishing')

    def test_happy_path_to_ready_for_approval(self):
        ctx = create_initial_context(title='Guide')
        ctx = self.orch.run_stage(ctx, 'research')
        ctx = self.orch.run_stage(ctx, 'drafting')
        ctx = self.orch.transition(ctx, WorkflowState.FACT_CHECK_PENDING)
        ctx = self.orch.run_stage(ctx, 'fact_check_placeholder')
        self.assertEqual(ctx.state, WorkflowState.REVIEWING)
        ctx = self.orch.run_stage(ctx, 'review')
        self.assertEqual(ctx.state, WorkflowState.READY_FOR_APPROVAL)
        self.assertIn('fact_checking', ctx.extension_data.get('hooks', {}))

    def test_production_generation_untouched_smoke(self):
        from content_ai.editorial.service import EditorialAIService
        from unittest.mock import MagicMock

        generation = MagicMock()
        generation.generate.return_value = MagicMock(
            content='ok',
            metadata={},
            provider='mock',
            success=True,
            warnings=[],
            telemetry=None,
        )
        draft = EditorialAIService(generation_service=generation).generate_draft(
            title='X'
        )
        self.assertEqual(draft.body, 'ok')


if __name__ == '__main__':
    unittest.main()
