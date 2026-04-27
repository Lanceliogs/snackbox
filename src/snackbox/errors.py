"""Custom exceptions for snackbox."""


class SnackboxError(Exception):
    """Base exception for all snackbox errors."""

    pass


class ConfigError(SnackboxError):
    """Raised when there's an issue with snackbox.yaml configuration."""

    pass


class BuildError(SnackboxError):
    """Raised when a build step fails."""

    pass


class CacheError(SnackboxError):
    """Raised when cache operations fail (download, extract, etc.)."""

    pass
