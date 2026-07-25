"""Base interface for Content AI prompt templates."""


class BasePromptTemplate:
    """
    Builds a plain-text prompt from a canonical request schema.

    Providers must never construct Peyvand-domain prompts themselves.
    """

    def build(self, request=None) -> str:
        raise NotImplementedError(
            f'{type(self).__name__} does not implement build()'
        )
