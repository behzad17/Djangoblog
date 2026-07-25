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


# RFC-005 platform exceptions (reuse ProviderError hierarchy).


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is registered but unavailable."""


class AuthenticationError(ProviderError):
    """Raised when provider credentials are missing or rejected."""


class RateLimitError(ProviderError):
    """Raised when a provider rate limit is hit."""


class TimeoutError(ProviderError):
    """Raised when a provider request times out."""


class InvalidResponseError(ProviderError):
    """Raised when a provider returns an unusable response."""


class CapabilityError(ProviderError):
    """Raised when a requested capability is unsupported."""


class ConfigurationError(ProviderConfigurationError):
    """Alias for configuration problems (RFC-005 naming)."""
