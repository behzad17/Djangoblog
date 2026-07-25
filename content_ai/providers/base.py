"""Abstract AI provider interface.

Concrete vendors must subclass ``BaseAIProvider``. Application code depends
only on this interface, never on a specific vendor SDK.
"""


class BaseAIProvider:
    """
    Contract for Content AI providers.

    Methods accept a plain prompt string (built by the prompt layer) and must
    return ``GenerationResult``. Base methods raise ``NotImplementedError``.
    No network I/O belongs in this base class.
    """

    name = 'base'

    def generate_post(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement generate_post()'
        )

    def generate_ad(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement generate_ad()'
        )

    def rewrite(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement rewrite()'
        )

    def summarize(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement summarize()'
        )

    def translate(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement translate()'
        )
