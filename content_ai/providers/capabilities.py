"""Provider capability descriptors (RFC-005)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """
    Declares what a provider adapter can do.

    Future providers expose capabilities dynamically via this model.
    """

    text_generation: bool = True
    json_output: bool = False
    streaming: bool = False
    reasoning: bool = False
    vision: bool = False
    function_calling: bool = False
    embeddings: bool = False
    audio: bool = False
    image_generation: bool = False
    long_context: bool = False
    structured_output: bool = False

    def supports(self, capability: str) -> bool:
        if not hasattr(self, capability):
            return False
        return bool(getattr(self, capability))
