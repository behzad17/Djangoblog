"""Base interface for Content AI prompt templates."""

from __future__ import annotations

from content_ai.prompts.loader import DEFAULT_PROMPT_VERSION, PromptLoader
from content_ai.prompts.renderer import TemplateRenderer


class BasePromptTemplate:
    """
    Builds a plain-text prompt from a canonical request schema.

    Providers must never construct Peyvand-domain prompts themselves.
    """

    def build(self, request=None) -> str:
        raise NotImplementedError(
            f'{type(self).__name__} does not implement build()'
        )


class AssetPromptTemplate(BasePromptTemplate):
    """
    Prompt template backed by a versioned markdown asset.

    Subclasses set ``kind`` and ``request_class``. Optional ``version``
    selects ``v1``, ``v2``, … for future A/B experiments (Git files only).
    """

    kind: str = ''
    request_class = None
    default_version: str = DEFAULT_PROMPT_VERSION

    def __init__(
        self,
        version: str | None = None,
        loader: PromptLoader | None = None,
        renderer: TemplateRenderer | None = None,
    ):
        self.version = version or self.default_version
        self.loader = loader or PromptLoader()
        self.renderer = renderer or TemplateRenderer()

    def build(self, request=None) -> str:
        req = request if request is not None else self.request_class()
        template = self.loader.load(self.kind, self.version)
        return self.renderer.render(template, self._values(req))

    def _values(self, request) -> dict:
        raise NotImplementedError(
            f'{type(self).__name__} does not implement _values()'
        )
