"""Exceptions for prompt asset loading and rendering."""


class PromptTemplateError(Exception):
    """Base error for prompt asset failures."""


class PromptTemplateNotFound(PromptTemplateError):
    """Raised when a markdown prompt asset cannot be located."""
