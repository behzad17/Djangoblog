"""Tests for editorial workflow architecture (RFC-003)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from content_ai.config.ai_engine import (
    ENABLE_EDITORIAL_WORKFLOW,
    FEATURE_FLAGS,
)
from content_ai.constants import AIGenerationTask
from content_ai.providers.mock import MOCK_RESPONSE, MockProvider
from content_ai.schemas import GenerationResult, PostGenerationRequest
from content_ai.services.generation import ContentGenerationService
from content_ai.workflow import (
    ContextError,
    PRODUCTION_GENERATION_STAGES,
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
    def test_workflow_enabled_for_production(self):
        self.assertTrue(ENABLE_EDITORIAL_WORKFLOW)
        self.assertTrue(FEATURE_FLAGS['ENABLE_EDITORIAL_WORKFLOW'])


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

    def test_execute_runs_production_generation_stages(self):
        self.assertEqual(
            PRODUCTION_GENERATION_STAGES,
            (
                'research',
                'source_intelligence',
                'knowledge',
                'drafting',
                'evaluation',
            ),
        )
        ctx = create_initial_context(title='Housing news', language='fa')
        ctx = self.orch.execute(ctx)
        self.assertEqual(ctx.state, WorkflowState.DRAFTING)
        self.assertIn('workflow-stub draft', ctx.generated_draft)
        stage_names = [entry.stage_name for entry in ctx.stage_logs]
        self.assertEqual(
            stage_names,
            [
                'research',
                'source_intelligence',
                'knowledge',
                'drafting',
                'evaluation',
            ],
        )
        self.assertEqual(
            ctx.extension_data.get('hooks', {}).get('preparation'),
            'completed',
        )
        self.assertEqual(
            ctx.extension_data.get('source_intelligence', {}).get('status'),
            'completed',
        )
        self.assertEqual(
            ctx.extension_data.get('knowledge', {}).get('status'),
            'skipped',
        )
        self.assertEqual(
            ctx.extension_data.get('evaluation', {}).get('status'),
            'skipped',
        )

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


class ProductionWorkflowIntegrationTests(unittest.TestCase):
    def test_content_generation_runs_workflow_execute(self):
        service = ContentGenerationService()
        provider = MagicMock(spec=MockProvider)
        provider.name = 'mock'
        provider.generate_post.return_value = GenerationResult(
            success=True,
            content=MOCK_RESPONSE,
            provider='mock',
        )

        with patch(
            'content_ai.providers.registry.get_provider',
            return_value=provider,
        ), patch.object(
            service.workflow,
            'execute',
            wraps=service.workflow.execute,
        ) as mocked_execute:
            result = service.generate(
                AIGenerationTask.POST_GENERATION,
                PostGenerationRequest(title='Workflow'),
            )

        mocked_execute.assert_called_once()
        provider.generate_post.assert_called_once()
        self.assertEqual(result.content, MOCK_RESPONSE)
        self.assertEqual(
            result.metadata.get('workflow_state'),
            WorkflowState.DRAFTING.value,
        )
        self.assertEqual(
            result.metadata.get('workflow_stages'),
            list(PRODUCTION_GENERATION_STAGES),
        )
        intelligence = result.metadata.get('intelligence') or {}
        self.assertEqual(
            (intelligence.get('source') or {}).get('status'),
            'completed',
        )
        self.assertEqual(
            (intelligence.get('knowledge') or {}).get('status'),
            'skipped',
        )
        self.assertEqual(
            (intelligence.get('evaluation') or {}).get('status'),
            'skipped',
        )
        hooks = intelligence.get('hooks') or {}
        self.assertEqual(hooks.get('preparation'), 'completed')
        self.assertEqual(hooks.get('source_intelligence'), 'completed')
        self.assertEqual(hooks.get('knowledge_retrieval'), 'skipped')
        self.assertEqual(hooks.get('prompt_assembly'), 'completed')
        self.assertEqual(hooks.get('ai_provider'), 'completed')
        self.assertEqual(hooks.get('prompt_evaluation'), 'skipped')
        self.assertEqual(hooks.get('completion'), 'completed')

    def test_knowledge_enabled_prepares_metadata_without_blocking(self):
        service = ContentGenerationService()
        with patch(
            'content_ai.knowledge.integration.ENABLE_KNOWLEDGE_ENGINE',
            True,
        ), patch(
            'content_ai.knowledge.integration.ENABLE_RAG',
            False,
        ):
            result = service.generate(
                AIGenerationTask.POST_GENERATION,
                PostGenerationRequest(title='Knowledge'),
                provider_name='mock',
            )
        self.assertTrue(result.success)
        knowledge = (result.metadata.get('intelligence') or {}).get(
            'knowledge'
        ) or {}
        self.assertEqual(knowledge.get('status'), 'prepared')
        self.assertGreater(knowledge.get('module_count', 0), 0)
        self.assertEqual(
            (result.metadata.get('intelligence') or {})
            .get('hooks', {})
            .get('knowledge_retrieval'),
            'completed',
        )

    def test_evaluation_hook_runs_when_flag_enabled(self):
        service = ContentGenerationService()
        with patch(
            'content_ai.workflow.services.evaluation.ENABLE_AI_EVALUATION_FRAMEWORK',
            True,
        ):
            result = service.generate(
                AIGenerationTask.POST_GENERATION,
                PostGenerationRequest(title='Evaluate me'),
                provider_name='mock',
            )
        self.assertTrue(result.success)
        evaluation = (result.metadata.get('intelligence') or {}).get(
            'evaluation'
        ) or {}
        self.assertEqual(evaluation.get('status'), 'completed')
        self.assertIn('overall_score', evaluation)
        self.assertEqual(
            (result.metadata.get('intelligence') or {})
            .get('hooks', {})
            .get('prompt_evaluation'),
            'completed',
        )

    def test_source_intelligence_enriches_request_metadata(self):
        service = ContentGenerationService()
        result = service.generate(
            AIGenerationTask.POST_GENERATION,
            PostGenerationRequest(
                title='خبر مسکن',
                source='https://example.com/housing',
                context='Persian community housing update',
            ),
            provider_name='mock',
        )
        source = (result.metadata.get('intelligence') or {}).get(
            'source'
        ) or {}
        self.assertEqual(source.get('status'), 'completed')
        self.assertEqual(source.get('source_type'), 'url')
        self.assertEqual(source.get('detected_language'), 'fa')


if __name__ == '__main__':
    unittest.main()
