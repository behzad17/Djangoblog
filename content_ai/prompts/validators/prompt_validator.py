"""Validate AI Engine prompt modules, versions, styles, and assembly order.

Used by PromptBuilder for production and Studio prompt assembly.
"""

from __future__ import annotations

from pathlib import Path

from content_ai.config.ai_engine import (
    SUPPORTED_PROMPT_VERSIONS,
    SUPPORTED_STYLES,
    SYSTEM_MODULE_ORDER,
)
from content_ai.prompts.builders.exceptions import (
    InvalidPromptStructureError,
    MissingPromptModuleError,
    UnknownPromptVersionError,
    UnknownStyleError,
)

# Assembly order markers (section headers in the final prompt string).
SECTION_IDENTITY = '## Identity'
SECTION_AUDIENCE = '## Audience'
SECTION_WRITING = '## Writing Rules'
SECTION_STYLE = '## Style'
SECTION_OUTPUT_SCHEMA = '## Output Schema'
SECTION_USER_PROMPT = '## User Prompt'

REQUIRED_SECTION_ORDER: tuple[str, ...] = (
    SECTION_IDENTITY,
    SECTION_AUDIENCE,
    SECTION_WRITING,
    SECTION_STYLE,
    SECTION_OUTPUT_SCHEMA,
    SECTION_USER_PROMPT,
)

SYSTEM_FILES: dict[str, str] = {
    'identity': 'identity.md',
    'audience': 'audience.md',
    'writing': 'writing.md',
    'output_schema': 'output_schema.md',
}


class PromptValidator:
    """
    Verify AI Engine prompt assets and assembled prompt structure.

    Does not call providers or touch production prompt templates.
    """

    def __init__(self, prompts_root: Path | None = None):
        # Default: content_ai/prompts/
        self.prompts_root = prompts_root or Path(__file__).resolve().parents[1]

    def validate_version(self, version: str) -> None:
        if version not in SUPPORTED_PROMPT_VERSIONS:
            raise UnknownPromptVersionError(
                f"Unknown prompt version {version!r}. "
                f"Supported: {', '.join(SUPPORTED_PROMPT_VERSIONS)}."
            )
        version_dir = self.prompts_root / version
        if not version_dir.is_dir():
            raise UnknownPromptVersionError(
                f"Prompt version directory missing: {version_dir}."
            )

    def validate_style(self, style: str, version: str | None = None) -> None:
        if style not in SUPPORTED_STYLES:
            raise UnknownStyleError(
                f"Unknown style {style!r}. "
                f"Supported: {', '.join(SUPPORTED_STYLES)}."
            )
        if version is not None:
            path = self.style_path(version, style)
            if not path.is_file():
                raise UnknownStyleError(
                    f"Style file missing for style={style!r} "
                    f"version={version!r} (expected {path})."
                )

    def system_path(self, version: str, module: str) -> Path:
        filename = SYSTEM_FILES.get(module)
        if filename is None:
            raise MissingPromptModuleError(
                f"Unknown system module {module!r}."
            )
        return self.prompts_root / version / 'system' / filename

    def style_path(self, version: str, style: str) -> Path:
        return self.prompts_root / version / 'styles' / f'{style}.md'

    def validate_required_files(self, version: str, style: str) -> None:
        """Ensure all required system modules and the style file exist."""
        self.validate_version(version)
        self.validate_style(style, version=version)
        missing: list[str] = []
        for module in SYSTEM_MODULE_ORDER:
            path = self.system_path(version, module)
            if not path.is_file():
                missing.append(str(path))
        style_file = self.style_path(version, style)
        if not style_file.is_file():
            missing.append(str(style_file))
        if missing:
            raise MissingPromptModuleError(
                'Missing required prompt module file(s): '
                + '; '.join(missing)
            )

    def validate_module_non_empty(self, path: Path, label: str) -> str:
        if not path.is_file():
            raise MissingPromptModuleError(
                f"Missing prompt module {label!r}: {path}."
            )
        text = path.read_text(encoding='utf-8')
        if not text.strip():
            raise InvalidPromptStructureError(
                f"Prompt module {label!r} is empty: {path}."
            )
        return text

    def validate_assembled_prompt(self, prompt: str) -> None:
        """
        Verify required section headers appear in the documented order.

        Knowledge must not appear as an automatic section yet.
        """
        if not (prompt or '').strip():
            raise InvalidPromptStructureError('Assembled prompt is empty.')

        positions: list[tuple[str, int]] = []
        for header in REQUIRED_SECTION_ORDER:
            idx = prompt.find(header)
            if idx < 0:
                raise InvalidPromptStructureError(
                    f"Assembled prompt missing required section {header!r}."
                )
            positions.append((header, idx))

        for i in range(1, len(positions)):
            prev_header, prev_idx = positions[i - 1]
            header, idx = positions[i]
            if idx <= prev_idx:
                raise InvalidPromptStructureError(
                    f"Invalid prompt section order: {header!r} must follow "
                    f"{prev_header!r}."
                )

        # Guardrail: knowledge is a separate layer and must not be auto-injected.
        if '## Knowledge' in prompt:
            raise InvalidPromptStructureError(
                'Assembled prompt must not include automatic Knowledge '
                'injection in this architecture phase.'
            )

    def validate(self, version: str, style: str, prompt: str) -> None:
        """Run full validation for a version, style, and assembled prompt."""
        self.validate_required_files(version, style)
        self.validate_assembled_prompt(prompt)
