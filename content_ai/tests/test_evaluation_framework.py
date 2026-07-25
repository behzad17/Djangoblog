"""Tests for passive AI Evaluation Framework (RFC-004)."""

from __future__ import annotations

import unittest

from content_ai.config.ai_engine import (
    ENABLE_AI_EVALUATION_FRAMEWORK,
    FEATURE_FLAGS,
)
from content_ai.evaluation.comparison import ComparisonEngine
from content_ai.evaluation.evaluator import Evaluator
from content_ai.evaluation.exceptions import (
    ComparisonError,
    MetricError,
    RegistryError,
    ReportError,
    SnapshotError,
)
from content_ai.evaluation.metrics import ReadabilityMetric, default_metrics
from content_ai.evaluation.registry import MetricRegistry, build_default_registry
from content_ai.evaluation.report import ReportBuilder
from content_ai.evaluation.scoring import MetricResult, aggregate_scores
from content_ai.evaluation.snapshot import create_snapshot, validate_snapshot


SAMPLE = (
    '# عنوان\n\n'
    'این یک متن آزمایشی برای ارزیابی خوانایی و ساختار است. '
    'Skatteverket یک مرجع رسمی است. '
    'برای جزئیات بیشتر https://example.com را ببینید.\n\n'
    'پاراگراف دوم درباره زندگی در سوئد صحبت می‌کند و اصطلاحات را تکرار می‌کند. '
    'زندگی در سوئد نیازمند آگاهی از خدمات عمومی است.\n'
)


class EvaluationFlagTests(unittest.TestCase):
    def test_framework_disabled(self):
        self.assertFalse(ENABLE_AI_EVALUATION_FRAMEWORK)
        self.assertFalse(FEATURE_FLAGS['ENABLE_AI_EVALUATION_FRAMEWORK'])


class SnapshotTests(unittest.TestCase):
    def test_create_snapshot(self):
        snap = create_snapshot(
            output_text=SAMPLE,
            input_text='prompt',
            provider='openai',
            model='gpt-test',
            prompt_version='v1',
            knowledge_version='kb-1',
            language='fa',
            latency_ms=12.5,
            estimated_cost=0.01,
            token_usage={'total_tokens': 100},
        )
        self.assertTrue(snap.generation_id)
        self.assertEqual(snap.output_size, len(SAMPLE))
        self.assertEqual(snap.provider, 'openai')
        validate_snapshot(snap)

    def test_invalid_score_range(self):
        snap = create_snapshot(output_text='x').with_scores({'readability': 1.5})
        with self.assertRaises(SnapshotError):
            validate_snapshot(snap)


class RegistryAndScoringTests(unittest.TestCase):
    def test_default_registry_and_duplicate(self):
        registry = build_default_registry()
        names = registry.list_metrics()
        self.assertIn('readability', names)
        self.assertIn('localisation', names)
        with self.assertRaises(RegistryError):
            registry.register(ReadabilityMetric())

    def test_invalid_weight(self):
        class Bad(ReadabilityMetric):
            name = 'bad'
            default_weight = -1

        registry = MetricRegistry()
        with self.assertRaises(RegistryError):
            registry.register(Bad())

    def test_aggregate_scores(self):
        results = [
            MetricResult(name='a', score=0.5, weight=1.0, confidence=1.0),
            MetricResult(name='b', score=1.0, weight=1.0, confidence=0.5),
        ]
        agg = aggregate_scores(results)
        self.assertAlmostEqual(agg.overall_score, 0.75)
        self.assertAlmostEqual(agg.weighted_score, 0.75)
        self.assertGreater(agg.confidence_score, 0)

    def test_aggregate_empty(self):
        with self.assertRaises(MetricError):
            aggregate_scores([])

    def test_metric_result_validation(self):
        with self.assertRaises(MetricError):
            MetricResult(name='x', score=2.0).validate()


class EvaluatorComparisonReportTests(unittest.TestCase):
    def test_evaluator(self):
        snap = create_snapshot(
            output_text=SAMPLE,
            language='fa',
            prompt_version='v1',
            provider='mock',
        )
        result = Evaluator().evaluate(snap)
        self.assertTrue(result.snapshot.scores)
        self.assertGreaterEqual(result.aggregate.weighted_score, 0)
        self.assertLessEqual(result.aggregate.weighted_score, 1)

    def test_comparison(self):
        a = Evaluator().evaluate(
            create_snapshot(
                output_text=SAMPLE,
                prompt_version='v1',
                provider='mock',
                language='fa',
            )
        ).snapshot
        b = Evaluator().evaluate(
            create_snapshot(
                output_text='short',
                prompt_version='v2',
                provider='mock',
                language='fa',
            )
        ).snapshot
        compared = ComparisonEngine().compare([a, b], dimension='prompt_version')
        self.assertEqual(compared.dimension, 'prompt_version')
        self.assertIn('v1', compared.averages)
        self.assertIn('v2', compared.averages)

    def test_comparison_unknown_dimension(self):
        snap = create_snapshot(output_text='x')
        with self.assertRaises(ComparisonError):
            ComparisonEngine().compare([snap], dimension='temperature')

    def test_report(self):
        snaps = [
            Evaluator().evaluate(
                create_snapshot(
                    output_text=SAMPLE,
                    prompt_version='v1',
                    provider='openai',
                    knowledge_version='kb-1',
                    language='fa',
                    latency_ms=10,
                    estimated_cost=0.02,
                    token_usage={'total_tokens': 50},
                )
            ).snapshot,
            Evaluator().evaluate(
                create_snapshot(
                    output_text=SAMPLE + ' more text for consistency.',
                    prompt_version='v2',
                    provider='mock',
                    knowledge_version='kb-2',
                    language='fa',
                    latency_ms=5,
                    estimated_cost=0.01,
                    token_usage={'total_tokens': 40},
                )
            ).snapshot,
        ]
        report = ReportBuilder().build(snaps)
        self.assertIsNotNone(report.summary.get('average_score'))
        self.assertTrue(report.rankings['best_prompt'])

    def test_report_empty(self):
        with self.assertRaises(ReportError):
            ReportBuilder().build([])

    def test_default_metrics_count(self):
        self.assertEqual(len(default_metrics()), 7)

    def test_existing_feedback_exports_intact(self):
        from content_ai.evaluation import (
            AIGenerationFeedback,
            FeedbackService,
        )

        self.assertTrue(AIGenerationFeedback)
        self.assertTrue(FeedbackService)


if __name__ == '__main__':
    unittest.main()
