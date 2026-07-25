"""Load versioned markdown prompt assets from disk (Git-managed)."""

from __future__ import annotations

from pathlib import Path

from content_ai.prompts.exceptions import PromptTemplateNotFound

DEFAULT_PROMPT_VERSION = 'v1'
PROMPTS_ROOT = Path(__file__).resolve().parent


class PromptLoader:
    """
    Resolve ``{kind}/{version}.md`` assets under the prompts package.

    No database. No Admin editing. Versions are files in Git.
    """

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir) if base_dir is not None else PROMPTS_ROOT

    def path_for(self, kind: str, version: str = DEFAULT_PROMPT_VERSION) -> Path:
        safe_kind = self._safe_segment(kind, 'kind')
        safe_version = self._safe_segment(version, 'version')
        return self.base_dir / safe_kind / f'{safe_version}.md'

    def load(self, kind: str, version: str = DEFAULT_PROMPT_VERSION) -> str:
        path = self.path_for(kind, version)
        if not path.is_file():
            raise PromptTemplateNotFound(
                f"Prompt template not found: kind={kind!r} version={version!r} "
                f"(expected {path})."
            )
        return path.read_text(encoding='utf-8')

    def exists(self, kind: str, version: str = DEFAULT_PROMPT_VERSION) -> bool:
        return self.path_for(kind, version).is_file()

    @staticmethod
    def _safe_segment(value: str, label: str) -> str:
        if not value or not isinstance(value, str):
            raise PromptTemplateNotFound(f'Invalid prompt {label}: {value!r}.')
        if '/' in value or '\\' in value or value.startswith('.'):
            raise PromptTemplateNotFound(f'Invalid prompt {label}: {value!r}.')
        return value
