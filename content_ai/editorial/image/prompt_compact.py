"""Compact featured-image prompts for the OpenAI Images API.

Keeps the visual plan and essential article cues; drops repetitive brand
boilerplate and long Persian excerpts so sync Heroku requests stay under H12.
"""

from __future__ import annotations

from typing import Any

# Target band from APF image-performance PR: 2000–2500 chars.
DEFAULT_MAX_IMAGE_PROMPT_CHARS = 2500
DEFAULT_TARGET_IMAGE_PROMPT_CHARS = 2200


def _clip(text: str, limit: int) -> str:
    cleaned = ' '.join((text or '').split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + '…'


def compact_image_prompt_for_api(
    prompt: str,
    *,
    max_chars: int = DEFAULT_MAX_IMAGE_PROMPT_CHARS,
    target_chars: int = DEFAULT_TARGET_IMAGE_PROMPT_CHARS,
) -> tuple[str, dict[str, Any]]:
    """
    Return (prompt_for_api, stats).

    Preserves:
    - Internal visual plan
    - Headline / lead / style cues
    - Final instruction

    Removes / shrinks:
    - Long Peyvand style boilerplate
    - Long article body excerpts
    - Repeated medium/style paragraphs
    """
    original = (prompt or '').strip()
    original_chars = len(original)
    limit = max(500, int(max_chars or DEFAULT_MAX_IMAGE_PROMPT_CHARS))
    target = min(limit, max(500, int(target_chars or DEFAULT_TARGET_IMAGE_PROMPT_CHARS)))

    if original_chars <= limit:
        return original, {
            'truncated': False,
            'original_chars': original_chars,
            'final_chars': original_chars,
            'max_chars': limit,
        }

    plan_start = original.find('Internal visual plan')
    context_start = original.find('Article context')
    final_start = original.find('Final instruction')

    header = (
        'Create a professional featured image for a Persian news / community '
        'website article. One clear visual idea. Clean 16:9 editorial layout. '
        'No text, logos, watermarks, captions, screens, or UI. '
        'Minimal, modern, Scandinavian, natural daylight, magazine quality.'
    )

    parts: list[str] = [header]

    if plan_start >= 0:
        end = len(original)
        for marker in (context_start, final_start):
            if marker > plan_start:
                end = min(end, marker)
        plan_block = original[plan_start:end].strip()
        if plan_block:
            parts.append(plan_block)

    if context_start >= 0:
        end = final_start if final_start > context_start else len(original)
        ctx = original[context_start:end]
        keep_prefixes = (
            'Article headline',
            'Lead (',
            'Selected image style',
            'Medium:',
            'Content type:',
            'Category:',
        )
        kept: list[str] = []
        for line in ctx.splitlines():
            stripped = line.strip()
            if any(stripped.startswith(prefix) for prefix in keep_prefixes):
                kept.append(_clip(stripped, 260))
        if kept:
            parts.append('Article context (meaning only; never render as text):\n' + '\n'.join(kept))

    if final_start >= 0:
        final_line = original[final_start:].strip().splitlines()[0]
        parts.append(_clip(final_line, 180))
    else:
        parts.append(
            'Final instruction: produce one clean 16:9 editorial image '
            'readable as a thumbnail in two seconds.'
        )

    compact = '\n\n'.join(part for part in parts if part).strip()
    if len(compact) > target:
        compact = compact[: target - 1].rstrip() + '…'
    if len(compact) > limit:
        compact = compact[: limit - 1].rstrip() + '…'

    return compact, {
        'truncated': True,
        'original_chars': original_chars,
        'final_chars': len(compact),
        'max_chars': limit,
        'target_chars': target,
        'kept_plan': plan_start >= 0,
        'kept_context': context_start >= 0,
    }
