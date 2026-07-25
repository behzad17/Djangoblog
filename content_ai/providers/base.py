"""Abstract AI provider interface.

Concrete vendors must subclass ``BaseAIProvider``. Application code depends
only on this interface, never on a specific vendor SDK.
"""


class BaseAIProvider:
    """
    Contract for Content AI providers.

    Methods raise ``NotImplementedError`` until a concrete provider overrides
    them. No network I/O belongs in this base class.
    """

    name = 'base'

    def generate_post(self, *args, **kwargs):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement generate_post()'
        )

    def generate_ad(self, *args, **kwargs):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement generate_ad()'
        )

    def rewrite(self, *args, **kwargs):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement rewrite()'
        )

    def summarize(self, *args, **kwargs):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement summarize()'
        )

    def translate(self, *args, **kwargs):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement translate()'
        )
