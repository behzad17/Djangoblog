"""Provider-layer exceptions for Content AI."""


class ProviderError(Exception):
    """Base class for Content AI provider errors."""


class ProviderNotFound(ProviderError):
    """Raised when a requested provider name is not registered."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider settings are missing or invalid."""


class GenerationError(ProviderError):
    """Raised when a provider fails to produce a generation result."""

    def __init__(self, message, telemetry=None):
        super().__init__(message)
        self.telemetry = telemetry
