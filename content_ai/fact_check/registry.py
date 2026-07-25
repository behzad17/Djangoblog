"""Registry for claim types, rules, and evidence providers (RFC-007)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from content_ai.fact_check.claims import Claim, ClaimType
from content_ai.fact_check.evidence import Evidence
from content_ai.fact_check.exceptions import RegistryError, ValidationError


VerificationRule = Callable[[Claim], Claim]
EvidenceProvider = Callable[[Claim], list[Evidence]]


class FactCheckRegistry:
    """
    Register claim types, verification rules, and evidence providers.

    Avoids hardcoded rule lists at call sites.
    """

    def __init__(self):
        self._claim_types: dict[str, ClaimType] = {
            item.value: item for item in ClaimType
        }
        self._rules: dict[str, VerificationRule] = {}
        self._providers: dict[str, EvidenceProvider] = {}
        self._validators: dict[str, Callable[[Claim], None]] = {}

    def register_claim_type(self, claim_type: ClaimType) -> None:
        if not isinstance(claim_type, ClaimType):
            raise RegistryError('claim_type must be a ClaimType.')
        if claim_type.value in self._claim_types:
            # Built-ins are preloaded; re-registering the same enum is fine.
            if self._claim_types[claim_type.value] is claim_type:
                return
            raise RegistryError(
                f'Duplicate claim type: {claim_type.value!r}.'
            )
        self._claim_types[claim_type.value] = claim_type

    def register_rule(self, name: str, rule: VerificationRule) -> None:
        key = (name or '').strip()
        if not key:
            raise RegistryError('Rule name is required.')
        if key in self._rules:
            raise RegistryError(f'Duplicate verification rule: {key!r}.')
        self._rules[key] = rule

    def register_provider(self, name: str, provider: EvidenceProvider) -> None:
        key = (name or '').strip()
        if not key:
            raise RegistryError('Provider name is required.')
        if key in self._providers:
            raise RegistryError(f'Duplicate evidence provider: {key!r}.')
        self._providers[key] = provider

    def register_validator(
        self,
        name: str,
        validator: Callable[[Claim], None],
    ) -> None:
        key = (name or '').strip()
        if not key:
            raise RegistryError('Validator name is required.')
        if key in self._validators:
            raise RegistryError(f'Duplicate validator: {key!r}.')
        self._validators[key] = validator

    def get_claim_type(self, name: str) -> ClaimType:
        try:
            return self._claim_types[name]
        except KeyError as exc:
            raise ValidationError(
                f'Unsupported claim type: {name!r}.'
            ) from exc

    def list_claim_types(self) -> list[str]:
        return sorted(self._claim_types.keys())

    def list_rules(self) -> list[str]:
        return sorted(self._rules.keys())

    def list_providers(self) -> list[str]:
        return sorted(self._providers.keys())

    def run_validators(self, claim: Claim) -> None:
        for validator in self._validators.values():
            validator(claim)

    def collect_evidence(self, claim: Claim) -> list[Evidence]:
        collected: list[Evidence] = []
        for provider in self._providers.values():
            collected.extend(provider(claim) or [])
        return collected

    def apply_rules(self, claim: Claim) -> Claim:
        current = claim
        for rule in self._rules.values():
            current = rule(current)
        return current

    def validate_configuration(self) -> None:
        if not self._claim_types:
            raise RegistryError('Broken configuration: no claim types.')


def build_default_registry() -> FactCheckRegistry:
    """Default registry with built-in claim types and stub no-op provider."""
    registry = FactCheckRegistry()

    def _noop_provider(claim: Claim) -> list[Evidence]:
        # External retrieval is intentionally not implemented.
        return []

    def _require_editor_if_empty_evidence(claim: Claim) -> Claim:
        if claim.evidence:
            return claim
        from content_ai.fact_check.claims import VerificationStatus
        from dataclasses import replace

        return replace(
            claim,
            verification_status=VerificationStatus.REQUIRES_EDITOR_REVIEW,
            warnings=tuple(
                list(claim.warnings)
                + ['No evidence attached; editor review required.']
            ),
        )

    registry.register_provider('noop', _noop_provider)
    registry.register_rule(
        'require_editor_without_evidence',
        _require_editor_if_empty_evidence,
    )
    registry.validate_configuration()
    return registry
