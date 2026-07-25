"""Tests for passive Fact Checking Framework (RFC-007)."""

from __future__ import annotations

import unittest

from content_ai.config.ai_engine import (
    ENABLE_FACT_CHECKING_FRAMEWORK,
    FEATURE_FLAGS,
)
from content_ai.fact_check import (
    ClaimType,
    ConfidenceLevel,
    FactChecker,
    FactCheckRegistry,
    VerificationStatus,
    Verifier,
    build_default_registry,
    build_fact_check_report,
    confidence_rank,
    create_claim,
    create_evidence,
    extract_claims,
    summarise_evidence_confidence,
    validate_claim,
)
from content_ai.fact_check.exceptions import (
    ClaimExtractionError,
    ConfidenceError,
    RegistryError,
    ValidationError,
)


class FactCheckFlagTests(unittest.TestCase):
    def test_framework_disabled(self):
        self.assertFalse(ENABLE_FACT_CHECKING_FRAMEWORK)
        self.assertFalse(FEATURE_FLAGS['ENABLE_FACT_CHECKING_FRAMEWORK'])


class ClaimAndEvidenceTests(unittest.TestCase):
    def test_create_and_validate_claim(self):
        claim = create_claim(
            claim_text='Migrationsverket processed 1000 cases.',
            claim_type=ClaimType.NUMERICAL,
            entity='Migrationsverket',
        )
        validate_claim(claim)
        self.assertEqual(claim.verification_status, VerificationStatus.UNVERIFIED)

    def test_empty_claim_rejected(self):
        with self.assertRaises(ValidationError):
            create_claim(claim_text='  ')

    def test_unsupported_claim_type(self):
        with self.assertRaises(ValidationError):
            create_claim(claim_text='x', claim_type='not-a-type')

    def test_evidence_model(self):
        evidence = create_evidence(
            source='migrationsverket.se',
            url='https://www.migrationsverket.se',
            confidence=ConfidenceLevel.MEDIUM,
            excerpt='Official notice',
        )
        claim = create_claim(
            claim_text='Official notice exists.',
            evidence=[evidence],
        )
        validate_claim(claim)
        self.assertEqual(len(claim.evidence), 1)


class ConfidenceTests(unittest.TestCase):
    def test_confidence_rank(self):
        self.assertLess(
            confidence_rank(ConfidenceLevel.LOW),
            confidence_rank(ConfidenceLevel.HIGH),
        )

    def test_summarise_evidence_confidence(self):
        level = summarise_evidence_confidence(
            [ConfidenceLevel.HIGH, ConfidenceLevel.LOW]
        )
        self.assertEqual(level, ConfidenceLevel.LOW)

    def test_invalid_confidence(self):
        with self.assertRaises(ConfidenceError):
            create_claim(claim_text='x', confidence='extreme')


class RegistryTests(unittest.TestCase):
    def test_default_registry(self):
        registry = build_default_registry()
        self.assertIn('general', registry.list_claim_types())
        self.assertIn('noop', registry.list_providers())

    def test_duplicate_provider(self):
        registry = FactCheckRegistry()

        def provider(claim):
            return []

        registry.register_provider('x', provider)
        with self.assertRaises(RegistryError):
            registry.register_provider('x', provider)


class PipelineAndReportTests(unittest.TestCase):
    def test_extract_claims(self):
        claims = extract_claims('First claim.\n\nSecond claim.')
        self.assertEqual(len(claims), 2)

    def test_extract_empty(self):
        with self.assertRaises(ClaimExtractionError):
            extract_claims('')

    def test_verifier_requires_editor_without_evidence(self):
        claim = create_claim(claim_text='A factual sounding statement.')
        verified = Verifier().verify(claim)
        self.assertEqual(
            verified.verification_status,
            VerificationStatus.REQUIRES_EDITOR_REVIEW,
        )
        self.assertEqual(verified.confidence, ConfidenceLevel.UNKNOWN)

    def test_fact_checker_report(self):
        report = FactChecker().check_text(
            'Migrationsverket issued guidance.\n\nSkatteverket opened a form.'
        )
        payload = report.to_dict()
        self.assertEqual(payload['summary']['claim_count'], 2)
        self.assertFalse(payload['summary']['auto_publish_allowed'])
        self.assertTrue(payload['metadata']['human_decision_required'])
        self.assertTrue(payload['claims'][0]['editorial_recommendation'])

    def test_duplicate_claims_rejected(self):
        claim = create_claim(claim_text='Same text')
        with self.assertRaises(ValidationError):
            FactChecker().check_claims([claim, create_claim(claim_text='Same text')])

    def test_report_empty_rejected(self):
        with self.assertRaises(ValidationError):
            build_fact_check_report([])

    def test_verification_states_exist(self):
        values = {item.value for item in VerificationStatus}
        self.assertIn('supported', values)
        self.assertIn('requires_editor_review', values)


if __name__ == '__main__':
    unittest.main()
