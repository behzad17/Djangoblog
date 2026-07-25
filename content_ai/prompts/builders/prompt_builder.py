"""Assemble versioned AI Engine prompts from modular markdown assets.

Architecture-only. Not wired into production generation or OpenAI.
"""

from __future__ import annotations

from pathlib import Path

from content_ai.config.ai_engine import (
    DEFAULT_PROMPT_VERSION,
    DEFAULT_STYLE,
)
from content_ai.prompts.validators.prompt_validator import (
    SECTION_AUDIENCE,
    SECTION_IDENTITY,
    SECTION_OUTPUT_SCHEMA,
    SECTION_STYLE,
    SECTION_USER_PROMPT,
    SECTION_WRITING,
    PromptValidator,
)


def _section(header: str, body: str) -> str:
    return f'{header}\n\n{body.strip()}\n'


class PromptBuilder:
    """
    Load, validate, and assemble AI Engine prompt modules.

    Default version is ``v1``. Knowledge is not injected automatically.
    """

    def __init__(
        self,
        prompts_root: Path | None = None,
        validator: PromptValidator | None = None,
    ):
        self.prompts_root = prompts_root or Path(__file__).resolve().parents[1]
        self.validator = validator or PromptValidator(
            prompts_root=self.prompts_root,
        )

    def build(
        self,
        *,
        version: str = DEFAULT_PROMPT_VERSION,
        style: str = DEFAULT_STYLE,
        user_prompt: str = '',
    ) -> str:
        """
        Assemble one complete prompt string.

        Order:
        Identity → Audience → Writing Rules → Style → Output Schema → User Prompt
        """
        self.validator.validate_required_files(version, style)

        identity = self.validator.validate_module_non_empty(
            self.validator.system_path(version, 'identity'),
            'identity',
        )
        audience = self.validator.validate_module_non_empty(
            self.validator.system_path(version, 'audience'),
            'audience',
        )
        writing = self.validator.validate_module_non_empty(
            self.validator.system_path(version, 'writing'),
            'writing',
        )
        style_body = self.validator.validate_module_non_empty(
            self.validator.style_path(version, style),
            f'style:{style}',
        )
        output_schema = self.validator.validate_module_non_empty(
            self.validator.system_path(version, 'output_schema'),
            'output_schema',
        )

        user_body = (user_prompt or '').strip()
        if not user_body:
            user_body = '(empty user prompt)'

        parts = [
            _section(SECTION_IDENTITY, identity),
            _section(SECTION_AUDIENCE, audience),
            _section(SECTION_WRITING, writing),
            _section(SECTION_STYLE, style_body),
            _section(SECTION_OUTPUT_SCHEMA, output_schema),
            _section(SECTION_USER_PROMPT, user_body),
        ]
        prompt = '\n'.join(parts).strip() + '\n'
        self.validator.validate_assembled_prompt(prompt)
        return prompt
