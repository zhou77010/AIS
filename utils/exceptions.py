"""AIS base exception hierarchy.

Every error raised by AIS derives from :class:`AISException`, so callers can
handle project errors without catching unrelated exceptions.
"""

from __future__ import annotations


class AISException(Exception):
    """Base class for every AIS error."""


class ConfigurationError(AISException):
    """Raised when configuration is missing or invalid."""


class DataError(AISException):
    """Raised when data collection or data access fails."""


class ValidationError(AISException):
    """Raised when data or evidence fails validation."""


class EngineError(AISException):
    """Raised when the AIS Core Engine cannot complete its work."""
