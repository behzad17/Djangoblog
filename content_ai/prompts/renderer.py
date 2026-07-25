"""Render markdown prompt templates with request field placeholders."""

from __future__ import annotations

import re
from typing import Any, Mapping

# {{ field_name }} — whitespace inside braces is optional.
_PLACEHOLDER_RE = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}')


class TemplateRenderer:
    """
    Replace ``{{ placeholders }}`` with values from a mapping.

    Missing keys become empty strings. No logic beyond substitution.
    """

    def render(self, template: str, values: Mapping[str, Any] | None = None) -> str:
        data = values or {}

        def _replace(match: re.Match) -> str:
            key = match.group(1)
            value = data.get(key, '')
            if value is None:
                return ''
            return str(value)

        return _PLACEHOLDER_RE.sub(_replace, template)
