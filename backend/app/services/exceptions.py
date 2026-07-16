class ServiceError(Exception):
    """Base error for service-layer failures."""


class NotFoundError(ServiceError):
    """Raised when a requested canonical record does not exist."""


class ValidationError(ServiceError):
    """Raised when a request violates canonical data model rules."""
