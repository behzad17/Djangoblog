"""Domain exceptions for Community business rules."""


class CommunityDomainError(Exception):
    """Base class for Community domain errors."""


class DiscussionClosedError(CommunityDomainError):
    """Raised when an action requires an open discussion."""


class DiscussionDeletedError(CommunityDomainError):
    """Raised when an action targets a soft-deleted discussion."""


class InactiveCategoryError(CommunityDomainError):
    """Raised when a discussion is assigned an inactive category."""


class InvalidDiscussionStateError(CommunityDomainError):
    """Raised when a discussion status transition or state is invalid."""


class ReplyModerationError(CommunityDomainError):
    """Raised when a reply moderation action is invalid."""


class UnauthorizedAuthorError(CommunityDomainError):
    """Raised when the acting user is not the content author."""


class ValidationError(CommunityDomainError):
    """Raised when required service input fails validation."""
