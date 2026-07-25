"""Canonical Content AI request schemas.

Providers accept these objects instead of vendor-specific payloads.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PostGenerationRequest:
    """Request for blog-post oriented generation."""

    title: str = ''
    source: str = ''
    language: str = ''
    category: str = ''
    context: str = ''
    instructions: str = ''


@dataclass(frozen=True, slots=True)
class AdGenerationRequest:
    """Request for advertisement oriented generation."""

    business_name: str = ''
    category: str = ''
    language: str = ''
    city: str = ''
    description: str = ''
    target_audience: str = ''
    instructions: str = ''
